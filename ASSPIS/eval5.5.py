# eval_phase2.py
# ------------------------------------------------------------
# Phase3.1 评估+调参脚本（替换版，兼容你现有用法）
#
# 用法（评估）：
#   python eval_phase2_7.py --train_mode conservative --roll_mode expanding --files "22-23数据.xlsx" "24年13维度数据.xlsx" --out_dir reports\p2_7
#
# 用法（多版本对比）：
#   python eval_phase2_7.py compare --baseline reports\B0 --experiments reports\A2 reports\C0 reports\E1 --out_dir reports\compare
# ------------------------------------------------------------

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import numpy as np
from pathlib import Path
from statistics import mean
from typing import Any
import pandas as pd
import time
# -------------------------
# Phase3.0/3.2: 预设（冻结基线与消融实验）
# -------------------------
_PRESETS: dict[str, dict[str, str]] = {
    # Phase 2.8 ablation
    "p2_8_r0": {"PHASE28_SAFE_DIVIDE": "0", "PHASE28_LOG_RATIO": "0", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r1": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "0", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r2": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r3": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1"},

    # Phase 3.2 消融实验专属 presets (基于 Phase 2.8 R3 最佳主干)
    "p3_1_base": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1",
                  "PHASE32_LOSS_L1": "0", "PHASE32_USE_WEIGHT": "0"},
    "p3_2_loss_only": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1",
                       "PHASE32_LOSS_L1": "1", "PHASE32_USE_WEIGHT": "0"},
    "p3_2_weight_only": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1",
                         "PHASE32_LOSS_L1": "0", "PHASE32_USE_WEIGHT": "1"},
    "p3_2_full": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1",
                  "PHASE32_LOSS_L1": "1", "PHASE32_USE_WEIGHT": "1"},
}

def _apply_preset(preset: str):
    if not preset:
        return
    p = preset.strip()
    if p not in _PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Allowed: {sorted(_PRESETS.keys())}")
    for k, v in _PRESETS[p].items():
        os.environ[k] = str(v)

def _env_snapshot(prefixes: tuple[str, ...] = ("TRAIN_", "ROLL_", "PHASE", "CLIP_")) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in os.environ.items():
        if any(k.startswith(p) for p in prefixes):
            out[k] = v
    return dict(sorted(out.items(), key=lambda kv: kv[0]))

def _write_json(path: Path, obj: Any):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)

def _phase3_score(derived: dict[str, Any], peak_std_coef: float = 0.25, dec_mean_coef: float = 0.35) -> dict[str, Any]:
    # score = weighted_WMAPE + a * peak_std + b * dec_mean
    wm_w = float(derived.get("wmape_weighted", float("nan")))
    peak_std = float(((derived.get("wmape_peak_11_12", {}) or {}).get("std", float("nan"))))
    dec_mean = float(((derived.get("wmape_dec", {}) or {}).get("mean", float("nan"))))
    score = wm_w
    if peak_std == peak_std:
        score += peak_std_coef * peak_std
    else:
        score = float("nan")
    if dec_mean == dec_mean:
        score += dec_mean_coef * dec_mean
    else:
        score = float("nan")
    return {
        "phase3_score": float(score),
        "phase3_score_components": {
            "wmape_weighted": wm_w,
            "peak_std_11_12": peak_std,
            "dec_mean": dec_mean,
        },
        "phase3_score_coeff": {
            "peak_std_coef": float(peak_std_coef),
            "dec_mean_coef": float(dec_mean_coef),
        },
    }


def _load_xgb_override(args: argparse.Namespace) -> dict | None:
    """从 --xgb_params_json / --xgb_params_file 读取 XGB 参数覆盖。"""
    js = getattr(args, "xgb_params_json", None)
    fp = getattr(args, "xgb_params_file", None)
    if js:
        try:
            return json.loads(js)
        except Exception as e:
            raise ValueError(f"--xgb_params_json 不是合法 JSON: {e}")
    if fp:
        p = Path(fp)
        if not p.exists():
            raise FileNotFoundError(f"--xgb_params_file 不存在: {p}")
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"--xgb_params_file 读取失败或不是 JSON: {e}")
    return None

def _discover_excel_files(cwd: Path) -> list[str]:
    candidates = [cwd / "data", cwd / "dataset", cwd / "datasets", cwd]
    exts = ("*.xlsx", "*.xls", "*.xlsm")
    files: list[Path] = []
    for d in candidates:
        if not d.exists():
            continue
        if d.is_dir():
            for ext in exts:
                files.extend(d.glob(ext))
        elif d == cwd:
            for ext in exts:
                files.extend(cwd.glob(ext))
    # 去重 + 按修改时间排序（新文件优先）
    uniq = {f.resolve(): f for f in files}
    out = sorted(uniq.values(), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in out]


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    # union fields (first row may not contain all)
    fieldset = set()
    for r in rows:
        fieldset.update(r.keys())
    fieldnames = list(fieldset)
    # keep stable ordering: common keys first
    preferred = ["time_key", "year", "month", "n_test", "sum_abs_y", "wmape_base", "wmape", "wmape_gain",
                 "smape", "mae", "rmse", "corr_log_mean_abs", "corr_log_mean"]
    fieldnames = preferred + [f for f in fieldnames if f not in preferred]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    xs2 = sorted(xs)
    if len(xs2) == 1:
        return float(xs2[0])
    k = (len(xs2) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs2) - 1)
    if f == c:
        return float(xs2[f])
    return float(xs2[f] * (c - k) + xs2[c] * (k - f))


def _agg_wmape_by_month(rows: list[dict], key: str) -> list[dict]:
    buckets: dict[int, list[dict]] = {}
    for r in rows:
        m = int(r.get("month", -1))
        if m < 1 or m > 12:
            continue
        buckets.setdefault(m, []).append(r)
    out: list[dict] = []
    for m in range(1, 13):
        rs = buckets.get(m, [])
        vals = [float(r.get(key, float("nan"))) for r in rs if r.get(key) is not None]
        vals = [v for v in vals if v == v]
        if not vals:
            continue
        w = [float(r.get("sum_abs_y", 0.0)) for r in rs]
        # weighted mean
        sw = sum(w) if sum(w) > 0 else 0.0
        wmean = sum(v * wi for v, wi in zip([float(r.get(key)) for r in rs], w) if wi is not None) / sw if sw > 0 else mean(vals)
        out.append({
            "month": m,
            f"{key}_mean": float(mean(vals)),
            f"{key}_std": float((sum((v - mean(vals)) ** 2 for v in vals) / max(1, len(vals) - 1)) ** 0.5),
            f"{key}_p10": _percentile(vals, 0.10),
            f"{key}_p50": _percentile(vals, 0.50),
            f"{key}_p90": _percentile(vals, 0.90),
            f"{key}_wmean": float(wmean),
            "n_folds": int(len(vals)),
        })
    return out


def _derived_metrics(rows: list[dict]) -> dict[str, Any]:
    def _safe(vals: list[float]) -> dict[str, float]:
        vals = [v for v in vals if v == v]
        if not vals:
            return {"mean": float("nan"), "std": float("nan")}
        mu = mean(vals)
        sd = (sum((v - mu) ** 2 for v in vals) / max(1, len(vals) - 1)) ** 0.5
        return {"mean": float(mu), "std": float(sd)}

    w = [float(r.get("sum_abs_y", 0.0)) for r in rows]
    wm = [float(r.get("wmape", float("nan"))) for r in rows]
    wmb = [float(r.get("wmape_base", float("nan"))) for r in rows]
    gain = [float(r.get("wmape_gain", float("nan"))) for r in rows]

    def _wmean(vals: list[float], weights: list[float]) -> float:
        pairs = [(v, wi) for v, wi in zip(vals, weights) if v == v and wi is not None and wi > 0]
        if not pairs:
            return float("nan")
        s = sum(wi for _, wi in pairs)
        return float(sum(v * wi for v, wi in pairs) / s) if s > 0 else float("nan")

    # peak subsets
    peak = [r for r in rows if int(r.get("month", 0)) in (11, 12)]
    nov = [r for r in rows if int(r.get("month", 0)) == 11]
    dec = [r for r in rows if int(r.get("month", 0)) == 12]

    out: dict[str, Any] = {
        "n_folds": int(len(rows)),
        "wmape_overall": _safe(wm),
        "wmape_weighted": _wmean(wm, w),
        "wmape_base_overall": _safe(wmb),
        "wmape_base_weighted": _wmean(wmb, w),
        "wmape_gain_overall": _safe(gain),
        "wmape_gain_weighted": _wmean(gain, w),
        "wmape_peak_11_12": _safe([float(r.get("wmape", float("nan"))) for r in peak]),
        "wmape_gain_peak_11_12": _safe([float(r.get("wmape_gain", float("nan"))) for r in peak]),
        "wmape_nov": _safe([float(r.get("wmape", float("nan"))) for r in nov]),
        "wmape_dec": _safe([float(r.get("wmape", float("nan"))) for r in dec]),
        "gain_positive_rate": float(sum(1 for g in gain if g == g and g > 0) / max(1, sum(1 for g in gain if g == g))),
        "bad_rate_wmape_ge_40": float(sum(1 for v in wm if v == v and v >= 40.0) / max(1, sum(1 for v in wm if v == v))),
        "corr_log_mean_abs": _safe([float(r.get("corr_log_mean_abs", float("nan"))) for r in rows]),
    }
    return out


def run_eval(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists() and args.fail_if_exists:
        print(f"[ERROR] out_dir 已存在：{out_dir}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    # set env BEFORE importing model (model reads env vars at import time)
    os.environ["TRAIN_MODE"] = args.train_mode
    os.environ["ROLL_MODE"] = args.roll_mode

    # Phase3.0 preset (sets PHASE28_* etc) BEFORE importing model
    try:
        _apply_preset(getattr(args, 'preset', '') or '')
    except Exception as e:
        print(f"[ERROR] preset 设置失败: {e}")
        return 2

    # files
    cwd = Path.cwd()
    files = list(args.files) if args.files else []
    if not files and args.data_dir:
        dd = Path(args.data_dir)
        if dd.exists() and dd.is_dir():
            files = [str(p) for p in dd.glob("*.xlsx")] + [str(p) for p in dd.glob("*.xls")] + [str(p) for p in dd.glob("*.xlsm")]
    if not files:
        files = _discover_excel_files(cwd)

    if not files:
        print("[ERROR] 未发现 Excel 文件。请用 --files 或 --data_dir 指定。")
        return 2

    print("Excel files:")
    for f in files:
        print(" -", f)

    # import project modules
    try:
        from dealer_data_preprocessing import load_and_process_data
    except Exception as e:
        print(f"[ERROR] 导入 dealer_data_preprocessing 失败: {e}")
        return 2

    try:
        dealers, dealer_codes = load_and_process_data(files)
    except Exception as e:
        print(f"[ERROR] load_and_process_data 失败: {e}")
        return 2

    try:
        import model
        xgb_override = _load_xgb_override(args)
        best_model, scaler, X, y, y_pred = model.train_model(
            dealers,
            xgb_params_override=xgb_override,
            skip_kfold=bool(getattr(args, "skip_kfold", False)),
            quiet=False,
        )
    except Exception as e:
        print(f"[ERROR] 训练/评估失败: {e}")
        return 2

    rolling_rows = getattr(best_model, "rolling_rows_", []) or []
    rolling_summary = getattr(best_model, "rolling_summary_", {}) or {}

    # save outputs
    _write_csv(out_dir / "rolling_rows.csv", rolling_rows)
    with (out_dir / "rolling_summary.json").open("w", encoding="utf-8") as f:
        json.dump(rolling_summary, f, ensure_ascii=False, indent=2, default=str)

    # month-of-year stats (wmape + optional wmape_base)
    moy = _agg_wmape_by_month(rolling_rows, "wmape")
    moy_base = _agg_wmape_by_month(rolling_rows, "wmape_base")
    # merge
    merged: dict[int, dict] = {}
    for r in moy:
        merged[int(r["month"])] = dict(r)
    for r in moy_base:
        m = int(r["month"])
        merged.setdefault(m, {"month": m})
        merged[m].update(r)
    _write_csv(out_dir / "wmape_by_month_of_year.csv", list(merged.values()))

    # derived metrics
    dm = _derived_metrics(rolling_rows)
    # Phase3.0: compute Phase3 KPI score (for later Optuna objective reuse)
    try:
        dm.update(_phase3_score(dm, peak_std_coef=float(getattr(args, "score_peak_std_coef", 0.25)), dec_mean_coef=float(getattr(args, "score_dec_mean_coef", 0.35))))
    except Exception:
        pass
    _write_json(out_dir / "derived_metrics.json", dm)

    # Phase3.0: write run manifest for reproducibility
    if not getattr(args, "no_manifest", False):
        from datetime import datetime, timezone
        manifest: dict[str, Any] = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "cwd": str(Path.cwd().resolve()),
            "python": sys.version,
            "argv": sys.argv,
            "args": {k: (list(v) if isinstance(v, tuple) else v) for k, v in vars(args).items() if k != "func"},
            "excel_files": [str(Path(p).resolve()) for p in files],
            "env_raw": _env_snapshot(),
        }
        # resolved model config (includes defaults)
        try:
            cfg = getattr(best_model, "config_", None)
            if cfg is None:
                import model as _m
                cfg = _m.get_runtime_config() if hasattr(_m, "get_runtime_config") else None
            manifest["model_config_resolved"] = cfg
        except Exception:
            manifest["model_config_resolved"] = None
        _write_json(out_dir / "run_manifest.json", manifest)

    print("\nSaved to:", str(out_dir))
    return 0


def run_compare(args: argparse.Namespace) -> int:
    base_dir = Path(args.baseline).resolve()
    exp_dirs = [Path(p).resolve() for p in args.experiments]
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists() and args.fail_if_exists:
        print(f"[ERROR] out_dir 已存在：{out_dir}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    def _read_rows(d: Path) -> list[dict]:
        p = d / "rolling_rows.csv"
        if not p.exists():
            raise FileNotFoundError(str(p))
        import pandas as pd
        df = pd.read_csv(p)
        return df.to_dict("records")

    base = _read_rows(base_dir)
    # index by time_key
    bmap = {int(r["time_key"]): r for r in base if "time_key" in r}

    import pandas as pd
    summary_rows = []
    delta_rows = []

    for ed in exp_dirs:
        ex = _read_rows(ed)
        emap = {int(r["time_key"]): r for r in ex if "time_key" in r}
        keys = sorted(set(bmap.keys()) & set(emap.keys()))
        if not keys:
            continue
        deltas = []
        for k in keys:
            bw = float(bmap[k].get("wmape", float("nan")))
            ew = float(emap[k].get("wmape", float("nan")))
            if bw == bw and ew == ew:
                deltas.append(ew - bw)
                delta_rows.append({
                    "experiment": ed.name,
                    "time_key": k,
                    "delta_wmape": ew - bw,
                    "wmape_base": bw,
                    "wmape_exp": ew,
                    "month": int(emap[k].get("month", -1)),
                    "sum_abs_y": float(emap[k].get("sum_abs_y", float("nan"))),
                })
        if not deltas:
            continue
        deltas_sorted = sorted(deltas)
        mu = mean(deltas_sorted)
        p10 = _percentile(deltas_sorted, 0.10)
        p50 = _percentile(deltas_sorted, 0.50)
        p90 = _percentile(deltas_sorted, 0.90)
        improve = sum(1 for d in deltas_sorted if d < 0) / len(deltas_sorted)
        summary_rows.append({
            "experiment": ed.name,
            "n_pairs": len(deltas_sorted),
            "delta_wmape_mean": float(mu),
            "delta_wmape_p10": float(p10),
            "delta_wmape_p50": float(p50),
            "delta_wmape_p90": float(p90),
            "improve_rate": float(improve),
        })

    if summary_rows:
        df = pd.DataFrame(summary_rows).sort_values("delta_wmape_mean")
        df.to_csv(out_dir / "compare_summary.csv", index=False, encoding="utf-8-sig")

    # Phase3.0: aggregate KPI compare (derived_metrics.json)
    def _read_dm(d: Path) -> dict[str, Any] | None:
        p = d / "derived_metrics.json"
        if not p.exists():
            return None
        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    base_dm = _read_dm(base_dir) or {}
    kpi_rows = []
    for ed in exp_dirs:
        dm = _read_dm(ed) or {}
        row = {
            "experiment": ed.name,
            "wmape_weighted_base": float(base_dm.get("wmape_weighted", float("nan"))),
            "wmape_weighted_exp": float(dm.get("wmape_weighted", float("nan"))),
            "phase3_score_base": float(base_dm.get("phase3_score", float("nan"))),
            "phase3_score_exp": float(dm.get("phase3_score", float("nan"))),
            "peak_std_base": float(((base_dm.get("wmape_peak_11_12", {}) or {}).get("std", float("nan")))),
            "peak_std_exp": float(((dm.get("wmape_peak_11_12", {}) or {}).get("std", float("nan")))),
            "dec_mean_base": float(((base_dm.get("wmape_dec", {}) or {}).get("mean", float("nan")))),
            "dec_mean_exp": float(((dm.get("wmape_dec", {}) or {}).get("mean", float("nan")))),
        }
        # deltas
        row["delta_wmape_weighted"] = row["wmape_weighted_exp"] - row["wmape_weighted_base"]
        row["delta_phase3_score"] = row["phase3_score_exp"] - row["phase3_score_base"]
        row["delta_peak_std"] = row["peak_std_exp"] - row["peak_std_base"]
        row["delta_dec_mean"] = row["dec_mean_exp"] - row["dec_mean_base"]
        kpi_rows.append(row)

    if kpi_rows:
        dfk = pd.DataFrame(kpi_rows).sort_values("delta_phase3_score")
        dfk.to_csv(out_dir / "compare_kpi.csv", index=False, encoding="utf-8-sig")

    if delta_rows:
        df2 = pd.DataFrame(delta_rows).sort_values(["experiment", "time_key"])
        df2.to_csv(out_dir / "compare_deltas.csv", index=False, encoding="utf-8-sig")

    print("Saved compare to:", str(out_dir))
    return 0



def run_tune(args: argparse.Namespace) -> int:
    """Phase3.1: 一键调参（Optuna 主线 + Random Search baseline），并导出最终 rolling 评估结果。"""
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists() and args.fail_if_exists:
        print(f"[ERROR] out_dir 已存在：{out_dir}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    # set env BEFORE importing model (model reads env vars at import time)
    os.environ["TRAIN_MODE"] = args.train_mode
    os.environ["ROLL_MODE"] = args.roll_mode

    # preset BEFORE importing model
    try:
        _apply_preset(getattr(args, "preset", "") or "")
    except Exception as e:
        print(f"[ERROR] preset 设置失败: {e}")
        return 2

    # files (same logic as run_eval)
    cwd = Path.cwd()
    files = list(args.files) if args.files else []
    if not files and args.data_dir:
        dd = Path(args.data_dir)
        if dd.exists() and dd.is_dir():
            files = [str(p) for p in dd.glob("*.xlsx")] + [str(p) for p in dd.glob("*.xls")] + [str(p) for p in dd.glob("*.xlsm")]
    if not files:
        files = _discover_excel_files(cwd)
    if not files:
        print("[ERROR] 未发现 Excel 文件。请用 --files 或 --data_dir 指定。")
        return 2

    print("Excel files:")
    for f in files:
        print(" -", f)

    # import project modules
    try:
        from dealer_data_preprocessing import load_and_process_data
    except Exception as e:
        print(f"[ERROR] 导入 dealer_data_preprocessing 失败: {e}")
        return 2

    try:
        dealers, dealer_codes = load_and_process_data(files)
    except Exception as e:
        print(f"[ERROR] load_and_process_data 失败: {e}")
        return 2

    # import model after env/preset is set
    try:
        import model
    except Exception as e:
        print(f"[ERROR] 导入 model 失败: {e}")
        return 2

    # prepare once
    try:
        prep = model.prepare_training_data(dealers)
    except Exception as e:
        print(f"[ERROR] prepare_training_data 失败: {e}")
        return 2

    print(f"[Prepared] N={len(prep.y_raw)} | d={prep.feature_dim} | unique_time_keys={len(np.unique(prep.time_keys))}")

    # score coefficients
    peak_std_coef = float(getattr(args, "score_peak_std_coef", 0.25))
    dec_mean_coef = float(getattr(args, "score_dec_mean_coef", 0.35))

    def _score_rows(rows: list[dict]) -> dict:
        dm = _derived_metrics(rows)
        dm.update(_phase3_score(dm, peak_std_coef=peak_std_coef, dec_mean_coef=dec_mean_coef))
        return dm

    # baseline params (conservative defaults)
    try:
        base_params = model._get_default_xgb_params(args.train_mode) if hasattr(model, "_get_default_xgb_params") else {}
    except Exception:
        base_params = {}

    # enforce fixed trees globally for fairness (baseline/random/optuna/export)
    _fixed = getattr(args, "fixed_n_estimators", None)
    if _fixed is not None:
        base_params = dict(base_params)
        base_params["n_estimators"] = int(_fixed)

    t0_base = time.time()
    print("[Baseline@tune] start rolling_backtest_prepared ...", flush=True)

    base_rows, _ = model.rolling_backtest_prepared(
        prep,
        base_params,
        last_n_folds=int(args.tune_last_n_folds) if args.tune_last_n_folds else None,
        quiet=True,
    )

    print(f"[Baseline@tune] done in {(time.time() - t0_base) / 60:.1f} min", flush=True)

    base_dm = _score_rows(base_rows)
    base_score = float(base_dm.get("phase3_score", float("nan")))
    if base_score != base_score:
        base_score = float("inf")
    print(
        f"[Baseline@tune] phase3_score={base_score:.4f} | wmape_weighted={base_dm.get('wmape_weighted'):.4f} | "
        f"peak_std={base_dm.get('wmape_peak_11_12', {}).get('std'):.4f} | dec_mean={base_dm.get('wmape_dec', {}).get('mean'):.4f}",
        flush=True
    )
    # -------------------------
    # Optuna tuning (single-objective or multi-objective)
    # -------------------------
    best_optuna_params: dict | None = None
    best_optuna_score: float | None = None
    best_optuna_tag: str | None = None  # for reporting

    # 5.5：关注 overall WMAPE 与旺季稳定性（Peak Std）
    tune_metric = str(getattr(args, "tune_metric", "phase3_score"))
    tradeoff_lambda = float(getattr(args, "tradeoff_lambda", 1.0))
    optuna_mode = str(getattr(args, "optuna_mode", "single")).lower().strip()  # single | mo

    def _kpis(dm: dict[str, Any]) -> tuple[float, float]:
        wm = float(dm.get("wmape_weighted", float("inf")))
        ps = float(((dm.get("wmape_peak_11_12", {}) or {}).get("std", float("inf"))))
        if wm != wm:
            wm = float("inf")
        if ps != ps:
            ps = float("inf")
        return wm, ps

    def _tune_score(dm: dict[str, Any]) -> float:
        # 兼容旧 Phase3.1 的 score，也支持 5.5 的 WMAPE / Composite
        if tune_metric == "wmape_only":
            wm, _ = _kpis(dm)
            return wm
        if tune_metric == "peak_only":
            _, ps = _kpis(dm)
            return ps
        if tune_metric == "wmape_composite":
            wm, ps = _kpis(dm)
            return wm + tradeoff_lambda * ps
        # default: phase3_score（旧口径）
        s = float(dm.get("phase3_score", float("inf")))
        if s != s:
            s = float("inf")
        return s

    if not getattr(args, "skip_optuna", False):
        try:
            import optuna
        except Exception as e:
            print("[ERROR] 未安装 optuna。请先安装：pip install optuna")
            print("  错误信息：", e)
            return 2

        # optuna storage：默认放在 out_dir/optuna 下，避免历史污染（5.5 必须公平预算）
        opt_root = out_dir / "optuna"
        opt_root.mkdir(parents=True, exist_ok=True)
        optuna_db = getattr(args, "optuna_db", None)
        if optuna_db:
            db_path = Path(optuna_db).expanduser().resolve()
        else:
            db_path = (opt_root / "optuna_journal.db").resolve()
        storage = "sqlite:///" + str(db_path).replace("\\", "/")

        n_trials = int(getattr(args, "optuna_trials", 30))
        fixed_n_estimators = getattr(args, "fixed_n_estimators", None)
        fixed_n_estimators = int(fixed_n_estimators) if fixed_n_estimators is not None else None

        if optuna_mode == "mo":
            # Multi-objective: minimize (wmape_weighted, peak_std_11_12)
            sampler = optuna.samplers.NSGAIISampler(seed=int(getattr(args, "seed", 42)))
            study = optuna.create_study(
                study_name="sales_forecast_mo",
                storage=storage,
                load_if_exists=False,
                directions=("minimize", "minimize"),
                sampler=sampler,
            )

            def objective_mo(trial: "optuna.Trial"):
                params = {
                    "learning_rate": float(trial.suggest_float("learning_rate", 0.01, 0.15, log=True)),
                    "max_depth": int(trial.suggest_int("max_depth", 3, 8)),
                    "min_child_weight": int(trial.suggest_int("min_child_weight", 1, 15)),
                    "subsample": float(trial.suggest_float("subsample", 0.6, 1.0)),
                    "colsample_bytree": float(trial.suggest_float("colsample_bytree", 0.6, 1.0)),
                    "reg_alpha": float(trial.suggest_float("reg_alpha", 1e-4, 5.0, log=True)),
                    "reg_lambda": float(trial.suggest_float("reg_lambda", 1e-2, 20.0, log=True)),
                    "gamma": float(trial.suggest_float("gamma", 0.0, 3.0)),
                }
                if fixed_n_estimators is None:
                    params["n_estimators"] = int(trial.suggest_int("n_estimators", 300, 2000, step=50))
                else:
                    params["n_estimators"] = fixed_n_estimators

                full_params = {**base_params, **params}
                rows, _ = model.rolling_backtest_prepared(
                    prep,
                    full_params,
                    last_n_folds=int(args.tune_last_n_folds) if args.tune_last_n_folds else None,
                    quiet=True,
                )
                dm = _score_rows(rows)
                wm, ps = _kpis(dm)
                return wm, ps

            study.optimize(objective_mo, n_trials=n_trials)

            # 所有 trials（用于画散点）
            all_rows = []
            for t in study.trials:
                if t.values is None or len(t.values) != 2:
                    continue
                wm, ps = float(t.values[0]), float(t.values[1])
                comp = wm + tradeoff_lambda * ps
                all_rows.append({
                    "trial_number": t.number,
                    "wmape_weighted": wm,
                    "peak_std_11_12": ps,
                    "wmape_composite": comp,
                    **t.params,
                })
            if all_rows:
                pd.DataFrame(all_rows).sort_values(["wmape_weighted", "peak_std_11_12"]).to_csv(
                    opt_root / "trials_2obj.csv", index=False, encoding="utf-8-sig"
                )

            # Pareto 前沿
            pareto = []
            for t in getattr(study, "best_trials", []) or []:
                wm, ps = float(t.values[0]), float(t.values[1])
                pareto.append({
                    "trial_number": t.number,
                    "wmape_weighted": wm,
                    "peak_std_11_12": ps,
                    "wmape_composite": wm + tradeoff_lambda * ps,
                    **t.params,
                })
            if pareto:
                dfp = pd.DataFrame(pareto).sort_values(["wmape_weighted", "peak_std_11_12"])
                # knee（到乌托邦点的归一化距离最小）
                wm_min, wm_max = float(dfp["wmape_weighted"].min()), float(dfp["wmape_weighted"].max())
                ps_min, ps_max = float(dfp["peak_std_11_12"].min()), float(dfp["peak_std_11_12"].max())
                denom_wm = (wm_max - wm_min) if (wm_max - wm_min) > 1e-12 else 1.0
                denom_ps = (ps_max - ps_min) if (ps_max - ps_min) > 1e-12 else 1.0
                dfp["dist_utopia"] = ((dfp["wmape_weighted"] - wm_min) / denom_wm) ** 2 + ((dfp["peak_std_11_12"] - ps_min) / denom_ps) ** 2
                dfp.to_csv(opt_root / "pareto_front.csv", index=False, encoding="utf-8-sig")

                # 代表性解：best_wmape / best_peak / best_composite / knee
                def _row_to_pick(df: "pd.DataFrame", idx: int) -> dict:
                    r = df.iloc[int(idx)].to_dict()
                    return r

                pick_best_wmape = _row_to_pick(dfp, int(dfp["wmape_weighted"].values.argmin()))
                pick_best_peak = _row_to_pick(dfp, int(dfp["peak_std_11_12"].values.argmin()))
                pick_best_comp = _row_to_pick(dfp, int(dfp["wmape_composite"].values.argmin()))
                pick_knee = _row_to_pick(dfp, int(dfp["dist_utopia"].values.argmin()))

                picks = {
                    "best_wmape": pick_best_wmape,
                    "best_peak": pick_best_peak,
                    "best_composite": pick_best_comp,
                    "knee": pick_knee,
                    "tradeoff_lambda": tradeoff_lambda,
                }
                _write_json(opt_root / "selected_trials.json", picks)

                # 默认用 best_composite 作为后续 full rolling 导出（折中解）
                drop_cols = {"trial_number", "wmape_weighted", "peak_std_11_12", "wmape_composite", "dist_utopia"}
                best_optuna_params = {k: v for k, v in pick_best_comp.items() if k not in drop_cols}
                best_optuna_score = float(pick_best_comp["wmape_composite"])
                best_optuna_tag = "mo_best_composite"
            else:
                print("[WARN] Optuna MO 未产生有效 Pareto trials（可能 trials 太少或评估失败）。")
                best_optuna_params = None
                best_optuna_score = None
                best_optuna_tag = None

        else:
            # Single-objective: minimize tune_metric
            sampler = optuna.samplers.TPESampler(seed=int(getattr(args, "seed", 42)))
            study = optuna.create_study(
                study_name="sales_forecast_single",
                storage=storage,
                load_if_exists=False,
                direction="minimize",
                sampler=sampler,
            )

            def objective_single(trial: "optuna.Trial") -> float:
                params = {
                    "learning_rate": float(trial.suggest_float("learning_rate", 0.01, 0.15, log=True)),
                    "max_depth": int(trial.suggest_int("max_depth", 3, 8)),
                    "min_child_weight": int(trial.suggest_int("min_child_weight", 1, 15)),
                    "subsample": float(trial.suggest_float("subsample", 0.6, 1.0)),
                    "colsample_bytree": float(trial.suggest_float("colsample_bytree", 0.6, 1.0)),
                    "reg_alpha": float(trial.suggest_float("reg_alpha", 1e-4, 5.0, log=True)),
                    "reg_lambda": float(trial.suggest_float("reg_lambda", 1e-2, 20.0, log=True)),
                    "gamma": float(trial.suggest_float("gamma", 0.0, 3.0)),
                }
                if fixed_n_estimators is None:
                    params["n_estimators"] = int(trial.suggest_int("n_estimators", 300, 2000, step=50))
                else:
                    params["n_estimators"] = fixed_n_estimators

                full_params = {**base_params, **params}
                rows, _ = model.rolling_backtest_prepared(
                    prep,
                    full_params,
                    last_n_folds=int(args.tune_last_n_folds) if args.tune_last_n_folds else None,
                    quiet=True,
                )
                dm = _score_rows(rows)
                return float(_tune_score(dm))

            study.optimize(objective_single, n_trials=n_trials)

            best_optuna_params = dict(study.best_params)
            best_optuna_score = float(study.best_value)
            best_optuna_tag = "single_best"

            _write_json(opt_root / "best_params.json", best_optuna_params)
            _write_json(opt_root / "best_value.json", {
                "best_score": best_optuna_score,
                "tune_metric": tune_metric,
                "tradeoff_lambda": tradeoff_lambda
            })
            try:
                df_trials = study.trials_dataframe()
                df_trials.to_csv(opt_root / "trials_single.csv", index=False, encoding="utf-8-sig")
            except Exception:
                pass

        if best_optuna_params is not None:
            print(f"[Optuna] mode={optuna_mode} best_tag={best_optuna_tag} best_score={best_optuna_score:.6f} (metric={tune_metric})")
            if optuna_mode == "mo":
                _write_json(opt_root / "best_params_recommended.json", best_optuna_params)
                _write_json(opt_root / "best_value_recommended.json", {
                    "wmape_composite": best_optuna_score,
                    "tune_metric": tune_metric,
                    "tradeoff_lambda": tradeoff_lambda,
                    "tag": best_optuna_tag,
                })

    # -------------------------
    # Random Search baseline (5.5 friendly)
    # -------------------------
    best_rand_params: dict | None = None
    best_rand_score: float | None = None
    rand_trials = []

    if not getattr(args, "skip_random", False):
        rng = np.random.default_rng(int(getattr(args, "seed", 42)) + 17)
        fixed_n_estimators = getattr(args, "fixed_n_estimators", None)
        fixed_n_estimators = int(fixed_n_estimators) if fixed_n_estimators is not None else None

        def sample_one() -> dict:
            def logu(a, b):
                return float(10 ** rng.uniform(np.log10(a), np.log10(b)))

            p = {
                "learning_rate": logu(0.01, 0.15),
                "max_depth": int(rng.integers(3, 9)),
                "min_child_weight": int(rng.integers(1, 16)),
                "subsample": float(rng.uniform(0.6, 1.0)),
                "colsample_bytree": float(rng.uniform(0.6, 1.0)),
                "reg_alpha": logu(1e-4, 5.0),
                "reg_lambda": logu(1e-2, 20.0),
                "gamma": float(rng.uniform(0.0, 3.0)),
            }
            if fixed_n_estimators is None:
                p["n_estimators"] = int(rng.integers(300, 2001) // 50 * 50)
            else:
                p["n_estimators"] = fixed_n_estimators
            return p

        n_iter = int(getattr(args, "random_iters", 30))
        best_score = float("inf")
        best_params = None

        # —— 进度/落盘（方案A）——
        t0_all = time.time()
        rnd_dir = out_dir / "random"
        rnd_dir.mkdir(parents=True, exist_ok=True)
        partial_path = rnd_dir / "trials_partial.csv"

        print(
            f"[Random] start: n_iter={n_iter} last_n_folds={int(args.tune_last_n_folds) if args.tune_last_n_folds else None}",
            flush=True)

        for i in range(n_iter):
            params = sample_one()
            full_params = {**base_params, **params}

            t0 = time.time()
            print(f"[Random] -> {i + 1}/{n_iter} start params={params}", flush=True)

            rows, _ = model.rolling_backtest_prepared(
                prep,
                full_params,
                last_n_folds=int(args.tune_last_n_folds) if args.tune_last_n_folds else None,
                quiet=True,
            )

            dm = _score_rows(rows)
            wm, ps = _kpis(dm)
            score = float(_tune_score(dm))

            rand_trials.append({
                "iter": i,
                "tune_metric": tune_metric,
                "tune_score": score,
                "wmape_weighted": wm,
                "peak_std_11_12": ps,
                **params,
            })

            if score < best_score:
                best_score = score
                best_params = params

            # 每轮都落盘一次：你可以直接看 random/trials_partial.csv 是否在增长来判断“是否在跑”
            try:
                pd.DataFrame(rand_trials).to_csv(partial_path, index=False, encoding="utf-8-sig")
            except Exception:
                pass

            dt = time.time() - t0
            avg = (time.time() - t0_all) / (i + 1)
            eta = avg * (n_iter - (i + 1))
            print(
                f"[Random] <- {i + 1}/{n_iter} score={score:.6f} best={best_score:.6f} "
                f"dt={dt / 60:.1f}min ETA={eta / 60:.1f}min (metric={tune_metric})",
                flush=True
            )

        best_rand_params = dict(best_params or {})
        best_rand_score = float(best_score)
        print(f"[Random] best_score={best_rand_score:.6f} (metric={tune_metric})", flush=True)

        _write_json(rnd_dir / "best_params.json", best_rand_params)
        _write_json(rnd_dir / "best_value.json", {
            "best_score": best_rand_score,
            "tune_metric": tune_metric,
            "tradeoff_lambda": tradeoff_lambda
        })
        if rand_trials:
            pd.DataFrame(rand_trials).sort_values("tune_score").to_csv(
                rnd_dir / "trials.csv", index=False, encoding="utf-8-sig"
            )

    def _coerce_xgb_param_types(params: dict | None) -> dict | None:
        if params is None:
            return None
        p = dict(params)

        int_keys = ["max_depth", "min_child_weight", "n_estimators", "random_state"]
        for k in int_keys:
            if k in p and p[k] is not None:
                p[k] = int(float(p[k]))

        float_keys = ["learning_rate", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda", "gamma"]
        for k in float_keys:
            if k in p and p[k] is not None:
                p[k] = float(p[k])

        return p
    # -------------------------
    # Final full rolling export for baseline / optuna / random
    # -------------------------
    def _export(tag: str, xgb_override: dict | None):
        od = out_dir / tag
        od.mkdir(parents=True, exist_ok=True)

        best_model, scaler, X, y, y_pred = model.train_model(
            dealers,
            xgb_params_override=xgb_override,
            skip_kfold=True if xgb_override is not None else False,
            quiet=False,
        )

        rows = getattr(best_model, "rolling_rows_", []) or []
        summary = getattr(best_model, "rolling_summary_", {}) or {}

        _write_csv(od / "rolling_rows.csv", rows)
        _write_json(od / "rolling_summary.json", summary)

        moy = _agg_wmape_by_month(rows, "wmape")
        _write_csv(od / "wmape_by_month_of_year.csv", moy)

        dm = _derived_metrics(rows)
        dm.update(_phase3_score(dm, peak_std_coef=peak_std_coef, dec_mean_coef=dec_mean_coef))
        _write_json(od / "derived_metrics.json", dm)

        if not getattr(args, "no_manifest", False):
            from datetime import datetime, timezone
            manifest: dict[str, Any] = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "cwd": str(Path.cwd().resolve()),
                "python": sys.version,
                "argv": sys.argv,
                "tag": tag,
                "args": {k: (list(v) if isinstance(v, tuple) else v) for k, v in vars(args).items() if k != "func"},
                "excel_files": [str(Path(p).resolve()) for p in files],
                "env_raw": _env_snapshot(),
                "xgb_params_override": xgb_override,
            }
            try:
                cfg = getattr(best_model, "config_", None)
                if cfg is None:
                    cfg = model.get_runtime_config() if hasattr(model, "get_runtime_config") else None
                manifest["model_config_resolved"] = cfg
            except Exception:
                manifest["model_config_resolved"] = None
            _write_json(od / "run_manifest.json", manifest)

        return od

    base_dir = _export("baseline_full", dict(base_params))

    opt_dir = None
    rnd_dir = None

    if best_optuna_params is not None and getattr(args, "fixed_n_estimators", None) is not None:
        best_optuna_params = dict(best_optuna_params)
        best_optuna_params["n_estimators"] = int(getattr(args, "fixed_n_estimators"))

    if best_optuna_params is not None:
        opt_dir = _export("optuna_best_full", _coerce_xgb_param_types({**base_params, **best_optuna_params}))
    if best_rand_params is not None:
        rnd_dir = _export("random_best_full", _coerce_xgb_param_types({**base_params, **best_rand_params}))

    if getattr(args, "auto_compare", False):
        comps = []
        if opt_dir is not None:
            comps.append(str(opt_dir))
        if rnd_dir is not None:
            comps.append(str(rnd_dir))
        if comps:
            cmp_args = argparse.Namespace(
                baseline=str(base_dir),
                experiments=comps,
                out_dir=str(out_dir / "compare"),
                fail_if_exists=False,
            )
            run_compare(cmp_args)

    print("\n[Tune Done] Saved to:", str(out_dir))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    ap_eval = sub.add_parser("run", help="run evaluation (default)")
    ap_eval.add_argument("--train_mode", default="conservative", choices=["conservative", "standard", "advanced"])
    ap_eval.add_argument("--roll_mode", default="expanding", choices=["expanding", "sliding"])
    ap_eval.add_argument("--preset", default="p2_8_r3", choices=sorted(_PRESETS.keys()), help="Phase3.0 冻结基线预设（默认 p2_8_r3）")
    ap_eval.add_argument("--xgb_params_json", default=None, help="覆盖 XGB 参数（JSON 字符串）")
    ap_eval.add_argument("--xgb_params_file", default=None, help="覆盖 XGB 参数（JSON 文件路径）")
    ap_eval.add_argument("--skip_kfold", action="store_true", help="跳过 KFold/RandomizedSearch（仅 rolling 口径；用于已选好参数的最终评估）")
    ap_eval.add_argument("--score_peak_std_coef", type=float, default=0.25, help="Phase3 score: peak std 系数")
    ap_eval.add_argument("--score_dec_mean_coef", type=float, default=0.35, help="Phase3 score: Dec mean 系数")
    ap_eval.add_argument("--no_manifest", action="store_true", help="不写 run_manifest.json（不推荐）")
    ap_eval.add_argument("--files", nargs="*", default=None)
    ap_eval.add_argument("--data_dir", default=None)
    ap_eval.add_argument("--out_dir", default="reports/p2_7")
    ap_eval.add_argument("--fail_if_exists", action="store_true")
    ap_eval.set_defaults(func=run_eval)

    ap_tune = sub.add_parser("tune", help="Phase3.1 tuning: Optuna + Random Search baseline, then export full rolling results")
    ap_tune.add_argument("--train_mode", default="conservative", choices=["conservative", "standard", "advanced"])
    ap_tune.add_argument("--roll_mode", default="expanding", choices=["expanding", "sliding"])
    ap_tune.add_argument("--preset", default="p3_2_full", choices=sorted(_PRESETS.keys()))
    ap_tune.add_argument("--score_peak_std_coef", type=float, default=0.25)
    ap_tune.add_argument("--score_dec_mean_coef", type=float, default=0.35)
    ap_tune.add_argument("--files", nargs="*", default=None)
    ap_tune.add_argument("--data_dir", default=None)
    ap_tune.add_argument("--out_dir", required=True)
    ap_tune.add_argument("--tune_last_n_folds", type=int, default=20, help="tuning objective 只评估最后 N 个 rolling folds（提速）")
    ap_tune.add_argument("--optuna_trials", type=int, default=30)
    ap_tune.add_argument("--random_iters", type=int, default=30)
    ap_tune.add_argument("--seed", type=int, default=42)
    # ---- 5.5 additions ----
    ap_tune.add_argument("--optuna_mode", default="single", choices=["single", "mo"],
                         help="Optuna 模式：single=单目标；mo=双目标(WMAPE, PeakStd)")
    ap_tune.add_argument("--tune_metric", default="phase3_score",
                         choices=["phase3_score", "wmape_only", "wmape_composite", "peak_only"],
                         help="单目标/Random 的评分口径；5.5 推荐 wmape_only 或 wmape_composite")
    ap_tune.add_argument("--tradeoff_lambda", type=float, default=1.0,
                         help="Composite=WMAPE + lambda*PeakStd 的 lambda（仅对 wmape_composite/MO 选点有效）")
    ap_tune.add_argument("--fixed_n_estimators", type=int, default=None,
                         help="固定树数（建议 5.5 设为 2900 以隔离容量影响）；None 则参与搜索")
    ap_tune.add_argument("--optuna_db", default=None,
                         help="Optuna sqlite 路径；不填则默认 out_dir/optuna/optuna_journal.db（推荐，避免污染）")
    ap_tune.add_argument("--skip_optuna", action="store_true")
    ap_tune.add_argument("--skip_random", action="store_true")
    ap_tune.add_argument("--auto_compare", action="store_true")
    ap_tune.add_argument("--no_manifest", action="store_true")
    ap_tune.add_argument("--fail_if_exists", action="store_true")
    ap_tune.set_defaults(func=run_tune)

    ap_cmp = sub.add_parser("compare", help="compare multiple experiment out_dir against baseline")
    ap_cmp.add_argument("--baseline", required=True)
    ap_cmp.add_argument("--experiments", nargs="+", required=True)
    ap_cmp.add_argument("--out_dir", required=True)
    ap_cmp.add_argument("--fail_if_exists", action="store_true")
    ap_cmp.set_defaults(func=run_compare)

    # default to run if no subcommand
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in ("run", "compare", "tune")):
        # emulate: run ...
        args = ap.parse_args(["run"] + sys.argv[1:])
    else:
        args = ap.parse_args()

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
