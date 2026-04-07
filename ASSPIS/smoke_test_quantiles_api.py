import json
import math
import requests
import matplotlib.pyplot as plt
import os
# -----------------------------
# 配置区：按需改这里即可
# -----------------------------
FORECAST_URL = "/forecast/quantiles"
ORIGINAL_URL = "/sales/original"

DEALER_CODE = "B450099"

# 做回测：用 base_month=7 预测 8~10
BASE_MONTH = 7
HORIZONS = 3                  # 预测 8,9,10
QUANTILES = [0.1, 0.5, 0.9]

# 情景：baseline vs leads+10%
SCENARIOS = [
    {"name": "baseline"},
    {"name": "leads+10%", "dimension": "leads", "change_percentage": 10},
]

CALIB_ALPHA = 0.2             # CQR 80% 区间

# 如果你想把真实值手动填进来（当 ORIGINAL_URL 不可用时），就写这里：
MANUAL_ACTUALS = None
# 例子：
# MANUAL_ACTUALS = {8: 120.0, 9: 115.0, 10: 140.0}


# -----------------------------
# 评估指标
# -----------------------------
def _safe_div(a, b, eps=1e-9):
    return a / (b if abs(b) > eps else eps)

def mae(y, p):
    return sum(abs(yy - pp) for yy, pp in zip(y, p)) / len(y)

def rmse(y, p):
    return math.sqrt(sum((yy - pp) ** 2 for yy, pp in zip(y, p)) / len(y))

def mape(y, p, eps=1e-9):
    return sum(abs(_safe_div(yy - pp, yy, eps)) for yy, pp in zip(y, p)) / len(y)

def smape(y, p, eps=1e-9):
    out = 0.0
    for yy, pp in zip(y, p):
        denom = (abs(yy) + abs(pp))
        out += abs(yy - pp) / (denom if denom > eps else eps)
    return 2.0 * out / len(y)

def wmape(y, p, eps=1e-9):
    num = sum(abs(yy - pp) for yy, pp in zip(y, p))
    den = sum(abs(yy) for yy in y)
    return _safe_div(num, den, eps)

def coverage(y, lo, hi):
    ok = 0
    for yy, l, h in zip(y, lo, hi):
        if l <= yy <= h:
            ok += 1
    return ok / len(y)

def avg_width(lo, hi):
    return sum(max(h - l, 0.0) for l, h in zip(lo, hi)) / len(lo)


# -----------------------------
# 拉真实值：优先走 /sales/original
# -----------------------------
def fetch_actuals(dealer_code, months):
    if MANUAL_ACTUALS is not None:
        return {m: float(MANUAL_ACTUALS[m]) for m in months if m in MANUAL_ACTUALS}

    # 你的 original 接口支持：?dealer_code=...&months=10 这样的参数（从日志看）:contentReference[oaicite:3]{index=3}
    # 这里我们直接传 months 为最大月，然后从返回里截取需要月份（兼容不同返回格式）
    max_m = max(months)
    r = requests.get(ORIGINAL_URL, params={"dealer_code": dealer_code, "months": max_m}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"/sales/original failed status={r.status_code}, text={r.text}")

    data = r.json()

    # 兼容你后端可能的返回：{"months":[...], "sales":[...]} 或 {"sales":{...}}
    if isinstance(data, dict) and "sales" in data and isinstance(data["sales"], dict):
        sales_map = {int(k): float(v) for k, v in data["sales"].items()}
        return {m: sales_map.get(int(m)) for m in months}

    if isinstance(data, dict) and "months" in data and "sales" in data and isinstance(data["months"], list) and isinstance(data["sales"], list):
        sales_map = {int(m): float(s) for m, s in zip(data["months"], data["sales"])}
        return {m: sales_map.get(int(m)) for m in months}
    # 新增：兼容 {"data":[{"month":1,"sales":232.0}, ...], ...}
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        sales_map = {}
        for row in data["data"]:
            if isinstance(row, dict) and "month" in row and "sales" in row:
                sales_map[int(row["month"])] = float(row["sales"])
        return {m: sales_map.get(int(m)) for m in months}

    # 如果格式不匹配，直接把原始返回打印出来便于你调
    raise RuntimeError(f"Unrecognized /sales/original response format: {json.dumps(data, ensure_ascii=False)[:2000]}")


# -----------------------------
# 主流程：请求预测 + 对比评估 + 画图
# -----------------------------
def main():
    payload = {
        "dealer_code": DEALER_CODE,
        "base_month": BASE_MONTH,
        "horizons": HORIZONS,
        "quantiles": QUANTILES,
        "scenarios": SCENARIOS,
        "calibration_alpha": CALIB_ALPHA,
    }

    r = requests.post(FORECAST_URL, json=payload, timeout=120)
    print("status:", r.status_code)
    if r.status_code != 200:
        print("Request failed. Response text:", r.text)
        return

    data = r.json()
    print("Response meta:", json.dumps({k: data.get(k) for k in ["dealer_code", "base_month", "meta"]}, ensure_ascii=False, indent=2))

    # -------- 取 baseline 预测 --------
    sc_base = data["scenarios"]["baseline"]
    months_pred = sc_base["months"]              # 例如 [8,9,10]
    point_base = sc_base["point"]
    q10_base = sc_base["quantiles"].get("0.1")
    q90_base = sc_base["quantiles"].get("0.9")

    # sanity：长度一致
    assert len(months_pred) == len(point_base), "months vs point length mismatch"

    # -------- 拉真实值（用于回测）--------
    actual_map = fetch_actuals(DEALER_CODE, months_pred)
    y_true = []
    y_pred = []
    lo = []
    hi = []

    for i, m in enumerate(months_pred):
        yt = actual_map.get(int(m), None)
        if yt is None:
            # 没有真实值就跳过（但会提示）
            print(f"[WARN] month {m} has no actual sales in /sales/original response, skip in metrics.")
            continue
        y_true.append(float(yt))
        y_pred.append(float(point_base[i]))
        if q10_base is not None and q90_base is not None:
            lo.append(float(q10_base[i]))
            hi.append(float(q90_base[i]))

    # -------- 打印误差指标 --------
    if len(y_true) >= 1:
        print("\n=== Backtest (baseline) ===")
        print("months:", months_pred)
        print("actual:", [round(v, 3) for v in y_true])
        print("pred  :", [round(v, 3) for v in y_pred])

        print(f"MAE  : {mae(y_true, y_pred):.4f}")
        print(f"RMSE : {rmse(y_true, y_pred):.4f}")
        print(f"MAPE : {mape(y_true, y_pred)*100:.2f}%")
        print(f"SMAPE: {smape(y_true, y_pred)*100:.2f}%")
        print(f"WMAPE: {wmape(y_true, y_pred)*100:.2f}%")

        if len(lo) == len(y_true) and len(hi) == len(y_true):
            cov = coverage(y_true, lo, hi)
            width = avg_width(lo, hi)
            print(f"Coverage(q10-q90): {cov*100:.2f}%")
            print(f"AvgWidth(q10-q90): {width:.4f}")
    else:
        print("\n[WARN] No actuals found for predicted months. Metrics skipped.")

    # -------- baseline vs leads+10% 敏感性检查 --------
    if "leads+10%" in data["scenarios"]:
        sc2 = data["scenarios"]["leads+10%"]
        point2 = sc2["point"]
        print("\n=== Scenario Sensitivity: leads+10% vs baseline (point) ===")
        for m, b, s in zip(months_pred, point_base, point2):
            diff = float(s) - float(b)
            rel = 100.0 * _safe_div(diff, float(b), 1e-9)
            print(f"month {m}: baseline={b:.4f}, leads+10%={s:.4f}, diff={diff:.4f} ({rel:+.2f}%)")

    # -------- 画图：point + 区间 + 真实值 --------
    plt.figure()
    plt.plot(months_pred, point_base, marker="o", label="pred(q0.5) baseline")

    if q10_base is not None and q90_base is not None:
        plt.fill_between(months_pred, q10_base, q90_base, alpha=0.2, label="q10-q90 baseline")

    # 真实值（如果存在）
    if len(y_true) >= 1:
        # 对齐预测月份：只画有实际的点
        months_true = []
        for m in months_pred:
            if actual_map.get(int(m)) is not None:
                months_true.append(int(m))
        plt.plot(months_true, y_true, marker="x", linestyle="--", label="actual")

    # 情景线
    if "leads+10%" in data["scenarios"]:
        plt.plot(months_pred, data["scenarios"]["leads+10%"]["point"], marker="o", label="pred(q0.5) leads+10%")

    plt.xlabel("Month")
    plt.ylabel("Sales")
    plt.title(f"{DEALER_CODE}  base_month={BASE_MONTH}  predict={months_pred}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("smoke_backtest_line.png", dpi=160, bbox_inches="tight")
    plt.show()

    # 打印完整 JSON（可选，太大就注释掉）
    # print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
