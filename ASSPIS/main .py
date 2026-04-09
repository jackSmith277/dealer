from __future__ import annotations

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import re
import subprocess
import traceback
from multiprocessing import Process
from pathlib import Path
from typing import Any, Iterable

import numpy as np

import dealer_data_preprocessing as dp
from dealer_data_preprocessing import load_dealers_data
from model import (
    build_single_dimension_overrides,
    get_prev_year_month,
    load_point_bundle,
    predict_t1_what_if,
)
from quantile_forecast import (
    load_quantile_bundle,
    predict_for_dealer,
)
from radar import plot_dealers_radar, dealers_score

# ==============================================================================
# Flask app
# ==============================================================================
app = Flask(__name__)
CORS(app)

# ==============================================================================
# 配置
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent

FILE_PATHS = [
    os.getenv("ASSPIS_FILE_24", str(BASE_DIR / "24年11维度数据.xlsx")),
    os.getenv("ASSPIS_FILE_2223", str(BASE_DIR / "22-23数据.xlsx")),
]

SERVICE_DIR = Path(os.getenv("SERVICE_DIR", str(BASE_DIR / "service")))
REGISTRY_PATH = Path(os.getenv("REGISTRY_PATH", str(SERVICE_DIR / "registry.json")))
MANIFEST_PATH = Path(os.getenv("MANIFEST_PATH", str(SERVICE_DIR / "manifest.json")))
POINT_BUNDLE_PATH = Path(os.getenv("POINT_BUNDLE_PATH", str(SERVICE_DIR / "bundles" / "point_bundle.joblib")))
QUANTILE_BUNDLE_PATH = Path(
    os.getenv("QUANTILE_BUNDLE_PATH", str(SERVICE_DIR / "bundles" / "quantile_bundle.joblib"))
)

DEFAULT_HISTORY_MONTHS = int(os.getenv("DEFAULT_HISTORY_MONTHS", "10"))
MAX_HISTORY_MONTHS = int(os.getenv("MAX_HISTORY_MONTHS", "12"))
DEFAULT_QUANTILE_HORIZONS = [
    int(x) for x in os.getenv("DEFAULT_QUANTILE_HORIZONS", "1,2,3").split(",") if x.strip()
]
DEFAULT_QUANTILES = [
    float(x) for x in os.getenv("DEFAULT_QUANTILES", "0.1,0.5,0.9").split(",") if x.strip()
]
MAX_CUSTOM_HORIZON = int(os.getenv("MAX_CUSTOM_HORIZON", "9"))

FORECAST_TIER_PRESETS = {
    "short": [1, 2, 3],
    "mid": [1, 2, 3, 4, 5, 6],
    "long": [1, 2, 3, 4, 5, 6, 7, 8, 9],
}

DIMENSIONS = [
    "potential_customers",
    "test_drives",
    "leads",
    "customer_flow",
    "defeat_rate",
    "success_rate",
    "success_response_time",
    "defeat_response_time",
    "policy",
    "gsev",
    "lead_to_potential_rate",
    "potential_to_store_rate",
    "store_to_sales_rate",
]

# ==============================================================================
# 全局运行对象
# ==============================================================================
# 真实历史数据：只供 /sales/original、下拉列表、雷达图、分数等使用
# 预测一律走 bundle
app_state: dict[str, Any] = {
    "dealers_raw": {},
    "dealer_codes": [],
    "point_bundle": None,
    "quantile_bundle": None,
    "service_registry": None,
    "service_manifest": None,
    "bundle_paths": {},
    "point_bundle_loaded": False,
    "quantile_bundle_loaded": False,
    "init_failed": False,
    "initialized": False,
}


# ==============================================================================
# 基础工具函数
# ==============================================================================
def convert_numpy(obj):
    """递归转换 numpy 类型，避免 jsonify / Jinja 报错。"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    return obj


def _get_dealers_raw() -> dict[str, Any]:
    return app_state["dealers_raw"]


def _get_dealer_codes() -> list[str]:
    return app_state["dealer_codes"]


def _get_point_bundle():
    return app_state["point_bundle"]


def _get_quantile_bundle():
    return app_state["quantile_bundle"]


def _get_month_value(dealer_data, field: str, year: int, month: int):
    """
    兼容两种 key：
    - 新版：dict[(year, month)]
    - 旧版：dict[month]
    """
    d = getattr(dealer_data, field, {}) or {}
    if (year, month) in d:
        return d[(year, month)]
    return d.get(month, None)


def _infer_default_year(dealer_data, fallback: int = 2024) -> int:
    candidates: list[tuple[int, int]] = []
    for f in (
        "sales",
        "potential_customers",
        "test_drives",
        "leads",
        "customer_flow",
        "defeat_rate",
        "success_rate",
        "success_response_time",
        "defeat_response_time",
        "policy",
        "gsev",
    ):
        d = getattr(dealer_data, f, {}) or {}
        for k in d.keys():
            if isinstance(k, tuple) and len(k) == 2:
                candidates.append((int(k[0]), int(k[1])))
    if candidates:
        return max(candidates)[0]
    return int(fallback)


def _infer_all_years(dealers_raw: dict[str, Any]) -> list[int]:
    years = set()
    for dealer_data in dealers_raw.values():
        for field in ("sales", "potential_customers", "customer_flow", "leads"):
            d = getattr(dealer_data, field, {}) or {}
            for k in d.keys():
                if isinstance(k, tuple) and len(k) == 2:
                    years.add(int(k[0]))
    return sorted(years) if years else [2024]


def _safe_int(v, default=None):
    try:
        if v in (None, "", "null"):
            return default
        return int(v)
    except Exception:
        return default


def _safe_float(v, default=None):
    try:
        if v in (None, "", "null"):
            return default
        return float(v)
    except Exception:
        return default


def _coerce_horizons(value) -> list[int]:
    def _normalize(xs: list[int]) -> list[int]:
        xs = sorted({int(x) for x in xs if 1 <= int(x) <= MAX_CUSTOM_HORIZON})
        return xs or list(DEFAULT_QUANTILE_HORIZONS)

    if value is None:
        return list(DEFAULT_QUANTILE_HORIZONS)

    if isinstance(value, int):
        n = max(1, min(int(value), MAX_CUSTOM_HORIZON))
        return list(range(1, n + 1))

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return list(DEFAULT_QUANTILE_HORIZONS)
        if re.fullmatch(r"\d+", value):
            n = max(1, min(int(value), MAX_CUSTOM_HORIZON))
            return list(range(1, n + 1))
        return _normalize([int(x.strip()) for x in value.split(",") if x.strip()])

    if isinstance(value, Iterable):
        out = []
        for x in value:
            ix = _safe_int(x, None)
            if ix is not None:
                out.append(ix)
        return _normalize(out)

    return list(DEFAULT_QUANTILE_HORIZONS)


def _coerce_quantiles(value) -> list[float] | None:
    if value in (None, "", []):
        return None
    if isinstance(value, str):
        return [float(x.strip()) for x in value.split(",") if x.strip()]
    if isinstance(value, Iterable):
        return [float(x) for x in value]
    return None


def _resolve_forecast_horizons(payload: dict[str, Any]) -> tuple[str, list[int], int | None]:
    """
    统一解析 forecast mode：
    - short -> 1..3
    - mid   -> 1..6
    - long  -> 1..9
    - custom -> 1..N
    同时兼容旧接口直接传 horizons。
    """
    if payload.get("horizons") not in (None, "", []):
        horizons = _coerce_horizons(payload.get("horizons"))
        return "explicit_horizons", horizons, max(horizons) if horizons else None

    mode = (payload.get("forecast_mode") or payload.get("mode") or "short").strip().lower()

    if mode in FORECAST_TIER_PRESETS:
        horizons = list(FORECAST_TIER_PRESETS[mode])
        return mode, horizons, max(horizons)

    if mode == "custom":
        n = _safe_int(
            payload.get("custom_horizon_n", payload.get("horizon_n", payload.get("months"))),
            None,
        )
        if n is None:
            raise ValueError("custom 模式缺少 custom_horizon_n（1~9）")
        if not (1 <= int(n) <= MAX_CUSTOM_HORIZON):
            raise ValueError(f"custom_horizon_n 必须在 1~{MAX_CUSTOM_HORIZON} 之间")
        horizons = list(range(1, int(n) + 1))
        return mode, horizons, int(n)

    raise ValueError(f"无效 forecast_mode: {mode}")


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        traceback.print_exc()
    return None


def _norm_path(path_str: str | Path | None, *, base_dir: Path | None = None) -> Path | None:
    if not path_str:
        return None
    p = Path(str(path_str))
    if p.is_absolute():
        return p
    if base_dir is not None:
        return (base_dir / p).resolve()
    return p.resolve()


def _find_values_by_key(data: Any, key_patterns: list[str]) -> list[str]:
    """从未知 schema 的 registry / manifest 中递归抽取可能路径。"""
    results: list[str] = []

    def walk(node: Any):
        if isinstance(node, dict):
            for k, v in node.items():
                lk = str(k).lower()
                if any(pat in lk for pat in key_patterns):
                    if isinstance(v, str):
                        results.append(v)
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return results


def load_service_registry() -> dict[str, Any] | None:
    reg = _read_json_if_exists(REGISTRY_PATH)
    app_state["service_registry"] = reg
    return reg


def load_service_manifest(path: Path | None = None) -> dict[str, Any] | None:
    manifest_path = path or MANIFEST_PATH
    manifest = _read_json_if_exists(manifest_path)
    app_state["service_manifest"] = manifest
    return manifest


def resolve_active_bundle_paths() -> dict[str, Path]:
    """
    解析当前激活 bundle 路径。
    优先级：
    1. 显式环境变量 / 固定路径
    2. registry.json 中显式路径
    3. manifest.json 中显式路径
    """
    point_path = POINT_BUNDLE_PATH
    quantile_path = QUANTILE_BUNDLE_PATH
    manifest_path = MANIFEST_PATH

    registry = load_service_registry()
    if registry:
        reg_candidates = _find_values_by_key(
            registry,
            [
                "point_bundle_path",
                "point_bundle",
                "quantile_bundle_path",
                "quantile_bundle",
                "manifest_path",
                "active_manifest",
            ],
        )
        for candidate in reg_candidates:
            cand = str(candidate)
            lc = cand.lower()
            if lc.endswith("manifest.json"):
                manifest_path = _norm_path(cand, base_dir=REGISTRY_PATH.parent) or manifest_path
            elif "point_bundle" in lc and lc.endswith(".joblib"):
                point_path = _norm_path(cand, base_dir=REGISTRY_PATH.parent) or point_path
            elif "quantile_bundle" in lc and lc.endswith(".joblib"):
                quantile_path = _norm_path(cand, base_dir=REGISTRY_PATH.parent) or quantile_path

    manifest = load_service_manifest(manifest_path)
    if manifest:
        mani_candidates = _find_values_by_key(
            manifest,
            ["point_bundle_path", "point_bundle", "quantile_bundle_path", "quantile_bundle"],
        )
        for candidate in mani_candidates:
            cand = str(candidate)
            lc = cand.lower()
            if "point_bundle" in lc and lc.endswith(".joblib"):
                point_path = _norm_path(cand, base_dir=manifest_path.parent) or point_path
            elif "quantile_bundle" in lc and lc.endswith(".joblib"):
                quantile_path = _norm_path(cand, base_dir=manifest_path.parent) or quantile_path

    resolved = {
        "service_dir": SERVICE_DIR,
        "registry_path": REGISTRY_PATH,
        "manifest_path": manifest_path,
        "point_bundle_path": point_path,
        "quantile_bundle_path": quantile_path,
    }
    app_state["bundle_paths"] = resolved
    return resolved


def preload_service_bundles():
    paths = resolve_active_bundle_paths()
    point_path = Path(paths["point_bundle_path"])
    quantile_path = Path(paths["quantile_bundle_path"])

    if not point_path.exists():
        raise FileNotFoundError(f"point bundle 不存在: {point_path}")
    if not quantile_path.exists():
        raise FileNotFoundError(f"quantile bundle 不存在: {quantile_path}")

    point_bundle = load_point_bundle(point_path)
    quantile_bundle = load_quantile_bundle(quantile_path)

    app_state["point_bundle"] = point_bundle
    app_state["quantile_bundle"] = quantile_bundle
    app_state["point_bundle_loaded"] = True
    app_state["quantile_bundle_loaded"] = True

    print("[service] bundles loaded")
    print(f"  point_bundle    : {point_path}")
    print(f"  quantile_bundle : {quantile_path}")
    print(f"  point_version   : {getattr(point_bundle, 'model_version', None)}")
    print(f"  quantile_ver    : {getattr(quantile_bundle, 'model_version', None)}")


# ==============================================================================
# 初始化
# ==============================================================================
def init_app(force: bool = False):
    if app_state["init_failed"] and not force:
        print("init_app: 上次初始化失败，停止重复初始化")
        return
    if app_state["initialized"] and not force:
        return

    print("[service] 正在加载原始 dealer 数据与离线 bundles...")
    try:
        dealers_raw, dealer_codes = load_dealers_data(FILE_PATHS)
        app_state["dealers_raw"] = dealers_raw
        app_state["dealer_codes"] = dealer_codes
        preload_service_bundles()
        app_state["initialized"] = True
        app_state["init_failed"] = False
        print(f"[service] init done | dealers={len(dealers_raw)}")
    except Exception as e:
        app_state["init_failed"] = True
        app_state["initialized"] = False
        print(f"[service] 初始化失败: {e}")
        traceback.print_exc()


# ==============================================================================
# 业务辅助函数
# ==============================================================================
def get_dealer_by_code(dealer_code: str):
    return _get_dealers_raw().get(str(dealer_code))


def _ensure_ready(require_quantile: bool = False) -> tuple[bool, str | None]:
    if not app_state["initialized"]:
        init_app()
    if not app_state["initialized"]:
        return False, "服务初始化失败，请检查 bundle 路径与控制台日志"
    if not app_state["point_bundle_loaded"]:
        return False, "point bundle 未加载"
    if require_quantile and not app_state["quantile_bundle_loaded"]:
        return False, "quantile bundle 未加载"
    return True, None


def _original_sales_series(dealer_data, year: int, months: int = DEFAULT_HISTORY_MONTHS) -> dict[int, float | None]:
    months = max(1, min(int(months), int(MAX_HISTORY_MONTHS)))
    return {
        m: (
            float(v) if (v := _get_month_value(dealer_data, "sales", int(year), m)) is not None else None
        )
        for m in range(1, months + 1)
    }


def _bundle_meta() -> dict[str, Any]:
    point_bundle = _get_point_bundle()
    quantile_bundle = _get_quantile_bundle()
    return {
        "point_bundle_loaded": bool(app_state["point_bundle_loaded"]),
        "quantile_bundle_loaded": bool(app_state["quantile_bundle_loaded"]),
        "point_model_version": getattr(point_bundle, "model_version", None),
        "quantile_model_version": getattr(quantile_bundle, "model_version", None),
        "point_feature_version": getattr(point_bundle, "feature_version", None),
        "quantile_feature_version": getattr(quantile_bundle, "feature_version", None),
        "point_trained_at": getattr(point_bundle, "trained_at", None),
        "quantile_trained_at": getattr(quantile_bundle, "trained_at", None),
        "quantile_horizons_supported": getattr(quantile_bundle, "horizons_supported", None),
        "quantile_quantiles": getattr(quantile_bundle, "quantiles", None),
        "bundle_paths": {
            k: str(v) for k, v in (app_state.get("bundle_paths") or {}).items()
        },
        "active_manifest": app_state.get("service_manifest"),
    }


def _predict_point_single(
    dealer_code: str,
    dimension: str,
    change_percentage: float,
    *,
    base_year: int,
    base_month: int,
) -> dict[str, Any]:
    point_bundle = _get_point_bundle()
    dealers_raw = _get_dealers_raw()
    return predict_t1_what_if(
        point_bundle,
        dealers_raw,
        dealer_code=dealer_code,
        base_year=int(base_year),
        base_month=int(base_month),
        dimension=str(dimension),
        change_percentage=float(change_percentage),
    )



def _sales_predict_payload_from_point_result(result: dict[str, Any], dealer_data) -> tuple[list[dict], list[dict]]:
    target_year = int(result["target_year"])
    target_month = int(result["target_month"])
    orig_val = _get_month_value(dealer_data, "sales", target_year, target_month)
    original_sales = float(orig_val) if orig_val is not None else None

    sales_prediction = [{
        "base_year": int(result["base_year"]),
        "base_month": int(result["base_month"]),
        "target_year": target_year,
        "target_month": target_month,
        "year": target_year,
        "month": target_month,
        "baseline_prediction": float(result["baseline"]),
        "scenario_prediction": float(result["scenario"]),
        "predicted_sales": float(result["scenario"]),
        "original_sales": original_sales,
    }]

    sales_changes = [{
        "base_year": int(result["base_year"]),
        "base_month": int(result["base_month"]),
        "target_year": target_year,
        "target_month": target_month,
        "year": target_year,
        "month": target_month,
        "baseline_prediction": float(result["baseline"]),
        "scenario_prediction": float(result["scenario"]),
        "sales_change": float(result["delta"]),
        "sales_change_pct": float(result["delta_pct"]),
        "delta": float(result["delta"]),
        "delta_pct": float(result["delta_pct"]),
    }]
    return sales_prediction, sales_changes



def _predict_point_batch_by_target_months(
    dealer_code: str,
    dimension: str,
    change_percentage: float,
    *,
    target_year: int,
    target_months: list[int],
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    批量输出 target months。
    内部统一换算成各 target month 的 base month，再调用 predict_t1_what_if。
    """
    dealer_data = get_dealer_by_code(dealer_code)
    sales_prediction: list[dict] = []
    sales_changes: list[dict] = []
    errors: list[dict] = []

    for target_month in target_months:
        base_year, base_month = get_prev_year_month(int(target_year), int(target_month), 1)
        try:
            result = _predict_point_single(
                dealer_code,
                dimension,
                change_percentage,
                base_year=base_year,
                base_month=base_month,
            )
            one_pred, one_change = _sales_predict_payload_from_point_result(result, dealer_data)
            sales_prediction.extend(one_pred)
            sales_changes.extend(one_change)
        except Exception as e:
            errors.append({
                "target_year": int(target_year),
                "target_month": int(target_month),
                "base_year": int(base_year),
                "base_month": int(base_month),
                "message": str(e),
            })

    return sales_prediction, sales_changes, errors


# ==============================================================================
# 页面路由
# ==============================================================================
@app.route("/test")
def test_forecast_page():
    return render_template("test_forecast.html")


@app.route("/", methods=["GET", "POST"])
def index():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return render_template("index.html", message=msg, dealer_codes=[]), 503

    radar_img = None
    dealer_code = None
    sales_prediction = None
    sales_changes = []
    original_sales = None
    dealer_scores_map = {}
    message = None

    # 这里前端已统一为 base_year / base_month；同时保留对旧 year / month 字段的兼容读取
    base_year_input = None
    base_month_input = None
    target_year_input = None
    target_month_input = None
    dimension_input = None
    change_percentage_input = None
    month_for_radar = None
    radar_year = None

    if request.method == "POST":
        dealer_code_input = (request.form.get("dealer_code") or "").strip()
        dimension_input = (request.form.get("dimension") or "").strip()
        change_percentage_input = _safe_float(request.form.get("change_percentage"), None)

        base_year_input = _safe_int(request.form.get("base_year"), None)
        base_month_input = _safe_int(request.form.get("base_month"), None)

        # 向后兼容：若前端模板暂未改名，则 year/month 按 base 解释
        if base_year_input is None:
            base_year_input = _safe_int(request.form.get("year"), None)
        if base_month_input is None:
            base_month_input = _safe_int(request.form.get("month"), None)

        radar_year = _safe_int(request.form.get("radar_year"), base_year_input or 2024)
        month_for_radar = _safe_int(request.form.get("radar_month"), None)

        if dealer_code_input and dimension_input and change_percentage_input is not None:
            try:
                if base_year_input is None or base_month_input is None:
                    raise ValueError("页面表单缺少 base_year / base_month")

                dealer_data = get_dealer_by_code(dealer_code_input)
                result = _predict_point_single(
                    dealer_code_input,
                    dimension_input,
                    change_percentage_input,
                    base_year=base_year_input,
                    base_month=base_month_input,
                )
                sales_prediction, sales_changes = _sales_predict_payload_from_point_result(result, dealer_data)
                target_year_input = int(result["target_year"])
                target_month_input = int(result["target_month"])
                original_sales = _original_sales_series(dealer_data, target_year_input, DEFAULT_HISTORY_MONTHS)
                dealer_code = dealer_code_input
            except Exception as e:
                traceback.print_exc()
                message = f"预测过程发生错误：{e}"

        try:
            if dealer_code_input and month_for_radar is not None:
                radar_img_path = plot_dealers_radar(dealer_code_input, month_for_radar, year=radar_year)
                if radar_img_path:
                    radar_img = f"/static/{os.path.basename(radar_img_path)}"
                elif message is None:
                    message = "雷达图生成失败，请检查输入数据是否完整。"
        except Exception as e:
            if message is None:
                message = f"生成雷达图时发生错误：{e}"

        try:
            if dealer_code_input and month_for_radar is not None:
                dealer_scores_map = dealers_score(dealer_code_input, month_for_radar, year=radar_year)
        except Exception as e:
            if message is None:
                message = f"经销商评分计算失败：{e}"

        return render_template(
            "index.html",
            radar_img=radar_img,
            dealer_code=dealer_code,
            sales_prediction=convert_numpy(sales_prediction),
            sales_changes=convert_numpy(sales_changes),
            original_sales=convert_numpy(original_sales),
            dealer_scores=convert_numpy(dealer_scores_map),
            dealer_codes=_get_dealer_codes(),
            dimension=dimension_input,
            change_percentage=change_percentage_input,
            base_year=base_year_input,
            base_month=base_month_input,
            target_year=target_year_input,
            target_month=target_month_input,
            # 向后兼容模板旧变量名
            year=base_year_input,
            month=base_month_input,
            month_for_radar=f"{month_for_radar}月" if month_for_radar else None,
            message=message,
        )

    return render_template(
        "index.html",
        radar_img=None,
        dealer_code=None,
        sales_prediction=None,
        sales_changes=[],
        original_sales=None,
        dealer_scores={},
        dealer_codes=_get_dealer_codes(),
        dimension=None,
        change_percentage=None,
        base_year=None,
        base_month=None,
        target_year=None,
        target_month=None,
        year=None,
        month=None,
        month_for_radar=None,
        message=None,
    )


# ==============================================================================
# API
# ==============================================================================
@app.get("/dealers")
def api_dealers():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503
    return jsonify({
        "dealer_codes": _get_dealer_codes(),
        "count": len(_get_dealer_codes()),
    })


@app.get("/options")
def api_options():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    dealers_raw = _get_dealers_raw()
    years = _infer_all_years(dealers_raw)
    return jsonify({
        "dimensions": DIMENSIONS,
        "years": years,
        "default_history_months": DEFAULT_HISTORY_MONTHS,
        "default_quantile_horizons": DEFAULT_QUANTILE_HORIZONS,
        "default_quantiles": DEFAULT_QUANTILES,
        "forecast_tier_presets": FORECAST_TIER_PRESETS,
        "max_custom_horizon": MAX_CUSTOM_HORIZON,
        "bundle_meta": convert_numpy(_bundle_meta()),
    })


@app.get("/health")
def api_health():
    ok, msg = _ensure_ready(require_quantile=False)
    status = "ok" if ok else "degraded"
    return jsonify({
        "status": status,
        "message": msg,
        "initialized": bool(app_state["initialized"]),
        "init_failed": bool(app_state["init_failed"]),
        "dealers_loaded": len(_get_dealers_raw()),
        "bundle_meta": convert_numpy(_bundle_meta()),
    }), (200 if ok else 503)


@app.get("/service/manifest")
def api_service_manifest():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503
    return jsonify({
        "registry": convert_numpy(app_state.get("service_registry")),
        "manifest": convert_numpy(app_state.get("service_manifest")),
        "bundle_paths": convert_numpy({k: str(v) for k, v in (app_state.get("bundle_paths") or {}).items()}),
    })


@app.get("/sales/original")
def api_sales_original():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    dealer_code = (request.args.get("dealer_code") or "").strip()
    dealer_data = get_dealer_by_code(dealer_code)
    if not dealer_code or dealer_data is None:
        return jsonify({"message": "dealer_code 不存在或为空"}), 400

    year = _safe_int(request.args.get("year"), _infer_default_year(dealer_data, fallback=2024))
    months = _safe_int(request.args.get("months"), DEFAULT_HISTORY_MONTHS)
    data = []
    for m in range(1, max(1, min(int(months), int(MAX_HISTORY_MONTHS))) + 1):
        val = _get_month_value(dealer_data, "sales", year, m)
        data.append({"year": int(year), "month": int(m), "sales": float(val) if val is not None else None})

    return jsonify({
        "dealer_code": dealer_code,
        "year": int(year),
        "months": int(months),
        "data": data,
    })


@app.post("/sales/predict")
def api_sales_predict():
    """
    方案 A：前后端统一使用 base_year / base_month。

    支持两种模式：
    1. 单点模式：传 base_year + base_month，返回 t+1 的 what-if 预测。
    2. 批量模式：不传 base_month 时，可传 target_year + target_months / predict_all，
       后端内部自动把 target 月换算成对应的 base 月，再循环调用 point bundle。
    """
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    payload = request.get_json(silent=True) or {}
    dealer_code = (payload.get("dealer_code") or "").strip()
    dimension = (payload.get("dimension") or "").strip()
    change_percentage = _safe_float(payload.get("change_percentage"), None)

    if not dealer_code or not dimension or change_percentage is None:
        return jsonify({"message": "缺少 dealer_code / dimension / change_percentage"}), 400
    if dimension not in DIMENSIONS:
        return jsonify({"message": f"无效 dimension: {dimension}"}), 400

    dealer_data = get_dealer_by_code(dealer_code)
    if dealer_data is None:
        return jsonify({"message": "dealer_code 不存在"}), 400

    base_year = _safe_int(payload.get("base_year"), None)
    base_month = _safe_int(payload.get("base_month"), None)
    month_for_radar = _safe_int(payload.get("month_for_radar"), None)

    # 兼容旧字段：如果前端一时未同步，把 year/month 按 base 解释
    if base_year is None:
        base_year = _safe_int(payload.get("year"), None)
    if base_month is None:
        base_month = _safe_int(payload.get("month"), None)

    response_data: dict[str, Any] = {
        "dealer_code": dealer_code,
        "dimension": dimension,
        "change_percentage": float(change_percentage),
        "dealer_scores": {},
        "bundle_meta": _bundle_meta(),
    }

    try:
        if base_year is not None and base_month is not None:
            result = _predict_point_single(
                dealer_code,
                dimension,
                change_percentage,
                base_year=base_year,
                base_month=base_month,
            )
            sales_prediction, sales_changes = _sales_predict_payload_from_point_result(result, dealer_data)
            target_year = int(result["target_year"])
            target_month = int(result["target_month"])
            original_sales = _original_sales_series(dealer_data, target_year, DEFAULT_HISTORY_MONTHS)

            response_data.update({
                "status": "success",
                "mode": "single_t1",
                "base_year": int(base_year),
                "base_month": int(base_month),
                "target_year": target_year,
                "target_month": target_month,
                "original_sales": original_sales,
                "sales_prediction": sales_prediction,
                "sales_changes": sales_changes,
                "point_result": result,
                # 向后兼容旧返回字段
                "year": int(base_year),
                "month": int(base_month),
                "message": None,
            })
        else:
            target_year = _safe_int(payload.get("target_year"), _infer_default_year(dealer_data, fallback=2024))
            target_months_raw = payload.get("target_months", None)
            predict_all = bool(payload.get("predict_all", False))
            months_limit = _safe_int(payload.get("months"), DEFAULT_HISTORY_MONTHS)

            if target_months_raw is None:
                if predict_all:
                    target_months = list(range(1, max(1, min(months_limit, MAX_HISTORY_MONTHS)) + 1))
                else:
                    target_months = list(range(1, max(1, min(months_limit, DEFAULT_HISTORY_MONTHS)) + 1))
            elif isinstance(target_months_raw, str):
                target_months = [int(x.strip()) for x in target_months_raw.split(",") if x.strip()]
            else:
                target_months = [int(x) for x in target_months_raw]

            sales_prediction, sales_changes, errors = _predict_point_batch_by_target_months(
                dealer_code,
                dimension,
                change_percentage,
                target_year=target_year,
                target_months=target_months,
            )
            original_sales = _original_sales_series(dealer_data, target_year, max(target_months) if target_months else DEFAULT_HISTORY_MONTHS)

            response_data.update({
                "status": "success" if sales_prediction else "partial_data",
                "mode": "batch_by_target_months",
                "target_year": int(target_year),
                "target_months": target_months,
                "original_sales": original_sales,
                "sales_prediction": sales_prediction,
                "sales_changes": sales_changes,
                "errors": errors,
                "message": None if sales_prediction else "所选月份无法生成有效预测，请查看 errors 字段",
            })

        if month_for_radar is not None:
            try:
                radar_year = response_data.get("target_year") or response_data.get("base_year") or _infer_default_year(dealer_data, 2024)
                response_data["dealer_scores"] = dealers_score(dealer_code, month_for_radar, year=radar_year)
            except Exception as e:
                response_data["dealer_scores"] = {}
                response_data["dealer_scores_message"] = str(e)

        return jsonify(convert_numpy(response_data))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"后端处理错误：{e}"}), 500


@app.post("/forecast/quantiles")
def api_forecast_quantiles():
    """
    分位数预测接口：
    - 只做参数转换与 bundle 调用
    - 不再在线 fit QuantileForecaster
    - 与方案 A 一致：base_year / base_month 表示基准月，h=1 对应 t+1
    """
    ok, msg = _ensure_ready(require_quantile=True)
    if not ok:
        return jsonify({"message": msg}), 503

    payload = request.get_json(silent=True) or {}
    dealer_code = (payload.get("dealer_code") or "").strip()
    dealer_data = get_dealer_by_code(dealer_code)
    if not dealer_code or dealer_data is None:
        return jsonify({"message": "dealer_code 不存在或为空"}), 400

    quantile_bundle = _get_quantile_bundle()
    base_year = _safe_int(payload.get("base_year"), _infer_default_year(dealer_data, fallback=2024))
    base_month = _safe_int(payload.get("base_month"), None)
    if base_month is None:
        base_month = quantile_bundle.forecaster.default_base_month(dealer_data, year=base_year)
        if base_month is None:
            return jsonify({"message": "该 dealer 无法找到特征齐全的 base_month"}), 400

    try:
        forecast_mode, horizons, custom_horizon_n = _resolve_forecast_horizons(payload)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    quantiles = _coerce_quantiles(payload.get("quantiles", None))

    scenarios = payload.get("scenarios", None)
    if not scenarios:
        scenarios = [{"name": "baseline"}]
        dim = (payload.get("dimension") or "").strip()
        chg = _safe_float(payload.get("change_percentage"), None)
        if dim and chg is not None:
            scenarios.append({
                "name": f"{dim}{chg:+.1f}%",
                "dimension": dim,
                "change_percentage": chg,
            })

    result: dict[str, Any] = {
        "dealer_code": dealer_code,
        "base_year": int(base_year),
        "base_month": int(base_month),
        "forecast_mode": forecast_mode,
        "custom_horizon_n": custom_horizon_n,
        "horizons": horizons,
        "meta": {
            "method": "bundle_quantile_forecast",
            "point_model_version": getattr(quantile_bundle, "point_model_version", None),
            "quantile_model_version": getattr(quantile_bundle, "model_version", None),
            "feature_version": getattr(quantile_bundle, "feature_version", None),
            "horizons_supported": getattr(quantile_bundle, "horizons_supported", None),
            "quantiles": quantiles or getattr(quantile_bundle, "quantiles", None),
            "forecast_tier_presets": FORECAST_TIER_PRESETS,
            "max_custom_horizon": MAX_CUSTOM_HORIZON,
        },
        "scenarios": {},
    }

    for sc in scenarios:
        name = (sc.get("name") or "scenario").strip()
        dim = (sc.get("dimension") or "").strip()
        chg = _safe_float(sc.get("change_percentage"), None)

        overrides = None
        scenario_applied = None
        if dim:
            if dim not in DIMENSIONS:
                result["scenarios"][name] = {"message": f"无效 dimension: {dim}"}
                continue
            if chg is None:
                result["scenarios"][name] = {"message": f"情景 {name} 缺少 change_percentage"}
                continue
            overrides = build_single_dimension_overrides(
                dealer_data,
                dimension=dim,
                change_percentage=float(chg),
                year=int(base_year),
                month=int(base_month),
                feature_context=quantile_bundle.feature_context,
                config=quantile_bundle.feature_context.config,
            )
            scenario_applied = {
                "dimension": dim,
                "change_percentage": float(chg),
                "overrides": overrides,
            }

        pred = predict_for_dealer(
            quantile_bundle,
            _get_dealers_raw(),
            dealer_code,
            base_year=int(base_year),
            base_month=int(base_month),
            horizons=horizons,
            quantiles=quantiles,
            overrides=overrides,
        )
        if scenario_applied is not None:
            pred["scenario_applied"] = scenario_applied

        pred["request_summary"] = {
            "forecast_mode": forecast_mode,
            "custom_horizon_n": custom_horizon_n,
            "horizons": horizons,
            "n_periods": len(horizons),
        }
        result["scenarios"][name] = pred

    return jsonify(convert_numpy(result))


# ==============================================================================
# 其它辅助进程
# ==============================================================================
def run_line_chart():
    if not Path("line_chart.py").exists():
        return
    subprocess.run(["python", "line_chart.py"])


# ==============================================================================
# 程序入口
# ==============================================================================
if __name__ == "__main__":
    from multiprocessing import freeze_support

    freeze_support()
    init_app()

    line_chart_process = None
    if Path("line_chart.py").exists():
        line_chart_process = Process(target=run_line_chart)
        line_chart_process.start()

    try:
        app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
    finally:
        if line_chart_process is not None:
            line_chart_process.terminate()
