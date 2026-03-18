# selector_service.py
# ------------------------------------------------------------
# 离线选模与上线包生成服务（由原 eval_phase2 / eval5.5 脚本重构）
#
# 目标：
# 1) 保留 baseline / Random / Optuna 的离线决策流程
# 2) 不再依赖“服务启动即重跑评估”，而是显式作为离线模型生产器执行
# 3) 统一生成：
#    - point bundle
#    - quantile bundle（若 quantile_forecast.py 可用）
#    - manifest
#    - registry
#    - candidate reports
# 4) 同时保留 CLI 入口，便于你现阶段继续手动运行
# ------------------------------------------------------------
from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import pandas as pd


# -------------------------
# 预设：沿用你当前实验脚本中的 preset 逻辑
# -------------------------
_PRESETS: dict[str, dict[str, str]] = {
    "p2_8_r0": {"PHASE28_SAFE_DIVIDE": "0", "PHASE28_LOG_RATIO": "0", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r1": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "0", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r2": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "0"},
    "p2_8_r3": {"PHASE28_SAFE_DIVIDE": "1", "PHASE28_LOG_RATIO": "1", "PHASE28_MISSING_FLAG": "1"},
    "p3_1_base": {
        "PHASE28_SAFE_DIVIDE": "1",
        "PHASE28_LOG_RATIO": "1",
        "PHASE28_MISSING_FLAG": "1",
        "PHASE32_LOSS_L1": "0",
        "PHASE32_USE_WEIGHT": "0",
    },
    "p3_2_loss_only": {
        "PHASE28_SAFE_DIVIDE": "1",
        "PHASE28_LOG_RATIO": "1",
        "PHASE28_MISSING_FLAG": "1",
        "PHASE32_LOSS_L1": "1",
        "PHASE32_USE_WEIGHT": "0",
    },
    "p3_2_weight_only": {
        "PHASE28_SAFE_DIVIDE": "1",
        "PHASE28_LOG_RATIO": "1",
        "PHASE28_MISSING_FLAG": "1",
        "PHASE32_LOSS_L1": "0",
        "PHASE32_USE_WEIGHT": "1",
    },
    "p3_2_full": {
        "PHASE28_SAFE_DIVIDE": "1",
        "PHASE28_LOG_RATIO": "1",
        "PHASE28_MISSING_FLAG": "1",
        "PHASE32_LOSS_L1": "1",
        "PHASE32_USE_WEIGHT": "1",
    },
}


def _apply_preset(preset: str | None):
    if not preset:
        return
    preset = str(preset).strip()
    if preset not in _PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Allowed: {sorted(_PRESETS.keys())}")
    for k, v in _PRESETS[preset].items():
        os.environ[k] = str(v)


def _env_snapshot(prefixes: tuple[str, ...] = ("TRAIN_", "ROLL_", "PHASE", "CLIP_")) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in os.environ.items():
        if any(k.startswith(p) for p in prefixes):
            out[k] = v
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def _write_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldset = set()
    for r in rows:
        fieldset.update(r.keys())
    fieldnames = list(fieldset)
    preferred = ["time_key", "year", "month", "n_test", "sum_abs_y", "wmape", "smape", "mae", "rmse"]
    fieldnames = preferred + [f for f in fieldnames if f not in preferred]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    if len(xs) == 1:
        return float(xs[0])
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return float(xs[f])
    return float(xs[f] * (c - k) + xs[c] * (k - f))


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
    uniq = {f.resolve(): f for f in files}
    out = sorted(uniq.values(), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in out]


def _agg_wmape_by_month(rows: list[dict], key: str = "wmape") -> list[dict]:
    buckets: dict[int, list[dict]] = {}
    for r in rows:
        m = int(r.get("month", -1))
        if 1 <= m <= 12:
            buckets.setdefault(m, []).append(r)
    out: list[dict] = []
    for m in range(1, 13):
        rs = buckets.get(m, [])
        vals = [float(r.get(key, float("nan"))) for r in rs if r.get(key) is not None]
        vals = [v for v in vals if v == v]
        if not vals:
            continue
        out.append({
            "month": m,
            f"{key}_mean": float(mean(vals)),
            f"{key}_std": float((sum((v - mean(vals)) ** 2 for v in vals) / max(1, len(vals) - 1)) ** 0.5),
            f"{key}_p10": _percentile(vals, 0.10),
            f"{key}_p50": _percentile(vals, 0.50),
            f"{key}_p90": _percentile(vals, 0.90),
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

    def _wmean(vals: list[float], weights: list[float]) -> float:
        pairs = [(v, wi) for v, wi in zip(vals, weights) if v == v and wi is not None and wi > 0]
        if not pairs:
            return float("nan")
        s = sum(wi for _, wi in pairs)
        return float(sum(v * wi for v, wi in pairs) / s) if s > 0 else float("nan")

    peak = [r for r in rows if int(r.get("month", 0)) in (11, 12)]
    dec = [r for r in rows if int(r.get("month", 0)) == 12]

    return {
        "n_folds": int(len(rows)),
        "wmape_overall": _safe(wm),
        "wmape_weighted": _wmean(wm, w),
        "wmape_peak_11_12": _safe([float(r.get("wmape", float("nan"))) for r in peak]),
        "wmape_dec": _safe([float(r.get("wmape", float("nan"))) for r in dec]),
        "bad_rate_wmape_ge_40": float(sum(1 for v in wm if v == v and v >= 40.0) / max(1, sum(1 for v in wm if v == v))),
    }


def _selector_score(derived: dict[str, Any], tradeoff_lambda: float = 1.0) -> dict[str, Any]:
    wmape_weighted = float(derived.get("wmape_weighted", float("nan")))
    peak_std = float(((derived.get("wmape_peak_11_12", {}) or {}).get("std", float("nan"))))
    dec_mean = float(((derived.get("wmape_dec", {}) or {}).get("mean", float("nan"))))
    composite = wmape_weighted
    if peak_std == peak_std:
        composite += float(tradeoff_lambda) * peak_std
    else:
        composite = float("nan")
    return {
        "score": float(composite),
        "score_components": {
            "wmape_weighted": wmape_weighted,
            "peak_std_11_12": peak_std,
            "dec_mean": dec_mean,
        },
        "tradeoff_lambda": float(tradeoff_lambda),
    }


@dataclass
class SelectorConfig:
    train_mode: str = "conservative"
    roll_mode: str = "expanding"
    preset: str = "p3_2_full"
    random_iters: int = 30
    optuna_trials: int = 30
    tune_last_n_folds: int | None = 20
    tradeoff_lambda: float = 1.0
    fixed_n_estimators: int | None = None
    seed: int = 42
    out_dir: str = "artifacts/selector_run"
    registry_path: str | None = None
    policy: str = "wmape_composite"
    auto_activate: bool = True
    generate_quantile_bundle: bool = True
    skip_random: bool = False
    skip_optuna: bool = False
    model_version_prefix: str = "bundle"
    quantile_horizons: list[int] | None = None
    quantiles: list[float] | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "SelectorConfig":
        return cls(
            train_mode=args.train_mode,
            roll_mode=args.roll_mode,
            preset=args.preset,
            random_iters=int(args.random_iters),
            optuna_trials=int(args.optuna_trials),
            tune_last_n_folds=int(args.tune_last_n_folds) if args.tune_last_n_folds else None,
            tradeoff_lambda=float(args.tradeoff_lambda),
            fixed_n_estimators=int(args.fixed_n_estimators) if args.fixed_n_estimators is not None else None,
            seed=int(args.seed),
            out_dir=str(args.out_dir),
            registry_path=str(args.registry_path) if args.registry_path else None,
            policy=str(args.policy),
            auto_activate=bool(args.auto_activate),
            generate_quantile_bundle=not bool(args.no_quantile_bundle),
            skip_random=bool(args.skip_random),
            skip_optuna=bool(args.skip_optuna),
            model_version_prefix=str(args.model_version_prefix),
            quantile_horizons=[int(x) for x in str(args.quantile_horizons).split(",") if str(x).strip()] if args.quantile_horizons else [1, 2, 3, 4, 5, 6],
            quantiles=[float(x) for x in str(args.quantiles).split(",") if str(x).strip()] if args.quantiles else [0.05, 0.10, 0.30, 0.50, 0.70, 0.90, 0.95],
        )


@dataclass
class CandidateResult:
    tag: str
    source: str
    xgb_params: dict
    rolling_rows: list[dict]
    rolling_summary: dict
    derived_metrics: dict
    selector_score: dict

    def to_summary_row(self) -> dict:
        peak_std = float(((self.derived_metrics.get("wmape_peak_11_12", {}) or {}).get("std", float("nan"))))
        dec_mean = float(((self.derived_metrics.get("wmape_dec", {}) or {}).get("mean", float("nan"))))
        return {
            "tag": self.tag,
            "source": self.source,
            "score": float(self.selector_score.get("score", float("nan"))),
            "wmape_weighted": float(self.derived_metrics.get("wmape_weighted", float("nan"))),
            "peak_std_11_12": peak_std,
            "dec_mean": dec_mean,
            "n_folds": int(self.derived_metrics.get("n_folds", 0)),
            "xgb_params": json.dumps(self.xgb_params, ensure_ascii=False),
        }


def _import_model_module():
    import model  # noqa
    return model


def prepare_selector_data(dealers, runtime_config: "RuntimeConfig | dict | None" = None):
    model = _import_model_module()
    return model.prepare_training_data(dealers, config=runtime_config)


def evaluate_candidate(prep, xgb_params: dict, runtime_config=None, tag: str = "candidate") -> CandidateResult:
    model = _import_model_module()
    rows, summary = model.rolling_backtest_prepared(
        prep,
        xgb_params=xgb_params,
        last_n_folds=None if runtime_config is None else None,
        quiet=True,
        runtime_config=runtime_config,
    )
    derived = _derived_metrics(rows)
    score = _selector_score(derived, tradeoff_lambda=float(getattr(runtime_config, "get", lambda *a, **k: 1.0)("TRADE_OFF_WEIGHT", 1.0)) if runtime_config is not None else 1.0)
    return CandidateResult(
        tag=tag,
        source="manual",
        xgb_params=dict(xgb_params),
        rolling_rows=rows,
        rolling_summary=summary,
        derived_metrics=derived,
        selector_score=score,
    )


def run_baseline(prep, runtime_config=None, selector_config: SelectorConfig | None = None) -> CandidateResult:
    model = _import_model_module()
    cfg = runtime_config
    base_params = dict(model._get_default_xgb_params((selector_config.train_mode if selector_config else "conservative")))
    if selector_config and selector_config.fixed_n_estimators is not None:
        base_params["n_estimators"] = int(selector_config.fixed_n_estimators)
    rows, summary = model.rolling_backtest_prepared(
        prep,
        xgb_params=base_params,
        last_n_folds=selector_config.tune_last_n_folds if selector_config else None,
        quiet=True,
        runtime_config=cfg,
    )
    derived = _derived_metrics(rows)
    score = _selector_score(derived, tradeoff_lambda=float(selector_config.tradeoff_lambda if selector_config else 1.0))
    return CandidateResult(
        tag="baseline",
        source="baseline",
        xgb_params=base_params,
        rolling_rows=rows,
        rolling_summary=summary,
        derived_metrics=derived,
        selector_score=score,
    )


def run_random_search(prep, runtime_config=None, selector_config: SelectorConfig | None = None) -> list[CandidateResult]:
    if selector_config is None:
        raise ValueError("selector_config 不能为空。")
    model = _import_model_module()
    rng = np.random.default_rng(selector_config.seed + 17)
    base_params = dict(model._get_default_xgb_params(selector_config.train_mode))
    results: list[CandidateResult] = []

    def logu(a, b):
        return float(10 ** rng.uniform(np.log10(a), np.log10(b)))

    for i in range(int(selector_config.random_iters)):
        params = {
            "learning_rate": logu(0.01, 0.15),
            "max_depth": int(rng.integers(3, 9)),
            "min_child_weight": int(rng.integers(1, 16)),
            "subsample": float(rng.uniform(0.6, 1.0)),
            "colsample_bytree": float(rng.uniform(0.6, 1.0)),
            "reg_alpha": logu(1e-4, 5.0),
            "reg_lambda": logu(1e-2, 20.0),
            "gamma": float(rng.uniform(0.0, 3.0)),
        }
        if selector_config.fixed_n_estimators is None:
            params["n_estimators"] = int(rng.integers(300, 2001) // 50 * 50)
        else:
            params["n_estimators"] = int(selector_config.fixed_n_estimators)

        full_params = {**base_params, **params}
        rows, summary = model.rolling_backtest_prepared(
            prep,
            xgb_params=full_params,
            last_n_folds=selector_config.tune_last_n_folds,
            quiet=True,
            runtime_config=runtime_config,
        )
        derived = _derived_metrics(rows)
        score = _selector_score(derived, tradeoff_lambda=float(selector_config.tradeoff_lambda))
        results.append(
            CandidateResult(
                tag=f"random_{i:03d}",
                source="random",
                xgb_params=full_params,
                rolling_rows=rows,
                rolling_summary=summary,
                derived_metrics=derived,
                selector_score=score,
            )
        )
    results.sort(key=lambda x: (float(x.selector_score.get("score", float("inf"))), float(x.derived_metrics.get("wmape_weighted", float("inf")))))
    return results


def run_optuna_search(prep, runtime_config=None, selector_config: SelectorConfig | None = None) -> list[CandidateResult]:
    if selector_config is None:
        raise ValueError("selector_config 不能为空。")
    try:
        import optuna
    except Exception as e:
        print(f"[WARN] Optuna 不可用，跳过 Optuna 搜索：{e}")
        return []

    model = _import_model_module()
    base_params = dict(model._get_default_xgb_params(selector_config.train_mode))
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=selector_config.seed))

    cache: dict[int, CandidateResult] = {}

    def objective(trial):
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
        if selector_config.fixed_n_estimators is None:
            params["n_estimators"] = int(trial.suggest_int("n_estimators", 300, 2000, step=50))
        else:
            params["n_estimators"] = int(selector_config.fixed_n_estimators)

        full_params = {**base_params, **params}
        rows, summary = model.rolling_backtest_prepared(
            prep,
            xgb_params=full_params,
            last_n_folds=selector_config.tune_last_n_folds,
            quiet=True,
            runtime_config=runtime_config,
        )
        derived = _derived_metrics(rows)
        score = _selector_score(derived, tradeoff_lambda=float(selector_config.tradeoff_lambda))
        cand = CandidateResult(
            tag=f"optuna_{trial.number:03d}",
            source="optuna",
            xgb_params=full_params,
            rolling_rows=rows,
            rolling_summary=summary,
            derived_metrics=derived,
            selector_score=score,
        )
        cache[trial.number] = cand
        return float(score.get("score", float("inf")))

    study.optimize(objective, n_trials=int(selector_config.optuna_trials))
    trials = [cache[k] for k in sorted(cache.keys())]
    trials.sort(key=lambda x: (float(x.selector_score.get("score", float("inf"))), float(x.derived_metrics.get("wmape_weighted", float("inf")))))
    return trials


def select_recommended_candidate(results: list[CandidateResult], policy: str = "wmape_composite") -> CandidateResult:
    if not results:
        raise ValueError("没有可供选择的候选结果。")

    def sort_key(c: CandidateResult):
        score = float(c.selector_score.get("score", float("inf")))
        wmape = float(c.derived_metrics.get("wmape_weighted", float("inf")))
        peak_std = float(((c.derived_metrics.get("wmape_peak_11_12", {}) or {}).get("std", float("inf"))))
        dec_mean = float(((c.derived_metrics.get("wmape_dec", {}) or {}).get("mean", float("inf"))))
        return (score, wmape, peak_std, dec_mean)

    return sorted(results, key=sort_key)[0]


def _ensure_runtime_config(selector_config: SelectorConfig):
    """
    先沿用 preset 生成一份基础配置，再立刻转为显式 RuntimeConfig。
    这样服务层后续传递的是 config 对象，而不是反复改 env + reload。
    """
    _apply_preset(selector_config.preset)
    os.environ["TRAIN_MODE"] = selector_config.train_mode
    os.environ["ROLL_MODE"] = selector_config.roll_mode

    model = _import_model_module()
    runtime_config = model.RuntimeConfig.from_env()

    cfg_values = runtime_config.to_dict()
    if selector_config.fixed_n_estimators is not None:
        cfg_values["PHASE34_BASE_TREES"] = int(selector_config.fixed_n_estimators)
    cfg_values["TRADE_OFF_WEIGHT"] = float(selector_config.tradeoff_lambda)

    runtime_config = model.RuntimeConfig.from_dict(cfg_values)
    model.apply_runtime_config(runtime_config)
    return model, runtime_config


def _export_candidate_reports(candidate: CandidateResult, out_dir: Path):
    candidate_dir = out_dir / "candidates" / candidate.tag
    candidate_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(candidate_dir / "rolling_rows.csv", candidate.rolling_rows)
    _write_json(candidate_dir / "rolling_summary.json", candidate.rolling_summary)
    _write_json(candidate_dir / "derived_metrics.json", candidate.derived_metrics)
    _write_json(candidate_dir / "selector_score.json", candidate.selector_score)
    _write_csv(candidate_dir / "wmape_by_month_of_year.csv", _agg_wmape_by_month(candidate.rolling_rows, "wmape"))
    _write_json(candidate_dir / "xgb_params.json", candidate.xgb_params)


def _train_quantile_bundle_if_available(
    dealers,
    point_bundle,
    out_dir: Path,
    selector_config: SelectorConfig,
) -> tuple[str | None, dict]:
    """
    尽量兼容 quantile_forecast.py；若当前项目尚未按 bundle 接口改完，则跳过并在 manifest 里记录原因。
    """
    if not selector_config.generate_quantile_bundle:
        return None, {"status": "skipped", "reason": "generate_quantile_bundle=False"}

    try:
        import quantile_forecast  # noqa
    except Exception as e:
        return None, {"status": "skipped", "reason": f"quantile_forecast import failed: {e}"}

    qmod = importlib.import_module("quantile_forecast")

    try:
        bundle_path = out_dir / "bundles" / "quantile_bundle.joblib"

        if hasattr(qmod, "fit") and hasattr(qmod, "save_quantile_bundle"):
            q_bundle = qmod.fit(
                dealers,
                point_bundle=point_bundle,
                horizons=selector_config.quantile_horizons or [1, 2, 3, 4, 5, 6],
                quantiles=selector_config.quantiles or [0.05, 0.10, 0.30, 0.50, 0.70, 0.90, 0.95],
            )
            qmod.save_quantile_bundle(q_bundle, bundle_path)
            meta = q_bundle.to_metadata_dict() if hasattr(q_bundle, "to_metadata_dict") else {}
            return str(bundle_path), {
                "status": "ok",
                "mode": "fit+save_quantile_bundle",
                "bundle_meta": meta,
            }

        return None, {"status": "skipped", "reason": "quantile_forecast.py 尚未完成 point_bundle 接口化"}

    except Exception as e:
        return None, {"status": "failed", "reason": str(e)}


def build_and_export_bundles(
    dealers,
    runtime_config,
    recommended_candidate: CandidateResult,
    out_dir: Path,
    selector_config: SelectorConfig,
):
    model = _import_model_module()
    prep = model.prepare_training_data(dealers, config=runtime_config)
    point_bundle = model.train_point_model_from_prepared(
        prep,
        xgb_params_override=recommended_candidate.xgb_params,
        model_version=f"{selector_config.model_version_prefix}_{time.strftime('%Y%m%d_%H%M%S')}",
        quiet=False,
        runtime_config=runtime_config,
    )
    point_bundle.rolling_summary = dict(recommended_candidate.rolling_summary or {})

    point_bundle_path = out_dir / "bundles" / "point_bundle.joblib"
    model.save_point_bundle(point_bundle, point_bundle_path)

    quantile_bundle_path, quantile_info = _train_quantile_bundle_if_available(
        dealers=dealers,
        point_bundle=point_bundle,
        out_dir=out_dir,
        selector_config=selector_config,
    )

    manifest = {
        "model_version": point_bundle.model_version,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "point_bundle_path": str(point_bundle_path),
        "quantile_bundle_path": quantile_bundle_path,
        "feature_version": point_bundle.feature_version,
        "config_summary": runtime_config.to_dict() if hasattr(runtime_config, "to_dict") else dict(runtime_config or {}),
        "train_data_summary": {
            "n_samples": int(prep.X_raw.shape[0]),
            "feature_dim": int(prep.feature_dim),
            "feature_names": list(prep.feature_names or []),
            "train_years_months": point_bundle.train_years_months,
        },
        "search_policy_summary": {
            "policy": selector_config.policy,
            "tradeoff_lambda": selector_config.tradeoff_lambda,
            "random_iters": selector_config.random_iters,
            "optuna_trials": selector_config.optuna_trials,
            "fixed_n_estimators": selector_config.fixed_n_estimators,
        },
        "selected_candidate_summary": {
            "tag": recommended_candidate.tag,
            "source": recommended_candidate.source,
            "xgb_params": recommended_candidate.xgb_params,
            "selector_score": recommended_candidate.selector_score,
            "derived_metrics": recommended_candidate.derived_metrics,
        },
        "quantile_info": quantile_info,
    }
    _write_json(out_dir / "manifest.json", manifest)

    registry_path = Path(selector_config.registry_path).resolve() if selector_config.registry_path else (out_dir / "registry.json")
    registry = {
        "active_point_bundle": str(point_bundle_path),
        "active_quantile_bundle": quantile_bundle_path,
        "active_model_version": point_bundle.model_version,
        "activated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if selector_config.auto_activate:
        _write_json(registry_path, registry)

    return point_bundle, str(point_bundle_path), quantile_bundle_path, manifest, str(registry_path)


def run_selector_pipeline(dealers, selector_config: SelectorConfig) -> dict:
    out_dir = Path(selector_config.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    model, runtime_config = _ensure_runtime_config(selector_config)

    prep = prepare_selector_data(dealers, runtime_config=runtime_config)

    results: list[CandidateResult] = []

    baseline = run_baseline(prep, runtime_config=runtime_config, selector_config=selector_config)
    results.append(baseline)

    if not selector_config.skip_random:
        results.extend(run_random_search(prep, runtime_config=runtime_config, selector_config=selector_config))

    if not selector_config.skip_optuna:
        results.extend(run_optuna_search(prep, runtime_config=runtime_config, selector_config=selector_config))

    if not results:
        raise ValueError("没有产生任何候选结果。")

    for cand in results:
        _export_candidate_reports(cand, out_dir)

    recommended = select_recommended_candidate(results, policy=selector_config.policy)
    point_bundle, point_bundle_path, quantile_bundle_path, manifest, registry_path = build_and_export_bundles(
        dealers=dealers,
        runtime_config=runtime_config,
        recommended_candidate=recommended,
        out_dir=out_dir,
        selector_config=selector_config,
    )

    summary_rows = [r.to_summary_row() for r in results]
    pd.DataFrame(summary_rows).sort_values(["score", "wmape_weighted"]).to_csv(
        out_dir / "candidate_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    run_manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "selector_config": asdict(selector_config),
        "runtime_config": runtime_config.to_dict() if hasattr(runtime_config, "to_dict") else dict(runtime_config or {}),
        "env_raw": _env_snapshot(),
        "recommended_tag": recommended.tag,
        "recommended_source": recommended.source,
        "point_bundle_path": point_bundle_path,
        "quantile_bundle_path": quantile_bundle_path,
        "registry_path": registry_path,
    }
    _write_json(out_dir / "run_manifest.json", run_manifest)

    return {
        "recommended_candidate": recommended,
        "point_bundle": point_bundle,
        "point_bundle_path": point_bundle_path,
        "quantile_bundle_path": quantile_bundle_path,
        "manifest_path": str(out_dir / "manifest.json"),
        "registry_path": registry_path,
        "out_dir": str(out_dir),
    }


def _load_dealers_from_files(files: list[str]):
    from dealer_data_preprocessing import load_and_process_data
    dealers, dealer_codes = load_and_process_data(files)
    return dealers, dealer_codes


def run_selector_from_cli(args: argparse.Namespace) -> int:
    selector_config = SelectorConfig.from_args(args)

    files = list(args.files) if args.files else []
    if not files and args.data_dir:
        dd = Path(args.data_dir)
        if dd.exists() and dd.is_dir():
            files = [str(p) for p in dd.glob("*.xlsx")] + [str(p) for p in dd.glob("*.xls")] + [str(p) for p in dd.glob("*.xlsm")]
    if not files:
        files = _discover_excel_files(Path.cwd())

    if not files:
        print("[ERROR] 未发现 Excel 文件。请用 --files 或 --data_dir 指定。")
        return 2

    print("Excel files:")
    for f in files:
        print(" -", f)

    try:
        dealers, _ = _load_dealers_from_files(files)
    except Exception as e:
        print(f"[ERROR] 读取 dealers 失败: {e}")
        return 2

    try:
        result = run_selector_pipeline(dealers, selector_config)
    except Exception as e:
        print(f"[ERROR] selector pipeline failed: {e}")
        return 2

    print("\n[selector_service] done")
    print("out_dir           :", result["out_dir"])
    print("manifest_path     :", result["manifest_path"])
    print("registry_path     :", result["registry_path"])
    print("point_bundle_path :", result["point_bundle_path"])
    print("quantile_bundle   :", result["quantile_bundle_path"])
    return 0


def main():
    ap = argparse.ArgumentParser(description="Offline selector service: baseline / random / optuna -> point bundle / manifest / registry")
    ap.add_argument("--train_mode", default="conservative", choices=["conservative", "standard", "advanced"])
    ap.add_argument("--roll_mode", default="expanding", choices=["expanding", "sliding"])
    ap.add_argument("--preset", default="p3_2_full", choices=sorted(_PRESETS.keys()))
    ap.add_argument("--files", nargs="*", default=None)
    ap.add_argument("--data_dir", default=None)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--registry_path", default=None, help="active registry 输出路径；不填则落在 out_dir/registry.json")
    ap.add_argument("--policy", default="wmape_composite", choices=["wmape_composite"])
    ap.add_argument("--random_iters", type=int, default=30)
    ap.add_argument("--optuna_trials", type=int, default=30)
    ap.add_argument("--tune_last_n_folds", type=int, default=20)
    ap.add_argument("--tradeoff_lambda", type=float, default=1.0)
    ap.add_argument("--fixed_n_estimators", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip_random", action="store_true")
    ap.add_argument("--skip_optuna", action="store_true")
    ap.add_argument("--auto_activate", action="store_true")
    ap.add_argument("--model_version_prefix", default="bundle")
    ap.add_argument("--no_quantile_bundle", action="store_true")
    ap.add_argument("--quantile_horizons", default="1,2,3,4,5,6")
    ap.add_argument("--quantiles", default="0.05,0.10,0.30,0.50,0.70,0.90,0.95")
    args = ap.parse_args()
    raise SystemExit(run_selector_from_cli(args))


if __name__ == "__main__":
    main()
