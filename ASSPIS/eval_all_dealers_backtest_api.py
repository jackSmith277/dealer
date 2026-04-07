# eval_all_dealers_backtest_api.py
# ------------------------------------------------------------
# 功能：通过调用 /forecast/quantiles + /sales/original 做批量回测评估
# 设计修正点（对应“细节修改”）：
#   1) BASE_MONTHS 自动生成：保证 base_month + max_horizon <= MONTHS_TOTAL
#   2) 支持 horizon 设定为：整数(1..H) 或显式列表（逗号分隔）
#   3) eval_by_horizon.json 增加：
#        - abs_err_share（=err_share）
#        - WMAPE_ratio_to_h1（用于判断 h=2 是否主导）
#        - coverage_q10_q90 / avg_width_q10_q90（按 horizon）
#   4) eval_summary.json 增加：dominant_horizon / dominant_abs_err_share
# ------------------------------------------------------------

import json
import math
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


# =============================
# 输出控制（避免覆盖）
# =============================
OUT_DIR = os.getenv("OUT_DIR", ".")
OUT_PREFIX = os.getenv("OUT_PREFIX", "")


def _p(name: str) -> str:
    return f"{OUT_PREFIX}{name}" if OUT_PREFIX else name


def _out(name: str) -> str:
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    return str(Path(OUT_DIR) / _p(name))


OUT_SUMMARY_JSON = _out("eval_summary.json")
OUT_BY_HORIZON_JSON = _out("eval_by_horizon.json")
OUT_WORST_DEALERS_JSON = _out("eval_worst_dealers.json")
OUT_WORST_BY_H_JSON = _out("eval_worst_dealers_by_horizon.json")
OUT_FAILS_JSON = _out("eval_failed_cases.json")
OUT_CONFIG_JSON = _out("eval_config.json")


# =============================
# 配置区：按需改这里
# =============================
FORECAST_URL = os.getenv("FORECAST_URL", "http://127.0.0.1:5000/forecast/quantiles")
ORIGINAL_URL = os.getenv("ORIGINAL_URL", "http://127.0.0.1:5000/sales/original")

# 从审计脚本生成的 complete_dealers.json 读经销商名单
COMPLETE_DEALERS_JSON = os.getenv("COMPLETE_DEALERS_JSON", "complete_dealers.json")

# 你当前总月份（只有 10 个月时保持默认 10）
MONTHS_TOTAL = int(os.getenv("MONTHS_TOTAL", "10"))

# horizons 设定：
#   - HORIZONS="3"          => 请求 1..3
#   - HORIZONS="1,2,3,4"    => 请求显式列表（后端需要支持 list）
HORIZONS_LIST_ENV = os.getenv("HORIZONS_LIST", "").strip()
if HORIZONS_LIST_ENV:
    HORIZON_LIST = [int(x) for x in HORIZONS_LIST_ENV.split(",") if x.strip()]
    HORIZON_MODE = "list"
else:
    HORIZONS_ENV = os.getenv("HORIZONS", "3").strip()
    if "," in HORIZONS_ENV:
        HORIZON_LIST = [int(x) for x in HORIZONS_ENV.split(",") if x.strip()]
        HORIZON_MODE = "list"
    else:
        HORIZON_LIST = list(range(1, int(HORIZONS_ENV) + 1))
        HORIZON_MODE = "range"

MAX_H = max(HORIZON_LIST) if HORIZON_LIST else 1

# 自动生成合法 base_month：保证 base_month + MAX_H <= MONTHS_TOTAL
BASE_MONTHS_ENV = os.getenv("BASE_MONTHS", "").strip()
if BASE_MONTHS_ENV:
    BASE_MONTHS = [int(x) for x in BASE_MONTHS_ENV.split(",") if x.strip()]
else:
    BASE_MONTHS = list(range(1, max(2, MONTHS_TOTAL - MAX_H + 1)))

# 如你想严格只做一次 “1-7 -> 8-10” 的 backtest：取消注释
# BASE_MONTHS = [MONTHS_TOTAL - MAX_H]

QUANTILES = [0.1, 0.5, 0.9]
CALIB_ALPHA = 0.2  # 注意：后端未必使用该字段（保留兼容）

# 情景可不测（整体评估一般先测 baseline）
SCENARIOS = [{"name": "baseline"}]

# worst dealers 输出数量
TOP_K_WORST = int(os.getenv("TOP_K_WORST", "20"))

# requests 超时
POST_TIMEOUT = int(os.getenv("POST_TIMEOUT", "120"))
GET_TIMEOUT = int(os.getenv("GET_TIMEOUT", "60"))


# =============================
# 指标函数
# =============================

def _safe_div(a: float, b: float, eps: float = 1e-9) -> float:
    return a / (b if abs(b) > eps else eps)


def mae(y: List[float], p: List[float]) -> float:
    return sum(abs(yy - pp) for yy, pp in zip(y, p)) / len(y)


def rmse(y: List[float], p: List[float]) -> float:
    return math.sqrt(sum((yy - pp) ** 2 for yy, pp in zip(y, p)) / len(y))


def wmape(y: List[float], p: List[float], eps: float = 1e-9) -> float:
    num = sum(abs(yy - pp) for yy, pp in zip(y, p))
    den = sum(abs(yy) for yy in y)
    return _safe_div(num, den, eps)


def smape_point(y: float, p: float, eps: float = 1e-9) -> float:
    denom = abs(y) + abs(p)
    return 2.0 * abs(y - p) / (denom if denom > eps else eps)


def pinball_loss(y: List[float], q_pred: List[float], q: float) -> float:
    loss = 0.0
    for yy, yhat in zip(y, q_pred):
        if yy >= yhat:
            loss += (yy - yhat) * q
        else:
            loss += (yhat - yy) * (1.0 - q)
    return loss / len(y)


def coverage(y: List[float], lo: List[float], hi: List[float]) -> float:
    ok = 0
    for yy, l, h in zip(y, lo, hi):
        if l <= yy <= h:
            ok += 1
    return ok / len(y)


def avg_width(lo: List[float], hi: List[float]) -> float:
    return sum(max(h - l, 0.0) for l, h in zip(lo, hi)) / len(lo)


def mase_scale(history: List[float] | None) -> float | None:
    if history is None or len(history) < 2:
        return None
    diffs = [abs(history[i] - history[i - 1]) for i in range(1, len(history))]
    s = sum(diffs) / len(diffs)
    return s if s > 1e-9 else None


# =============================
# 拉真实值：/sales/original
# =============================

def fetch_actuals_full(dealer_code: str, months_upto: int, session: requests.Session) -> Dict[int, float]:
    r = session.get(
        ORIGINAL_URL,
        params={"dealer_code": dealer_code, "months": int(months_upto)},
        timeout=GET_TIMEOUT,
    )
    if r.status_code != 200:
        raise RuntimeError(f"/sales/original failed status={r.status_code}, text={r.text[:500]}")

    data = r.json()

    if isinstance(data, dict) and "sales" in data and isinstance(data["sales"], dict):
        return {int(k): float(v) for k, v in data["sales"].items()}

    if (
        isinstance(data, dict)
        and "months" in data
        and "sales" in data
        and isinstance(data["months"], list)
        and isinstance(data["sales"], list)
    ):
        return {int(m): float(s) for m, s in zip(data["months"], data["sales"]) }

    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        out: Dict[int, float] = {}
        for row in data["data"]:
            if isinstance(row, dict) and "month" in row and "sales" in row:
                out[int(row["month"])] = float(row["sales"])
        return out

    raise RuntimeError(
        "Unrecognized /sales/original response format: "
        + json.dumps(data, ensure_ascii=False)[:2000]
    )


def load_complete_dealers(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, dict) and "complete_dealers" in obj and isinstance(obj["complete_dealers"], list):
        return [str(x) for x in obj["complete_dealers"]]
    raise ValueError("complete_dealers.json format error: expect {'complete_dealers':[...]}.")


# =============================
# 主流程
# =============================

def _save_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _stage_counts(failed: List[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in failed:
        st = str(row.get("stage", "unknown"))
        out[st] = out.get(st, 0) + 1
    return out


def main() -> None:
    dealer_codes = load_complete_dealers(COMPLETE_DEALERS_JSON)
    print(f"[eval] loaded complete dealers: {len(dealer_codes)}")
    print(f"[eval] horizon_mode={HORIZON_MODE}, horizons={HORIZON_LIST}")
    print(f"[eval] base_months={BASE_MONTHS} (MONTHS_TOTAL={MONTHS_TOTAL}, MAX_H={MAX_H})")

    session = requests.Session()

    # 全局收集
    y_all: List[float] = []
    p_all: List[float] = []
    abs_err_all: List[float] = []
    smape_all: List[float] = []

    # 分 horizon 收集
    by_h: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: {"y": [], "p": [], "abs_err": [], "smape": []})

    # 概率预测收集（baseline；如果缺失会导致 pinball/coverage 输出 None）
    q_preds: Dict[float, List[float]] = {q: [] for q in QUANTILES}

    # overall interval
    q10_list: List[float] = []
    q90_list: List[float] = []

    # by-horizon interval
    q10_by_h: Dict[int, List[float]] = defaultdict(list)
    q90_by_h: Dict[int, List[float]] = defaultdict(list)

    # MASE
    mase_vals: List[float] = []
    mase_vals_by_h: Dict[int, List[float]] = defaultdict(list)

    # 失败记录
    failed: List[Dict[str, Any]] = []

    # worst dealers：overall & by horizon
    dealer_points: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    dealer_points_by_h: Dict[int, Dict[str, List[Tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))

    t0 = time.time()

    _save_json(
        OUT_CONFIG_JSON,
        {
            "FORECAST_URL": FORECAST_URL,
            "ORIGINAL_URL": ORIGINAL_URL,
            "COMPLETE_DEALERS_JSON": COMPLETE_DEALERS_JSON,
            "MONTHS_TOTAL": MONTHS_TOTAL,
            "BASE_MONTHS": BASE_MONTHS,
            "HORIZON_MODE": HORIZON_MODE,
            "HORIZON_LIST": HORIZON_LIST,
            "MAX_H": MAX_H,
            "QUANTILES": QUANTILES,
            "SCENARIOS": SCENARIOS,
            "OUT_DIR": OUT_DIR,
            "OUT_PREFIX": OUT_PREFIX,
            "TOP_K_WORST": TOP_K_WORST,
        },
    )

    for idx, dealer_code in enumerate(dealer_codes, 1):
        for base_month in BASE_MONTHS:
            # 兼容后端：range 模式仍传 int；list 模式传 list（后端需支持）
            horizons_payload: Any = (max(HORIZON_LIST) if HORIZON_MODE == "range" else list(HORIZON_LIST))

            payload = {
                "dealer_code": dealer_code,
                "base_month": int(base_month),
                "horizons": horizons_payload,
                "quantiles": QUANTILES,
                "scenarios": SCENARIOS,
                "calibration_alpha": float(CALIB_ALPHA),
            }

            try:
                r = session.post(FORECAST_URL, json=payload, timeout=POST_TIMEOUT)
                if r.status_code != 200:
                    failed.append(
                        {
                            "dealer": dealer_code,
                            "base_month": base_month,
                            "stage": "forecast",
                            "status": r.status_code,
                            "text": r.text[:500],
                            "payload_horizons": horizons_payload,
                        }
                    )
                    continue

                pred = r.json()
                if not isinstance(pred, dict) or "scenarios" not in pred:
                    failed.append(
                        {
                            "dealer": dealer_code,
                            "base_month": base_month,
                            "stage": "bad_forecast_payload",
                            "text": json.dumps(pred, ensure_ascii=False)[:500],
                        }
                    )
                    continue

                sc = (pred.get("scenarios") or {}).get("baseline")
                if not isinstance(sc, dict):
                    failed.append({"dealer": dealer_code, "base_month": base_month, "stage": "no_baseline"})
                    continue

                months_pred = sc.get("months")
                point = sc.get("point")
                qmap = sc.get("quantiles", {}) or {}

                if not months_pred or not isinstance(months_pred, list) or not point or not isinstance(point, list):
                    failed.append({"dealer": dealer_code, "base_month": base_month, "stage": "empty_prediction"})
                    continue

                max_month = max(int(m) for m in months_pred)
                sales_map = fetch_actuals_full(dealer_code, max_month, session=session)

                # MASE scale：<= base_month 的历史
                hist = [sales_map[m] for m in sorted(sales_map.keys()) if m <= base_month and m in sales_map]
                scale = mase_scale(hist)

                for i, tm in enumerate(months_pred):
                    tm_int = int(tm)
                    yt = sales_map.get(tm_int)
                    if yt is None:
                        failed.append(
                            {
                                "dealer": dealer_code,
                                "base_month": base_month,
                                "stage": "actual_missing",
                                "target_month": tm_int,
                            }
                        )
                        continue

                    yp = float(point[i])
                    yt_f = float(yt)

                    y_all.append(yt_f)
                    p_all.append(yp)

                    ae = abs(yt_f - yp)
                    abs_err_all.append(ae)

                    sp = smape_point(yt_f, yp)
                    smape_all.append(sp)

                    dealer_points[dealer_code].append((yt_f, yp))

                    h = tm_int - int(base_month)
                    by_h[h]["y"].append(yt_f)
                    by_h[h]["p"].append(yp)
                    by_h[h]["abs_err"].append(ae)
                    by_h[h]["smape"].append(sp)

                    dealer_points_by_h[h][dealer_code].append((yt_f, yp))

                    # quantiles（仅在当前点存在时追加；否则 pinball 会输出 None）
                    for q in QUANTILES:
                        qstr = str(float(q))
                        if qstr in qmap and i < len(qmap[qstr]):
                            q_preds[q].append(float(qmap[qstr][i]))

                    # q10-q90 interval（overall + by_h）
                    if "0.1" in qmap and "0.9" in qmap and i < len(qmap["0.1"]) and i < len(qmap["0.9"]):
                        q10 = float(qmap["0.1"][i])
                        q90 = float(qmap["0.9"][i])
                        q10_list.append(q10)
                        q90_list.append(q90)
                        q10_by_h[h].append(q10)
                        q90_by_h[h].append(q90)

                    # MASE
                    if scale is not None:
                        v = ae / scale
                        mase_vals.append(v)
                        mase_vals_by_h[h].append(v)

            except Exception as e:
                failed.append({"dealer": dealer_code, "base_month": base_month, "stage": "exception", "error": repr(e)})
                continue

        if idx % 20 == 0:
            print(f"[eval] progress {idx}/{len(dealer_codes)} dealers, points={len(y_all)}")

    if len(y_all) == 0:
        print("[eval] no valid points collected. Showing first 5 failed cases:")
        print(json.dumps(failed[:5], ensure_ascii=False, indent=2))
        raise RuntimeError("No valid evaluation points collected. Check base_months/horizons or API responses.")

    total_abs_err = sum(abs_err_all)
    total_abs_y = sum(abs(v) for v in y_all)

    summary: Dict[str, Any] = {
        "n_points": len(y_all),
        "MAE": mae(y_all, p_all),
        "RMSE": rmse(y_all, p_all),
        "WMAPE": wmape(y_all, p_all),
        "sMAPE": sum(smape_all) / len(smape_all),
        "MASE": (sum(mase_vals) / len(mase_vals)) if len(mase_vals) else None,
        "abs_err_sum": total_abs_err,
        "abs_y_sum": total_abs_y,
        "fail_count": len(failed),
        "fail_by_stage": _stage_counts(failed),
        "elapsed_sec": round(time.time() - t0, 3),
    }

    # probabilistic
    for q in QUANTILES:
        if len(q_preds[q]) == len(y_all):
            summary[f"pinball_q{q}"] = pinball_loss(y_all, q_preds[q], q)
        else:
            summary[f"pinball_q{q}"] = None

    if len(q10_list) == len(y_all) and len(q90_list) == len(y_all):
        summary["coverage_q10_q90"] = coverage(y_all, q10_list, q90_list)
        summary["avg_width_q10_q90"] = avg_width(q10_list, q90_list)
    else:
        summary["coverage_q10_q90"] = None
        summary["avg_width_q10_q90"] = None

    # by horizon + 主导贡献
    by_h_out: Dict[str, Any] = {}
    for h, d in sorted(by_h.items()):
        if len(d["y"]) == 0:
            continue
        abs_err_sum_h = sum(d["abs_err"])
        abs_y_sum_h = sum(abs(v) for v in d["y"])

        row = {
            "n_points": len(d["y"]),
            "MAE": mae(d["y"], d["p"]),
            "RMSE": rmse(d["y"], d["p"]),
            "WMAPE": wmape(d["y"], d["p"]),
            "sMAPE": sum(d["smape"]) / len(d["smape"]),
            "MASE": (sum(mase_vals_by_h[h]) / len(mase_vals_by_h[h])) if len(mase_vals_by_h[h]) else None,
            "abs_err_sum": abs_err_sum_h,
            "abs_y_sum": abs_y_sum_h,
            "err_share": _safe_div(abs_err_sum_h, total_abs_err),
            "abs_err_share": _safe_div(abs_err_sum_h, total_abs_err),
            "y_share": _safe_div(abs_y_sum_h, total_abs_y),
        }

        # horizon 维度下的区间覆盖/宽度
        if len(q10_by_h[h]) == len(d["y"]) and len(q90_by_h[h]) == len(d["y"]):
            row["coverage_q10_q90"] = coverage(d["y"], q10_by_h[h], q90_by_h[h])
            row["avg_width_q10_q90"] = avg_width(q10_by_h[h], q90_by_h[h])
        else:
            row["coverage_q10_q90"] = None
            row["avg_width_q10_q90"] = None

        by_h_out[str(h)] = row

    # WMAPE ratio to h=1（用于判断 h=2 是否“相对更差”）
    w1 = by_h_out.get("1", {}).get("WMAPE", None)
    if w1 is not None and isinstance(w1, (int, float)) and w1 > 0:
        for hk, row in by_h_out.items():
            row["WMAPE_ratio_to_h1"] = float(row["WMAPE"]) / float(w1)
    else:
        for hk, row in by_h_out.items():
            row["WMAPE_ratio_to_h1"] = None

    # summary：dominant horizon（按 abs_err_share 最大）
    if by_h_out:
        dom_h, dom_share = None, -1.0
        for hk, row in by_h_out.items():
            s = float(row.get("abs_err_share", 0.0) or 0.0)
            if s > dom_share:
                dom_share = s
                dom_h = hk
        summary["dominant_horizon"] = int(dom_h) if dom_h is not None else None
        summary["dominant_abs_err_share"] = float(dom_share) if dom_h is not None else None
        summary["WMAPE_by_horizon"] = {hk: float(row["WMAPE"]) for hk, row in by_h_out.items()}
        summary["WMAPE_ratio_to_h1_by_horizon"] = {hk: row.get("WMAPE_ratio_to_h1") for hk, row in by_h_out.items()}
    else:
        summary["dominant_horizon"] = None
        summary["dominant_abs_err_share"] = None
        summary["WMAPE_by_horizon"] = {}
        summary["WMAPE_ratio_to_h1_by_horizon"] = {}

    # worst dealers（overall）
    dealer_scores: List[Tuple[str, float, float, int]] = []
    for code, pairs in dealer_points.items():
        yy = [t[0] for t in pairs]
        pp = [t[1] for t in pairs]
        if len(yy) >= 3:
            dealer_scores.append((code, wmape(yy, pp), mae(yy, pp), len(yy)))
    dealer_scores.sort(key=lambda x: x[1], reverse=True)
    worst_overall = [{"dealer": c, "WMAPE": w, "MAE": m, "n_points": n} for c, w, m, n in dealer_scores[:TOP_K_WORST]]

    # worst dealers（by horizon）
    worst_by_h: Dict[str, Any] = {}
    for h, mp in sorted(dealer_points_by_h.items()):
        scores_h: List[Tuple[str, float, float, int]] = []
        for code, pairs in mp.items():
            yy = [t[0] for t in pairs]
            pp = [t[1] for t in pairs]
            if len(yy) >= 2:
                scores_h.append((code, wmape(yy, pp), mae(yy, pp), len(yy)))
        scores_h.sort(key=lambda x: x[1], reverse=True)
        worst_by_h[str(h)] = [{"dealer": c, "WMAPE": w, "MAE": m, "n_points": n} for c, w, m, n in scores_h[:TOP_K_WORST]]

    _save_json(OUT_SUMMARY_JSON, summary)
    _save_json(OUT_BY_HORIZON_JSON, by_h_out)
    _save_json(OUT_WORST_DEALERS_JSON, worst_overall)
    _save_json(OUT_WORST_BY_H_JSON, worst_by_h)
    _save_json(OUT_FAILS_JSON, failed)

    print("[eval] done.")
    print("[eval] summary\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[eval] saved: {OUT_SUMMARY_JSON}")
    print(f"[eval] saved: {OUT_BY_HORIZON_JSON}")
    print(f"[eval] saved: {OUT_WORST_DEALERS_JSON}")
    print(f"[eval] saved: {OUT_WORST_BY_H_JSON}")
    print(f"[eval] saved: {OUT_FAILS_JSON}")
    print(f"[eval] saved: {OUT_CONFIG_JSON}")


if __name__ == "__main__":
    main()
