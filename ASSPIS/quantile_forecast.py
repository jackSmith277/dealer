# quantile_forecast.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor

# 复用你现有的特征工程与 log1p 目标变换
from pathlib import Path
import json
import time

import joblib

from model import (
    build_features,
    _to_log_target,
    _from_log_target,
    _has_required_month_fields,
    _get_default_xgb_params,
    TRAIN_MODE,
    FeatureContext,
    PointModelBundle,
    RuntimeConfig,
    apply_runtime_config,
    build_single_dimension_overrides,
    load_point_bundle,
)

# -----------------------------
# Utilities (year-month aware)
# -----------------------------
def _is_ym_key(k) -> bool:
    return isinstance(k, tuple) and len(k) == 2 and isinstance(k[0], int) and isinstance(k[1], int)

def _infer_latest_year_from_maps(dealer_data, fallback: int = 2024) -> int:
    # 优先看 sales，其次看各特征
    candidates = []
    for f in (
        "sales", "potential_customers", "test_drives", "leads", "customer_flow",
        "defeat_rate", "success_rate", "success_response_time", "defeat_response_time",
        "policy", "gsev"
    ):
        mp = getattr(dealer_data, f, {}) or {}
        for k in mp.keys():
            if _is_ym_key(k):
                candidates.append(k[0])
    return max(candidates) if candidates else fallback

def _months_for_year(mp: dict, year: int) -> set[int]:
    if not mp:
        return set()
    # 新结构：key=(year,month)
    if any(_is_ym_key(k) for k in mp.keys()):
        return {int(m) for (y, m) in mp.keys() if int(y) == int(year)}
    # 旧结构：key=month
    return {int(m) for m in mp.keys() if isinstance(m, (int, np.integer))}

def _map_at(mp: dict, year: int, month: int):
    if mp is None:
        return None
    if (int(year), int(month)) in mp:
        return mp.get((int(year), int(month)))
    return mp.get(int(month))

def _safe_quantile(a: np.ndarray, q: float) -> float:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return 0.0
    return float(np.quantile(a, q))

def _clamp_nonneg(x: np.ndarray) -> np.ndarray:
    return np.maximum(np.asarray(x, dtype=float), 0.0)

def _base_sales_from_map(sales_map: dict, year: int, month: int) -> Optional[float]:
    """
    尽量取 (year,month) 对应销量；若缺失，退一步取同一年 <=month 的最近一个销量。
    兼容旧 month-key。
    """
    v = _map_at(sales_map, year, month)
    if v is not None:
        return float(v)

    # 找同一年更早月份
    months = sorted(_months_for_year(sales_map, year))
    prev = [m for m in months if int(m) < int(month)]
    if prev:
        vv = _map_at(sales_map, year, max(prev))
        return float(vv) if vv is not None else None
    return None

def _latest_month_with_features(dealer_data, year: int) -> Optional[int]:
    """找该 dealer 在指定 year 下最晚一个“当月 10 个原子字段”齐全的月份，用于 base_month 默认值。"""
    maps = [
        getattr(dealer_data, "potential_customers", {}),
        getattr(dealer_data, "test_drives", {}),
        getattr(dealer_data, "leads", {}),
        getattr(dealer_data, "customer_flow", {}),
        getattr(dealer_data, "defeat_rate", {}),
        getattr(dealer_data, "success_rate", {}),
        getattr(dealer_data, "success_response_time", {}),
        getattr(dealer_data, "defeat_response_time", {}),
        getattr(dealer_data, "policy", {}),
        getattr(dealer_data, "gsev", {}),
    ]
    common = _months_for_year(maps[0], year)
    for mp in maps[1:]:
        common &= _months_for_year(mp, year)
    return max(common) if common else None

# -----------------------------
# Fit helper
# -----------------------------
def _fit_one_quantile_model(X: np.ndarray, y: np.ndarray, tau: float, xgb_params: Dict[str, Any]):
    params = dict(xgb_params)

    params["objective"] = "reg:quantileerror"
    params["quantile_alpha"] = float(tau)

    xgb_model = xgb.XGBRegressor(**params)
    try:
        xgb_model.fit(X, y)
        return xgb_model, "xgb_reg:quantileerror"
    except Exception:
        gbr = GradientBoostingRegressor(
            loss="quantile",
            alpha=float(tau),
            random_state=42,
        )
        gbr.fit(X, y)
        return gbr, "sk_gbr_quantile"

# -----------------------------
# Forecaster (Architecture A)
# -----------------------------
@dataclass
class QuantileForecaster:
    default_quantiles: List[float] = field(default_factory=lambda: [0.1, 0.5, 0.9])

    calib_alpha: float = 0.2
    calib_target_month_window: int = 4
    min_calib_samples: int = 30
    min_train_samples: int = 10

    # 修正：限制 ratio_prev 仅在 h=2 使用，h>=3 回归 direct_log1p
    direct_log1p_horizons: List[int] = field(default_factory=lambda: [1] + list(range(3, 13)))
    direct_raw_horizons: List[int] = field(default_factory=list)
    ratio_base_horizons: List[int] = field(default_factory=list)
    ratio_prev_horizons: List[int] = field(default_factory=lambda: [2])

    ratio_eps: float = 1e-6
    ratio_clip_min: float = 0.0
    ratio_clip_max: float = 3.0  # 修正：大幅收紧单期最大增长倍数

    min_samples_per_horizon: int = 20
    random_state: int = 42
    debug: bool = False

    xgb_params_overrides: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    models: Dict[int, Dict[float, Any]] = field(default_factory=dict)
    model_kind: Dict[int, Dict[float, str]] = field(default_factory=dict)

    cqr_qhat: Dict[int, float] = field(default_factory=dict)

    trained_max_target_month: int = 0
    trained_year: int = 2024
    horizon_train_sizes: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    is_fitted: bool = False

    # -----------------------------
    # Strategy helpers
    # -----------------------------
    def _strategy(self, h: int) -> str:
        h = int(h)
        if h in set(self.ratio_prev_horizons):
            return "ratio_prev"
        if h in set(self.ratio_base_horizons):
            return "ratio_base"
        if h in set(self.direct_log1p_horizons):
            return "direct_log1p"
        if h in set(self.direct_raw_horizons):
            return "direct_raw"
        return "direct_log1p"

    def _to_model_target(self, y_raw: np.ndarray, h: int, denom: Optional[np.ndarray] = None) -> np.ndarray:
        st = self._strategy(h)
        if st in ("ratio_base", "ratio_prev"):
            if denom is None:
                raise ValueError("ratio 策略需要 denom。")
            denom = np.maximum(np.asarray(denom, dtype=float), self.ratio_eps)
            ratio = np.asarray(y_raw, dtype=float) / denom
            ratio = np.clip(ratio, self.ratio_clip_min, self.ratio_clip_max)
            return _to_log_target(ratio)
        if st == "direct_log1p":
            return _to_log_target(y_raw)
        return np.asarray(y_raw, dtype=float)

    def _from_model_pred(self, y_pred_model: np.ndarray, h: int, denom: Optional[np.ndarray] = None) -> np.ndarray:
        st = self._strategy(h)
        if st in ("ratio_base", "ratio_prev"):
            if denom is None:
                raise ValueError("ratio 策略需要 denom。")
            ratio_hat = _from_log_target(y_pred_model)
            ratio_hat = np.clip(np.asarray(ratio_hat, dtype=float), self.ratio_clip_min, self.ratio_clip_max)
            return np.asarray(ratio_hat, dtype=float) * np.asarray(denom, dtype=float)
        if st == "direct_log1p":
            return _from_log_target(y_pred_model)
        return np.asarray(y_pred_model, dtype=float)

    def _calib_window_for_horizon(self, h: int) -> int:
        h = int(h)
        if h >= 2:
            return max(int(self.calib_target_month_window), 4)
        return max(2, int(self.calib_target_month_window) - 1)

    def _min_calib_samples_for_horizon(self, h: int) -> int:
        h = int(h)
        if h >= 2:
            return max(int(self.min_calib_samples), 30)
        return max(10, min(int(self.min_calib_samples), 20))

    def _xgb_params_for_horizon(self, h: int) -> Dict[str, Any]:
        params = dict(_get_default_xgb_params(TRAIN_MODE))
        h = int(h)

        if h >= 2:
            params["min_child_weight"] = max(float(params.get("min_child_weight", 1.0)), 5.0)
            params["subsample"] = min(float(params.get("subsample", 1.0)), 0.8)
            params["colsample_bytree"] = min(float(params.get("colsample_bytree", 1.0)), 0.8)
            params["reg_lambda"] = max(float(params.get("reg_lambda", 1.0)), 5.0)

        if h >= 3:
            params["min_child_weight"] = max(float(params.get("min_child_weight", 5.0)), 10.0)
            params["subsample"] = min(float(params.get("subsample", 0.8)), 0.75)
            params["colsample_bytree"] = min(float(params.get("colsample_bytree", 0.8)), 0.75)
            params["reg_lambda"] = max(float(params.get("reg_lambda", 5.0)), 10.0)

        if int(h) in self.xgb_params_overrides:
            params.update(self.xgb_params_overrides[int(h)])
        return params

    def _split_train_calib(self, target_months: np.ndarray, h: int) -> Tuple[np.ndarray, np.ndarray]:
        target_months = np.asarray(target_months, dtype=int)
        n = int(len(target_months))
        if n <= 1:
            return np.ones(n, dtype=bool), np.zeros(n, dtype=bool)

        window = int(self._calib_window_for_horizon(h))
        min_calib = int(self._min_calib_samples_for_horizon(h))

        max_tm = int(np.max(target_months))
        calib_tms = set(range(max(1, max_tm - window + 1), max_tm + 1))
        calib_mask = np.array([int(tm) in calib_tms for tm in target_months], dtype=bool)
        train_mask = ~calib_mask

        if calib_mask.sum() >= min_calib and train_mask.sum() >= self.min_train_samples:
            return train_mask, calib_mask

        rng = np.random.RandomState(self.random_state)
        idx = np.arange(n)
        rng.shuffle(idx)

        desired_calib = max(min_calib, int(0.2 * n))
        desired_calib = min(desired_calib, n - self.min_train_samples)
        if desired_calib <= 0:
            return np.ones(n, dtype=bool), np.zeros(n, dtype=bool)

        calib_idx = idx[:desired_calib]
        calib_mask = np.zeros(n, dtype=bool)
        calib_mask[calib_idx] = True
        train_mask = ~calib_mask

        if train_mask.sum() < self.min_train_samples:
            desired_calib = max(1, n - self.min_train_samples)
            calib_idx = idx[:desired_calib]
            calib_mask = np.zeros(n, dtype=bool)
            calib_mask[calib_idx] = True
            train_mask = ~calib_mask

        return train_mask, calib_mask

    # -----------------------------
    # Fit
    # -----------------------------
    def fit(
        self,
        dealers: Dict[str, Any],
        scaler,
        horizons: Optional[List[int]] = None,
        quantiles: Optional[List[float]] = None,
        calib_alpha: Optional[float] = None,
        train_upto_month: Optional[int] = None,
        train_year: Optional[int] = None,
        feature_context: Optional[FeatureContext] = None,
        runtime_config: Optional[dict | RuntimeConfig] = None,
    ) -> "QuantileForecaster":
        if runtime_config is None and feature_context is not None:
            runtime_config = feature_context.config
        if runtime_config is not None:
            apply_runtime_config(runtime_config)

        if calib_alpha is not None:
            self.calib_alpha = float(calib_alpha)

        if quantiles is None:
            quantiles = list(self.default_quantiles)

        q_low = self.calib_alpha / 2.0
        q_high = 1.0 - self.calib_alpha / 2.0
        quantiles = sorted(set([float(q) for q in quantiles] + [q_low, q_high, 0.05, 0.95]))

        # 选择训练年份（默认用数据里最大的 year）
        if train_year is None:
            ys = []
            for _, d in dealers.items():
                ys.append(_infer_latest_year_from_maps(d, fallback=2024))
            train_year = max(ys) if ys else 2024
        train_year = int(train_year)
        self.trained_year = train_year

        # 计算该 year 的 max_target_month（只看该年 sales）
        max_target_month = 0
        for _, d in dealers.items():
            sales_map = getattr(d, "sales", {}) or {}
            months = _months_for_year(sales_map, train_year)
            if months:
                max_target_month = max(max_target_month, max(months))

        self.trained_max_target_month = int(max_target_month)

        if train_upto_month is not None:
            max_target_month = min(int(max_target_month), int(train_upto_month))
            self.trained_max_target_month = int(max_target_month)

        if max_target_month < 2:
            raise ValueError(f"销量月份太少（year={train_year}），无法训练分位数预测模型。")

        max_h_trainable = max_target_month - 1
        if horizons is None:
            horizons = list(range(1, max_h_trainable + 1))
        else:
            horizons = [int(h) for h in horizons if 1 <= int(h) <= max_h_trainable]

        self.models.clear()
        self.model_kind.clear()
        self.cqr_qhat.clear()
        self.horizon_train_sizes.clear()

        for h in horizons:
            st = self._strategy(h)

            X_list: List[List[float]] = []
            y_list: List[float] = []
            denom_list: List[float] = []
            target_months: List[int] = []

            for _, dealer_data in dealers.items():
                sales_map = getattr(dealer_data, "sales", {}) or {}

                for m in range(1, max_target_month - h + 1):
                    # ✅ 这里必须传 year（否则你改过 model 签名就会报错）
                    if not _has_required_month_fields(dealer_data, train_year, m, include_target=False):
                        continue

                    tm = m + h
                    y_tm = _map_at(sales_map, train_year, tm)
                    if y_tm is None:
                        continue

                    denom = 0.0
                    if st == "ratio_base":
                        denom_val = _base_sales_from_map(sales_map, train_year, m)
                        if denom_val is None:
                            continue
                        denom = float(denom_val)

                    elif st == "ratio_prev":
                        y_prev = _map_at(sales_map, train_year, tm - 1)
                        if y_prev is None:
                            continue
                        denom = float(y_prev)

                    X_list.append(build_features(dealer_data, train_year, m, feature_context=feature_context, config=runtime_config))
                    y_list.append(float(y_tm))
                    denom_list.append(float(denom))
                    target_months.append(int(tm))

            n_total = len(y_list)
            if n_total < self.min_samples_per_horizon:
                if self.debug:
                    print(f"[QuantileForecaster] horizon={h} skipped, n_total={n_total}")
                continue

            X_raw = np.asarray(X_list, dtype=float)
            y_raw = np.asarray(y_list, dtype=float)
            denom_arr = np.asarray(denom_list, dtype=float)
            target_months_arr = np.asarray(target_months, dtype=int)

            train_mask, calib_mask = self._split_train_calib(target_months_arr, h)
            if train_mask.sum() == 0:
                if self.debug:
                    print(
                        f"[QuantileForecaster] horizon={h} invalid split: "
                        f"n_train={train_mask.sum()} n_calib={calib_mask.sum()}"
                    )
                continue

            do_cqr = bool(calib_mask.sum() > 0)

            X_train = scaler.transform(X_raw[train_mask])
            y_train = self._to_model_target(
                y_raw[train_mask],
                h,
                denom=denom_arr[train_mask] if st.startswith("ratio") else None,
            )

            self.models[h] = {}
            self.model_kind[h] = {}
            for tau in quantiles:
                mdl, kind = _fit_one_quantile_model(
                    X_train, y_train, tau=float(tau), xgb_params=self._xgb_params_for_horizon(h)
                )
                self.models[h][float(tau)] = mdl
                self.model_kind[h][float(tau)] = kind

            if do_cqr:
                # 【新增修复】：在这里生成校准集数据，解决 X_cal, y_cal, denom_cal 未定义报错
                X_cal = scaler.transform(X_raw[calib_mask])
                y_cal = y_raw[calib_mask]
                denom_cal = denom_arr[calib_mask] if st.startswith("ratio") else None

                # 寻找中位数的预测值，抛弃边缘分位数
                tau_median = 0.5 if 0.5 in self.models[h] else quantiles[len(quantiles) // 2]
                m_median = self.models[h][float(tau_median)]
                pred_median_raw = self._from_model_pred(m_median.predict(X_cal), h, denom=denom_cal)
                pred_median_raw = _clamp_nonneg(pred_median_raw)

                denom_cal_safe = np.maximum(y_cal, 1.0)

                # 【核心重构：基于点预测的绝对百分比误差 APE】
                # 计算预测中位数与真实值的相对偏差比例
                r_ape = np.abs(pred_median_raw - y_cal) / denom_cal_safe

                # 提取能覆盖 (1-alpha) 概率的百分比误差（例如 80% 置信度下的最大误差率）
                qhat_pct = _safe_quantile(r_ape, 1.0 - self.calib_alpha)

                # 强限制：行业内单店优秀 MAPE 在 15-25% 之间。
                # 即使模型极度不准，也不允许单侧区间偏差超过 45% (0.45)，防止极端脏数据带崩全局
                self.cqr_qhat[h] = float(min(max(qhat_pct, 0.05), 0.45))
            else:
                self.cqr_qhat[h] = 0.0

            self.horizon_train_sizes[h] = {
                "n_total": int(n_total),
                "n_train": int(train_mask.sum()),
                "n_calib": int(calib_mask.sum()),
                "strategy": st,
                "qhat": float(self.cqr_qhat[h]),
                "train_year": int(train_year),
            }

        self.is_fitted = True
        return self

    def supported_horizons(self) -> List[int]:
        return sorted(self.models.keys())

    # -----------------------------
    # Predict
    # -----------------------------
    def predict(
            self,
            dealer_data,
            scaler,
            base_year: int,
            base_month: int,
            horizons: List[int],
            quantiles: Optional[List[float]] = None,
            overrides: Optional[dict] = None,
            feature_context: Optional[FeatureContext] = None,
            runtime_config: Optional[dict | RuntimeConfig] = None,
            calib_alpha: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.is_fitted:
            raise RuntimeError("QuantileForecaster 未训练。")

        base_year = int(base_year)
        base_month = int(base_month)

        if runtime_config is None and feature_context is not None:
            runtime_config = feature_context.config
        if runtime_config is not None:
            apply_runtime_config(runtime_config)

        if quantiles is None:
            quantiles = list(self.default_quantiles)

        effective_calib_alpha = calib_alpha if calib_alpha is not None else self.calib_alpha

        q_low = effective_calib_alpha / 2.0
        q_high = 1.0 - effective_calib_alpha / 2.0
        all_q_candidates = sorted(set([float(q) for q in quantiles] + [q_low, q_high, 0.05, 0.95]))
        trained_q = self.models.get(horizons[0] if horizons else 1, {}).keys()
        if trained_q:
            all_q = sorted([q for q in all_q_candidates if q in trained_q])
        else:
            all_q = all_q_candidates
        # 补充常用的 90% 置信区间边界 (q05, q95)，方便前端动态切换
        all_q_sorted = np.array(all_q, dtype=float)
        q_keys_sorted = [str(float(q)) for q in all_q_sorted]

        feats = build_features(dealer_data, base_year, base_month, overrides=overrides, feature_context=feature_context, config=runtime_config)
        X = np.asarray([feats], dtype=float)
        Xs = scaler.transform(X)

        interval_pct = int((1.0 - effective_calib_alpha) * 100)
        calibrated_interval_key = f"calibrated_interval_{interval_pct}"

        out = {
            "base_year": int(base_year),
            "base_month": int(base_month),
            "horizons_requested": [int(h) for h in horizons],
            "horizons_supported": [],
            "unsupported_horizons": [],
            "years": [],
            "months": [],
            "point": [],
            "quantiles": {str(float(q)): [] for q in all_q_sorted},
            calibrated_interval_key: {"lower": [], "upper": []},
            "meta": {
                "strategy_by_horizon": {},
                "cqr_alpha": float(effective_calib_alpha),
                "trained_year": int(self.trained_year),
                "trained_max_target_month": int(self.trained_max_target_month),
                "interval_name": calibrated_interval_key
            },
        }

        i_low = int(np.where(np.isclose(all_q_sorted, q_low))[0][0])
        i_high = int(np.where(np.isclose(all_q_sorted, q_high))[0][0])
        i_median = int(np.where(np.isclose(all_q_sorted, 0.5))[0][0]) if 0.5 in all_q_sorted else len(all_q_sorted) // 2

        base_sales = None
        sales_map = getattr(dealer_data, "sales", {}) or {}
        base_sales = _base_sales_from_map(sales_map, base_year, base_month)

        requested_h = sorted({int(h) for h in horizons})
        requested_set = set(requested_h)

        compute_set = set(requested_set)
        for hh in list(requested_set):
            if self._strategy(hh) == "ratio_prev":
                compute_set.update(range(1, hh))
        compute_h = sorted(compute_set)

        prev_pred_by_q: Optional[np.ndarray] = None
        prev_h: Optional[int] = None

        for h in compute_h:
            if h not in self.models:
                if h in requested_set:
                    out["unsupported_horizons"].append(h)
                prev_pred_by_q = None
                prev_h = None
                continue

            st = self._strategy(h)
            out["meta"]["strategy_by_horizon"][str(h)] = st

            preds_raw = np.zeros(len(all_q_sorted), dtype=float)

            for i, q in enumerate(all_q_sorted):
                mdl = self.models[h][float(q)]
                yhat_model = mdl.predict(Xs)

                denom_vec = None
                if st == "ratio_base":
                    denom_val = float(base_sales) if base_sales is not None else 0.0
                    denom_vec = np.array([max(denom_val, self.ratio_eps)], dtype=float)

                elif st == "ratio_prev":
                    if prev_pred_by_q is not None and prev_h is not None and (h - prev_h) == 1:
                        # 修正：所有分位数统一使用中位数预测作为分母，降维打击尾部爆炸
                        denom_val = float(prev_pred_by_q[i_median])
                    else:
                        denom_val = float(base_sales) if base_sales is not None else 0.0
                    denom_vec = np.array([max(denom_val, self.ratio_eps)], dtype=float)

                yhat_raw = self._from_model_pred(yhat_model, h, denom=denom_vec)
                preds_raw[i] = float(yhat_raw[0])

            # === 上下文定位：在 predict 函数的 for h in compute_h: 循环中 ===
            preds_raw = _clamp_nonneg(preds_raw)
            # 保证分位数单调不降（防止分位数交叉错乱）
            preds_mono = np.maximum.accumulate(preds_raw)

            if h in requested_set:
                out["horizons_supported"].append(h)

                # 解决跨年月份溢出 Bug
                total_months = int(base_year) * 12 + int(base_month) - 1 + int(h)
                pred_year = total_months // 12
                pred_month = total_months % 12 + 1
                out["years"].append(pred_year)
                out["months"].append(pred_month)

                for q_key, v in zip(q_keys_sorted, preds_mono.tolist()):
                    out["quantiles"][q_key].append(float(v))

                if "0.5" in out["quantiles"]:
                    out["point"].append(out["quantiles"]["0.5"][-1])
                else:
                    out["point"].append(float(preds_mono[len(preds_mono) // 2]))

                # 【清理并重构区间计算逻辑，避免多余代码】
                # 完全抛弃 XGBoost 边缘分位数发散结果，以中位数为绝对锚点
                median_val = float(preds_mono[i_median])

                # 提取校准集中学习到的经验百分比误差
                qhat_pct = float(self.cqr_qhat.get(h, 0.25))  # 若无则默认给 25% 的容错率

                # 【动态时间惩罚系数】
                # 摒弃原有的倒数缩减，采用符合物理常识的放大：预测越远，不确定性越大
                # h=1(1.0), h=2(1.1), h=3(1.2) ...
                scale = 1.0 + 0.1 * (h - 1)

                # 计算绝对台数容错带
                margin = median_val * qhat_pct * scale

                # 直接基于中位数生成对称区间
                lower_bound = median_val - margin
                upper_bound = median_val + margin

                # 【业务常识物理限制兜底】
                # 下限物理限制：极其悲观的情况下，单月销量也不应低于预测中位数的 40% (保障基本盘)
                # 除非预测值本来就很低(小于5.0)，这时候允许下限到0
                lower_cap = median_val * 0.4
                lower_bound = max(lower_bound, lower_cap) if median_val > 5.0 else max(lower_bound, 0.0)

                # 上限物理限制：不超过预测中位数的 1.8 倍
                upper_cap_median = median_val * 1.8
                upper_bound = min(upper_bound, upper_cap_median)

                out[calibrated_interval_key]["lower"].append(lower_bound)
                out[calibrated_interval_key]["upper"].append(upper_bound)

            prev_pred_by_q = preds_mono.copy()
            prev_h = h

        return out
        # === 紧接着直接 return out，上面的替换结束 ===

    def default_base_month(self, dealer_data, year: Optional[int] = None) -> Optional[int]:
        if year is None:
            year = _infer_latest_year_from_maps(dealer_data, fallback=2024)
        return _latest_month_with_features(dealer_data, int(year))


@dataclass
class QuantileModelBundle:
    forecaster: QuantileForecaster
    scaler: Any
    feature_context: FeatureContext
    point_model_version: Optional[str]
    model_version: str
    trained_at: str
    feature_version: str
    feature_names: List[str]
    horizons_supported: List[int]
    quantiles: List[float]
    calib_alpha: float
    trained_year: int
    trained_max_target_month: int
    horizon_train_sizes: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    config_summary: Dict[str, Any] = field(default_factory=dict)

    def to_metadata_dict(self) -> Dict[str, Any]:
        return {
            "model_version": str(self.model_version),
            "point_model_version": self.point_model_version,
            "trained_at": str(self.trained_at),
            "feature_version": str(self.feature_version),
            "feature_names": list(self.feature_names or []),
            "horizons_supported": [int(h) for h in (self.horizons_supported or [])],
            "quantiles": [float(q) for q in (self.quantiles or [])],
            "calib_alpha": float(self.calib_alpha),
            "trained_year": int(self.trained_year),
            "trained_max_target_month": int(self.trained_max_target_month),
            "horizon_train_sizes": {
                str(int(k)): dict(v or {}) for k, v in (self.horizon_train_sizes or {}).items()
            },
            "config_summary": dict(self.config_summary or {}),
        }


def _safe_json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def _resolve_point_bundle(point_bundle: PointModelBundle | str | Path) -> PointModelBundle:
    if isinstance(point_bundle, PointModelBundle):
        return point_bundle
    return load_point_bundle(point_bundle)


def fit(
    dealers: Dict[str, Any],
    *,
    point_bundle: PointModelBundle | str | Path,
    horizons: Optional[List[int]] = None,
    quantiles: Optional[List[float]] = None,
    calib_alpha: float = 0.2,
    train_year: Optional[int] = None,
    train_upto_month: Optional[int] = None,
    debug: bool = False,
    model_version: Optional[str] = None,
) -> QuantileModelBundle:
    """
    selector_service.py 对接入口：
    - 复用 point bundle 的 scaler / feature_context / runtime_config
    - 训练 quantile forecaster
    - 返回可序列化的 QuantileModelBundle
    """
    pb = _resolve_point_bundle(point_bundle)
    feature_context = getattr(pb, "feature_context", None)
    if feature_context is None:
        cfg = pb.config if isinstance(pb.config, RuntimeConfig) else RuntimeConfig.from_dict(pb.config)
        feature_context = FeatureContext(
            global_medians=dict(pb.global_medians or {}),
            config=cfg,
            feature_names=list(pb.feature_names or []),
            feature_version=str(getattr(pb, "feature_version", "point_features_v2")),
        )

    runtime_config = feature_context.config
    apply_runtime_config(runtime_config)

    qf = QuantileForecaster(
        default_quantiles=list(quantiles or [0.05, 0.10, 0.30, 0.50, 0.70, 0.90, 0.95]),
        calib_alpha=float(calib_alpha),
        debug=bool(debug),
    )
    qf.fit(
        dealers=dealers,
        scaler=pb.scaler,
        horizons=horizons,
        quantiles=quantiles,
        calib_alpha=calib_alpha,
        train_upto_month=train_upto_month,
        train_year=train_year,
        feature_context=feature_context,
        runtime_config=runtime_config,
    )

    return QuantileModelBundle(
        forecaster=qf,
        scaler=pb.scaler,
        feature_context=feature_context,
        point_model_version=getattr(pb, "model_version", None),
        model_version=model_version or f"quantile_{time.strftime('%Y%m%d_%H%M%S')}",
        trained_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        feature_version=str(getattr(feature_context, "feature_version", "point_features_v2")),
        feature_names=list(getattr(feature_context, "feature_names", []) or []),
        horizons_supported=qf.supported_horizons(),
        quantiles=sorted(set([float(q) for q in (quantiles or qf.default_quantiles)])),
        calib_alpha=float(qf.calib_alpha),
        trained_year=int(qf.trained_year),
        trained_max_target_month=int(qf.trained_max_target_month),
        horizon_train_sizes={int(k): dict(v or {}) for k, v in qf.horizon_train_sizes.items()},
        config_summary=runtime_config.to_dict() if hasattr(runtime_config, "to_dict") else dict(runtime_config or {}),
    )


def save_quantile_bundle(bundle: QuantileModelBundle, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    meta_path.write_text(
        json.dumps(bundle.to_metadata_dict(), ensure_ascii=False, indent=2, default=_safe_json_default),
        encoding="utf-8",
    )
    return path


def load_quantile_bundle(path: str | Path) -> QuantileModelBundle:
    obj = joblib.load(Path(path))
    if isinstance(obj, QuantileModelBundle):
        return obj
    if isinstance(obj, dict):
        fc = obj.get("feature_context")
        if isinstance(fc, dict):
            cfg_raw = fc.get("config")
            cfg = cfg_raw if isinstance(cfg_raw, RuntimeConfig) else RuntimeConfig.from_dict(cfg_raw)
            fc = FeatureContext(
                global_medians=dict(fc.get("global_medians", {}) or {}),
                config=cfg,
                feature_names=list(fc.get("feature_names", []) or []),
                feature_version=str(fc.get("feature_version", "point_features_v2")),
            )
        return QuantileModelBundle(
            forecaster=obj["forecaster"],
            scaler=obj["scaler"],
            feature_context=fc,
            point_model_version=obj.get("point_model_version"),
            model_version=str(obj.get("model_version", Path(path).stem)),
            trained_at=str(obj.get("trained_at", "")),
            feature_version=str(obj.get("feature_version", "point_features_v2")),
            feature_names=list(obj.get("feature_names", []) or []),
            horizons_supported=[int(h) for h in (obj.get("horizons_supported", []) or [])],
            quantiles=[float(q) for q in (obj.get("quantiles", []) or [])],
            calib_alpha=float(obj.get("calib_alpha", 0.2)),
            trained_year=int(obj.get("trained_year", 2024)),
            trained_max_target_month=int(obj.get("trained_max_target_month", 0)),
            horizon_train_sizes={int(k): dict(v or {}) for k, v in (obj.get("horizon_train_sizes", {}) or {}).items()},
            config_summary=dict(obj.get("config_summary", {}) or {}),
        )
    raise TypeError(f"无法识别的 quantile bundle 类型: {type(obj)!r}")


def predict_with_bundle(
    bundle_or_path: QuantileModelBundle | str | Path,
    dealer_data,
    *,
    base_year: int,
    base_month: int,
    horizons: List[int],
    quantiles: Optional[List[float]] = None,
    overrides: Optional[dict] = None,
    calib_alpha: Optional[float] = None,
) -> Dict[str, Any]:
    bundle = bundle_or_path if isinstance(bundle_or_path, QuantileModelBundle) else load_quantile_bundle(bundle_or_path)
    return bundle.forecaster.predict(
        dealer_data=dealer_data,
        scaler=bundle.scaler,
        base_year=int(base_year),
        base_month=int(base_month),
        horizons=[int(h) for h in horizons],
        quantiles=quantiles,
        overrides=overrides,
        feature_context=bundle.feature_context,
        runtime_config=bundle.feature_context.config,
        calib_alpha=calib_alpha,
    )


def predict_for_dealer(
    bundle_or_path: QuantileModelBundle | str | Path,
    dealers: Dict[str, Any],
    dealer_code: str,
    *,
    base_year: int,
    base_month: int,
    horizons: List[int],
    quantiles: Optional[List[float]] = None,
    overrides: Optional[dict] = None,
    calib_alpha: Optional[float] = None,
) -> Dict[str, Any]:
    dealer_data = dealers.get(dealer_code)
    if dealer_data is None:
        raise KeyError(f"未找到经销商: {dealer_code}")
    out = predict_with_bundle(
        bundle_or_path,
        dealer_data,
        base_year=base_year,
        base_month=base_month,
        horizons=horizons,
        quantiles=quantiles,
        overrides=overrides,
        calib_alpha=calib_alpha,
    )
    out["dealer_code"] = str(dealer_code)
    bundle = bundle_or_path if isinstance(bundle_or_path, QuantileModelBundle) else load_quantile_bundle(bundle_or_path)
    out["model_version"] = bundle.model_version
    out["point_model_version"] = bundle.point_model_version
    out["feature_version"] = bundle.feature_version
    return out


def predict_t1_what_if_quantiles(
    bundle_or_path: QuantileModelBundle | str | Path,
    dealers: Dict[str, Any],
    dealer_code: str,
    *,
    base_year: int,
    base_month: int,
    dimension: str,
    change_percentage: float,
    quantiles: Optional[List[float]] = None,
) -> Dict[str, Any]:
    bundle = bundle_or_path if isinstance(bundle_or_path, QuantileModelBundle) else load_quantile_bundle(bundle_or_path)
    dealer_data = dealers.get(dealer_code)
    if dealer_data is None:
        raise KeyError(f"未找到经销商: {dealer_code}")

    overrides = build_single_dimension_overrides(
        dealer_data,
        dimension=dimension,
        change_percentage=float(change_percentage),
        year=int(base_year),
        month=int(base_month),
        feature_context=bundle.feature_context,
        config=bundle.feature_context.config,
    )
    out = predict_with_bundle(
        bundle,
        dealer_data,
        base_year=base_year,
        base_month=base_month,
        horizons=[1],
        quantiles=quantiles,
        overrides=overrides,
    )
    out["dealer_code"] = str(dealer_code)
    out["dimension"] = str(dimension)
    out["change_percentage"] = float(change_percentage)
    out["scenario_applied"] = {
        "dimension": str(dimension),
        "change_percentage": float(change_percentage),
        "overrides": overrides,
    }
    out["model_version"] = bundle.model_version
    out["point_model_version"] = bundle.point_model_version
    out["feature_version"] = bundle.feature_version
    return out
