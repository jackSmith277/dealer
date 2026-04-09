from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from multiprocessing import Process, freeze_support
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

import jwt
import numpy as np
import pandas as pd
from passlib.hash import pbkdf2_sha256

load_dotenv()

ASSPIS_DIR = Path(__file__).parent / "ASSPIS"
BACKEND_DIR = Path(__file__).parent / "back"
AIPLUGIN_DIR = Path(__file__).parent / "aiplugin" / "插件" / "汽车服务"

sys.path.insert(0, str(ASSPIS_DIR))
sys.path.insert(0, str(BACKEND_DIR))

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
from wordcloud_service import wordcloud_generator

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '123456')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'dealer_management')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

BASE_DIR = Path(__file__).parent.resolve()
ASSPIS_BASE_DIR = ASSPIS_DIR

FILE_PATHS = [
    os.getenv("ASSPIS_FILE_24", str(ASSPIS_BASE_DIR / "24年11维度数据.xlsx")),
    os.getenv("ASSPIS_FILE_2223", str(ASSPIS_BASE_DIR / "22-23数据.xlsx")),
]

SERVICE_DIR = Path(os.getenv("SERVICE_DIR", str(ASSPIS_BASE_DIR / "service")))
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

AIPLUGIN_SOURCE_DIR = AIPLUGIN_DIR
SCRAPER_PATH = AIPLUGIN_SOURCE_DIR / "新爬取.py"
ANALYZER_PATH = AIPLUGIN_SOURCE_DIR / "评论分析.py"
AIPLUGIN_RUNTIME_DIR = Path(os.getenv('AIPLUGIN_RUNTIME_DIR', str(Path(__file__).parent / "aiplugin_runtime")))

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


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='dealer')
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dealer(db.Model):
    __tablename__ = 'dealers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dealer_name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    contact_name = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(20), nullable=False)
    dimension = db.Column(db.String(50), nullable=False)
    change_percentage = db.Column(db.Integer, nullable=False)
    base_year = db.Column(db.Integer, default=2024)
    base_month = db.Column(db.Integer, nullable=False)
    target_year = db.Column(db.Integer, default=2024)
    target_month = db.Column(db.Integer, nullable=False)
    predicted_sales = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AnalysisReport(db.Model):
    __tablename__ = 'analysis_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    dealer_code = db.Column(db.String(20), nullable=False)
    report_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    selected_cards = db.Column(db.Text, nullable=False)
    report_content = db.Column(db.Text, nullable=False)


class MonthlyMetrics11d(db.Model):
    __tablename__ = 'monthly_metrics_11d'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False)
    stat_year = db.Column(db.Integer, nullable=False)
    stat_month = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Numeric(18, 4), nullable=True)
    potential_customers = db.Column(db.Numeric(18, 4), nullable=True)
    test_drives = db.Column(db.Numeric(18, 4), nullable=True)
    leads = db.Column(db.Numeric(18, 4), nullable=True)
    customer_flow = db.Column(db.Numeric(18, 4), nullable=True)
    defeat_rate = db.Column(db.Numeric(18, 6), nullable=True)
    success_rate = db.Column(db.Numeric(18, 6), nullable=True)
    success_response_time = db.Column(db.Numeric(18, 4), nullable=True)
    defeat_response_time = db.Column(db.Numeric(18, 4), nullable=True)
    policy = db.Column(db.Numeric(18, 4), nullable=True)
    gsev = db.Column(db.Numeric(18, 4), nullable=True)


class MonthlyRadarScores(db.Model):
    __tablename__ = 'monthly_radar_scores'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False)
    stat_year = db.Column(db.Integer, nullable=False)
    stat_month = db.Column(db.Integer, nullable=False)
    spread_force = db.Column(db.Numeric(18, 4), nullable=True)
    experience_force = db.Column(db.Numeric(18, 4), nullable=True)
    conversion_force = db.Column(db.Numeric(18, 4), nullable=True)
    service_force = db.Column(db.Numeric(18, 4), nullable=True)
    operation_force = db.Column(db.Numeric(18, 4), nullable=True)


class TestDriveComment(db.Model):
    __tablename__ = 'test_drive_comments'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=True)
    dealer_name = db.Column(db.String(100), nullable=True)
    car_model = db.Column(db.String(100), nullable=True)
    service_advisor = db.Column(db.String(50), nullable=True)
    comment_content = db.Column(db.Text, nullable=True)
    appeal_status = db.Column(db.String(50), nullable=True)
    modify_status = db.Column(db.String(50), nullable=True)
    comment_status = db.Column(db.String(50), nullable=True)
    overall_score = db.Column(db.Numeric(5, 2), nullable=True)
    comment_time = db.Column(db.DateTime, nullable=True)
    work_order_no = db.Column(db.String(100), nullable=True)
    invitation_time = db.Column(db.DateTime, nullable=True)
    region = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    appeal_reason = db.Column(db.Text, nullable=True)
    headquarters_reply = db.Column(db.Text, nullable=True)
    appeal_audit_time = db.Column(db.DateTime, nullable=True)
    process_score = db.Column(db.Text, nullable=True)
    process_score_tags = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ConsumptionPolicy(db.Model):
    __tablename__ = 'consumption_policies'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    policy_name = db.Column(db.String(255), nullable=False)
    province = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    district = db.Column(db.String(50), nullable=True)
    policy_category = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.String(50), nullable=True)
    end_date = db.Column(db.String(50), nullable=True)
    policy_content = db.Column(db.Text, nullable=True)
    source_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash='admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
    
    try:
        dealer_count = db.session.execute(db.text("SELECT COUNT(*) FROM v_dealer_info")).scalar()
        existing_dealer_count = Dealer.query.count()
        
        if dealer_count > 0 and existing_dealer_count == 0:
            print(f"开始导入 {dealer_count} 个经销商数据...")
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            added_count = 0
            
            for row in dealer_info_result:
                dealer_code = row[0]
                province = row[1] or ''
                city = row[2] or ''
                fed_level = row[3] or ''
                
                existing_user = User.query.filter_by(username=dealer_code).first()
                if existing_user:
                    continue
                
                user = User(
                    username=dealer_code,
                    password_hash='123456',
                    role='dealer',
                    status=1
                )
                db.session.add(user)
                db.session.flush()
                
                region = f"{province}{city}" if province and city else (province or city or '')
                
                dealer = Dealer(
                    user_id=user.id,
                    dealer_name=dealer_code,
                    level=fed_level,
                    region=region,
                    contact_name='',
                    contact_phone='',
                    address='',
                )
                db.session.add(dealer)
                added_count += 1
            
            db.session.commit()
            print(f"成功导入 {added_count} 个经销商数据")
    except Exception as e:
        print(f"导入经销商数据失败: {str(e)}")
        db.session.rollback()


def convert_numpy(obj):
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
    if value is None:
        return list(DEFAULT_QUANTILE_HORIZONS)
    if isinstance(value, int):
        return list(range(1, int(value) + 1))
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return list(DEFAULT_QUANTILE_HORIZONS)
        if re.fullmatch(r"\d+", value):
            n = int(value)
            return list(range(1, n + 1))
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    if isinstance(value, Iterable):
        out = []
        for x in value:
            ix = _safe_int(x, None)
            if ix is not None:
                out.append(ix)
        return out or list(DEFAULT_QUANTILE_HORIZONS)
    return list(DEFAULT_QUANTILE_HORIZONS)


def _coerce_quantiles(value) -> list[float] | None:
    if value in (None, "", []):
        return None
    if isinstance(value, str):
        return [float(x.strip()) for x in value.split(",") if x.strip()]
    if isinstance(value, Iterable):
        return [float(x) for x in value]
    return None


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


def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + __import__('datetime').timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except:
        return None


def load_module(module_name: str, file_path: Path, strip_after: str | None = None):
    source = file_path.read_text(encoding="utf-8")
    if strip_after and strip_after in source:
        source = source.split(strip_after, 1)[0]
    module = ModuleType(module_name)
    module.__file__ = str(file_path)
    sys.modules[module_name] = module
    exec(compile(source, str(file_path), "exec"), module.__dict__)
    return module


def ensure_runtime_dirs() -> dict[str, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = AIPLUGIN_RUNTIME_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": run_dir,
        "excel": run_dir / "reviews.xlsx",
        "report": run_dir / "review_analysis_report.md",
        "summary_excel": run_dir / "review_analysis_summary.xlsx",
        "reviews_json": run_dir / "reviews.json",
    }


def read_excel_file(file_path: Path) -> dict[str, pd.DataFrame]:
    suffix = file_path.suffix.lower()
    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    excel = pd.ExcelFile(file_path, engine=engine)
    return {sheet_name: pd.read_excel(file_path, sheet_name=sheet_name, engine=engine) for sheet_name in excel.sheet_names}


class DataCleaningTool:
    def run(self, parameters: dict) -> str:
        data_json = parameters.get("data_json")
        if not data_json:
            return "错误：缺少原始数据"
        try:
            raw_data = json.loads(data_json)
            records = raw_data.get("完整数据", raw_data.get("data", []))
            if not records:
                return "警告：原始数据为空"
            df = pd.DataFrame(records)
            columns_to_keep = parameters.get("columns_to_keep")
            if columns_to_keep:
                df = df[columns_to_keep]
            if parameters.get("drop_na", False):
                df = df.dropna()
            df = df.fillna(0)
            cleaned_records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return json.dumps({"clean_data": cleaned_records}, ensure_ascii=False, indent=2)
        except Exception as exc:
            return f"清洗出错：{exc}"


class DataStatisticsTool:
    def run(self, parameters: dict) -> str:
        data_json = parameters.get("data_json")
        if not data_json:
            return "错误：缺少数据"
        try:
            raw_data = json.loads(data_json)
            records = raw_data.get("clean_data", raw_data.get("data", []))
            df = pd.DataFrame(records)
            numeric_stats = {}
            for col in df.select_dtypes(include=[np.number]).columns:
                numeric_stats[str(col)] = {
                    "count": int(df[col].count()),
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()) if pd.notna(df[col].std()) else 0.0,
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }
            categorical_stats = {}
            for col in df.select_dtypes(include=["object"]).columns:
                categorical_stats[str(col)] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": df[col].astype(str).value_counts().head(10).to_dict(),
                }
            result = {
                "shape": f"{len(df)} 行，{len(df.columns)} 列",
                "numeric_stats": numeric_stats,
                "categorical_stats": categorical_stats,
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return f"统计出错：{exc}"


def preview_markdown(df: pd.DataFrame, limit: int = 5) -> str:
    preview = df.head(limit).fillna("")
    if preview.empty:
        return "无可预览数据。"
    headers = [str(col) for col in preview.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in preview.iterrows():
        values = [str(value).replace("\n", " ").replace("|", "\\|") for value in row.tolist()]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_key_findings(df: pd.DataFrame, stats: dict) -> list[str]:
    findings: list[str] = []
    numeric_stats = stats.get("numeric_stats", {})
    categorical_stats = stats.get("categorical_stats", {})

    for col, item in list(numeric_stats.items())[:4]:
        spread = item["max"] - item["min"]
        findings.append(
            f"`{col}` 的均值为 `{item['mean']:.2f}`，中位数为 `{item['median']:.2f}`，区间跨度为 `{spread:.2f}`。"
        )

    for col, item in list(categorical_stats.items())[:2]:
        top_values = item.get("top_values", {})
        if top_values:
            top_label = next(iter(top_values.keys()))
            top_count = top_values[top_label]
            findings.append(f"`{col}` 共出现 `{item['unique_count']}` 个不同取值，其中 `{top_label}` 最常见，出现 `{top_count}` 次。")

    if not findings:
        findings.append("该表以文本列为主，暂无足够数值字段进行深入统计。")
    return findings


def build_trend_analysis(df: pd.DataFrame) -> list[str]:
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if len(numeric_cols) < 2:
        return ["未识别到足够的数值列，暂不生成趋势分析。"]

    first_col = df.columns[0]
    trend_lines: list[str] = []
    for _, row in df.head(6).iterrows():
        values = [(col, row[col]) for col in numeric_cols if pd.notna(row[col])]
        if len(values) < 2:
            continue
        start_col, start_val = values[-1]
        end_col, end_val = values[0]
        delta = float(end_val) - float(start_val)
        direction = "上升" if delta > 0 else "下降" if delta < 0 else "持平"
        trend_lines.append(
            f"`{row[first_col]}` 从 `{start_col}` 的 `{float(start_val):.2f}` 变化到 `{end_col}` 的 `{float(end_val):.2f}`，整体呈 `{direction}` 趋势。"
        )
    return trend_lines or ["未生成有效趋势分析。"]


def build_markdown_report(file_name: str, sheet_name: str, df: pd.DataFrame, clean_data: dict, stats: dict) -> str:
    findings = build_key_findings(df, stats)
    trends = build_trend_analysis(df)
    numeric_stats = stats.get("numeric_stats", {})

    stat_lines = [
        "| 列名 | 均值 | 中位数 | 标准差 | 最小值 | 最大值 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for col, item in list(numeric_stats.items())[:8]:
        stat_lines.append(
            f"| {col} | {item['mean']:.2f} | {item['median']:.2f} | {item['std']:.2f} | {item['min']:.2f} | {item['max']:.2f} |"
        )
    if len(stat_lines) == 2:
        stat_lines.append("| 无数值列 | - | - | - | - | - |")

    return "\n".join(
        [
            "# 数据分析报告",
            "",
            "## 分析背景与目标",
            "",
            f"本次分析基于文件 `{file_name}` 中的工作表 `{sheet_name}` 展开，目标是对数据进行清洗、统计概览与趋势识别，并输出适合前端展示的 Markdown 报告。",
            "",
            "## 数据概况",
            "",
            f"- 数据规模：`{stats.get('shape', f'{len(df)} 行，{len(df.columns)} 列')}`",
            f"- 原始字段：`{'`, `'.join(map(str, df.columns.tolist()))}`",
            f"- 清洗后记录数：`{len(clean_data.get('clean_data', []))}`",
            "",
            "## 数据预览",
            "",
            preview_markdown(df),
            "",
            "## 关键发现",
            "",
            "\n".join(f"- {item}" for item in findings),
            "",
            "## 统计计算结果",
            "",
            "\n".join(stat_lines),
            "",
            "## 趋势识别与对比分析",
            "",
            "\n".join(f"- {item}" for item in trends),
            "",
            "## 结论与建议",
            "",
            "- 若该表用于月度对比，可重点关注波动幅度最大的指标，并结合业务背景解释变化原因。",
            "- 若该表用于展示看板，建议优先把数值列均值、最大值、最小值和趋势方向做成图表。",
            "- 当前报告为结构化快速分析版，适合作为前端预览和进一步深度分析的基础。",
        ]
    ).strip() + "\n"


def analyze_excel_file(file_path: Path) -> dict:
    sheets = read_excel_file(file_path)
    if not sheets:
        raise RuntimeError("Excel 文件中没有可分析的工作表。")

    first_sheet_name = next(iter(sheets.keys()))
    df = sheets[first_sheet_name]
    data_records = df.to_dict(orient="records")
    sample_data = json.dumps({"完整数据": data_records}, ensure_ascii=False, indent=2)

    cleaner = DataCleaningTool()
    clean_result_text = cleaner.run({"data_json": sample_data, "drop_na": False})
    if clean_result_text.startswith("错误") or clean_result_text.startswith("警告") or clean_result_text.startswith("清洗出错"):
        raise RuntimeError(clean_result_text)
    clean_result = json.loads(clean_result_text)

    statistician = DataStatisticsTool()
    stats_result_text = statistician.run({"data_json": json.dumps(clean_result, ensure_ascii=False)})
    if stats_result_text.startswith("错误") or stats_result_text.startswith("统计出错"):
        raise RuntimeError(stats_result_text)
    stats_result = json.loads(stats_result_text)

    markdown_report = build_markdown_report(file_path.name, first_sheet_name, df, clean_result, stats_result)

    summary = {
        "sheet_count": len(sheets),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "sheet_names": list(sheets.keys()),
    }

    return {
        "ok": True,
        "markdown_report": markdown_report,
        "echarts": None,
        "summary": summary,
    }


def scrape_reviews(target_url: str, max_items: int) -> tuple[list[dict[str, str]], Path]:
    scraper = load_module("car_review_scraper_runtime", SCRAPER_PATH, strip_after="class Solution(object):")
    paths = ensure_runtime_dirs()
    browser_path, browser_channel = scraper.detect_local_browser()
    site = scraper.detect_site(target_url, None)
    reviews = scraper.scrape_url(
        url=target_url,
        site=site,
        max_items=max_items,
        max_pages=5,
        scroll_rounds=6,
        pause_seconds=1.5,
        headless=True,
        browser_executable=browser_path,
        browser_channel=browser_channel,
    )
    reviews = [scraper.normalize_review(review) for review in reviews]
    reviews.sort(key=scraper.review_sort_key, reverse=True)
    scraper.write_excel(str(paths["excel"]), [(target_url, reviews)])
    paths["reviews_json"].write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    return reviews, paths["run_dir"]


def analyze_reviews(run_dir: Path) -> tuple[str, Path]:
    analyzer = load_module("car_review_analyzer_runtime", ANALYZER_PATH)
    excel_path = run_dir / "reviews.xlsx"
    report_path = run_dir / "review_analysis_report.md"
    summary_excel_path = run_dir / "review_analysis_summary.xlsx"

    reviews_by_sheet = analyzer.load_reviews_by_sheet(str(excel_path))
    if not reviews_by_sheet:
        raise RuntimeError("没有读取到可分析的评论数据。")

    results = []
    for sheet_name, reviews in reviews_by_sheet.items():
        results.append(analyzer.analyze_sheet(sheet_name, reviews))

    markdown = analyzer.render_markdown(results)
    analyzer.write_text(str(report_path), markdown)
    analyzer.write_summary_excel(str(summary_excel_path), results)
    return markdown, report_path


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 401
    
    if user.status == 0:
        return jsonify({'error': '账号已禁用'}), 401
    
    if password != user.password_hash:
        return jsonify({'error': '密码错误'}), 401
    
    token = generate_token(user)
    dealer_code = user.username if user.role == 'dealer' else None
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'dealerCode': dealer_code
        }
    })


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'dealer')
    dealer_data = data.get('dealer_data', {})
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    if role == 'admin':
        return jsonify({'error': '无权创建管理员账户'}), 403
    
    user = User(
        username=username,
        password_hash=password,
        role=role
    )
    
    db.session.add(user)
    db.session.flush()
    
    if role == 'dealer' and dealer_data:
        dealer = Dealer(
            user_id=user.id,
            dealer_name=dealer_data.get('dealer_name'),
            level=dealer_data.get('level'),
            region=dealer_data.get('region'),
            contact_name=dealer_data.get('contact_name'),
            contact_phone=dealer_data.get('contact_phone'),
            address=dealer_data.get('address')
        )
        db.session.add(dealer)
    
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201


@app.route('/api/users', methods=['GET'])
def get_users():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload or payload['role'] != 'admin':
        return jsonify({'error': '无权限访问'}), 403
    
    users = User.query.all()
    user_list = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
        
        if user.role == 'dealer':
            dealer = Dealer.query.filter_by(user_id=user.id).first()
            if dealer:
                province = ''
                city = ''
                if dealer.region:
                    if '/' in dealer.region:
                        parts = dealer.region.split('/')
                        province = parts[0] if len(parts) > 0 else ''
                        city = parts[1] if len(parts) > 1 else ''
                    else:
                        import re
                        match = re.match(r'^(.*?[省自治区])(.+)$', dealer.region)
                        if match:
                            province = match.group(1)
                            city = match.group(2)
                        else:
                            province = dealer.region
                
                user_data['dealer'] = {
                    'id': dealer.id,
                    'dealer_name': dealer.dealer_name,
                    'level': dealer.level,
                    'region': dealer.region,
                    'province': province,
                    'city': city,
                    'contact_name': dealer.contact_name,
                    'contact_phone': dealer.contact_phone,
                    'address': dealer.address
                }
        
        user_list.append(user_data)
    
    return jsonify(user_list)


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
        
        if user.role == 'dealer':
            dealer = Dealer.query.filter_by(user_id=user.id).first()
            if dealer:
                province = ''
                city = ''
                if dealer.region:
                    parts = dealer.region.split('/')
                    if len(parts) >= 2:
                        province = parts[0]
                        city = parts[1]
                    else:
                        province = dealer.region
                
                user_data['dealer'] = {
                    'id': dealer.id,
                    'dealer_name': dealer.dealer_name,
                    'level': dealer.level,
                    'region': dealer.region,
                    'province': province,
                    'city': city,
                    'contact_name': dealer.contact_name,
                    'contact_phone': dealer.contact_phone,
                    'address': dealer.address
                }
        
        return jsonify(user_data)
    except Exception as e:
        print(f'获取用户信息失败: {str(e)}')
        return jsonify({'error': f'获取失败: {str(e)}'}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload:
            return jsonify({'error': '无效的令牌'}), 401
        
        if payload['role'] != 'admin' and payload['user_id'] != user_id:
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role == 'admin' and payload['role'] != 'admin':
            return jsonify({'error': '不能修改管理员账户'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        if payload['role'] != 'admin':
            if 'password' in data:
                user.password_hash = data['password']
        else:
            if 'password' in data:
                user.password_hash = data['password']
            if 'status' in data:
                user.status = data['status']
        
        db.session.commit()
        return jsonify({'message': '用户信息更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'更新用户信息失败: {str(e)}')
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role == 'admin':
            return jsonify({'error': '不能删除管理员账户'}), 403
        
        dealer = Dealer.query.filter_by(user_id=user_id).first()
        if dealer:
            db.session.delete(dealer)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'删除用户失败: {str(e)}')
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@app.route('/api/dealers/<int:user_id>', methods=['GET'])
def get_dealer_info(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload:
        return jsonify({'error': '无效的令牌'}), 401
    
    if payload['role'] != 'admin' and payload['user_id'] != user_id:
        return jsonify({'error': '无权限访问'}), 403
    
    dealer = Dealer.query.filter_by(user_id=user_id).first()
    if not dealer:
        return jsonify({
            'id': None,
            'user_id': user_id,
            'dealer_name': '',
            'level': '',
            'province': '',
            'city': '',
            'contact_name': '',
            'contact_phone': '',
            'address': '',
            'created_at': None,
            'updated_at': None
        })
    
    province = ''
    city = ''
    if dealer.region:
        parts = dealer.region.split('/')
        if len(parts) >= 2:
            province = parts[0]
            city = parts[1]
        else:
            province = dealer.region
    
    return jsonify({
        'id': dealer.id,
        'user_id': dealer.user_id,
        'dealer_name': dealer.dealer_name,
        'level': dealer.level,
        'province': province,
        'city': city,
        'contact_name': dealer.contact_name,
        'contact_phone': dealer.contact_phone,
        'address': dealer.address,
        'created_at': dealer.created_at,
        'updated_at': dealer.updated_at
    })


@app.route('/api/dealers/<int:user_id>', methods=['PUT'])
def update_dealer_info(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload:
        return jsonify({'error': '无效的令牌'}), 401
    
    if payload['role'] != 'admin' and payload['user_id'] != user_id:
        return jsonify({'error': '无权限修改'}), 403
    
    data = request.get_json()
    dealer = Dealer.query.filter_by(user_id=user_id).first()
    
    if not dealer:
        region = ''
        if 'province' in data and 'city' in data:
            province = data.get('province', '')
            city = data.get('city', '')
            region = f"{province}{city}" if province and city else (province or city or '')
        else:
            region = data.get('region', '')
        
        dealer = Dealer(
            user_id=user_id,
            dealer_name=data.get('dealer_name', ''),
            level=data.get('level', ''),
            region=region,
            contact_name=data.get('contact_name', ''),
            contact_phone=data.get('contact_phone', ''),
            address=data.get('address', '')
        )
        db.session.add(dealer)
        db.session.commit()
        return jsonify({'message': '经销商信息创建成功'}), 201
    
    if 'dealer_name' in data:
        dealer.dealer_name = data['dealer_name']
    if 'level' in data:
        dealer.level = data['level']
    
    if 'province' in data or 'city' in data:
        province = data.get('province', '')
        city = data.get('city', '')
        dealer.region = f"{province}{city}" if province and city else (province or city or '')
    elif 'region' in data:
        dealer.region = data['region']
    
    if 'contact_name' in data:
        dealer.contact_name = data['contact_name']
    if 'contact_phone' in data:
        dealer.contact_phone = data['contact_phone']
    if 'address' in data:
        dealer.address = data['address']
    
    db.session.commit()
    
    return jsonify({'message': '经销商信息更新成功'}), 200


@app.route('/api/dealers', methods=['POST'])
def add_dealer():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        required_fields = ['username', 'password', 'dealer_name', 'level', 'contact_name', 'contact_phone', 'address']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field}不能为空'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        region = ''
        if 'province' in data and 'city' in data:
            province = data.get('province', '')
            city = data.get('city', '')
            region = f"{province}{city}" if province and city else (province or city or '')
        else:
            region = data.get('region', '')
        
        user = User(
            username=data['username'],
            password_hash=data['password'],
            role='dealer'
        )
        
        db.session.add(user)
        db.session.flush()
        
        dealer = Dealer(
            user_id=user.id,
            dealer_name=data['dealer_name'],
            level=data['level'],
            region=region,
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            address=data['address']
        )
        
        db.session.add(dealer)
        db.session.commit()
        
        return jsonify({'message': '经销商添加成功'}), 201
    except Exception as e:
        db.session.rollback()
        print(f'添加经销商失败: {str(e)}')
        return jsonify({'error': f'添加失败: {str(e)}'}), 500


@app.route('/api/dealers/list', methods=['GET'])
def get_dealers_list():
    try:
        dealers = []
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        dealers_query = db.session.execute(db.text("""
            SELECT d.id, d.user_id, d.dealer_name, d.level, d.region, 
                   d.contact_name, d.contact_phone, d.address, u.status
            FROM dealers d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.id
        """))
        
        for row in dealers_query:
            dealer_code = row[2]
            info = dealer_info_map.get(dealer_code, {'province': '', 'city': ''})
            dealers.append({
                'id': row[0],
                'user_id': row[1],
                'dealer_code': dealer_code,
                'dealer_name': row[2],
                'level': row[3] or '',
                'region': row[4] or '',
                'province': info['province'],
                'city': info['city'],
                'contact_name': row[5] or '',
                'contact_phone': row[6] or '',
                'address': row[7] or '',
                'status': row[8] if row[8] is not None else 1
            })
        
        return jsonify({
            'success': True,
            'dealers': dealers
        }), 200
        
    except Exception as e:
        print(f'获取经销商列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/prediction/history', methods=['GET'])
def get_prediction_history():
    try:
        token = request.headers.get('Authorization')
        current_user = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            current_user = verify_token(token)
        
        query = PredictionHistory.query
        if current_user and current_user.get('role') == 'dealer':
            dealer_code = current_user.get('username')
            query = query.filter_by(dealer_code=dealer_code)
        
        histories = query.order_by(PredictionHistory.created_at.desc()).all()
        
        history_list = []
        for history in histories:
            history_list.append({
                'id': history.id,
                'dealer_code': history.dealer_code,
                'dimension': history.dimension,
                'change_percentage': history.change_percentage,
                'base_year': history.base_year,
                'base_month': history.base_month,
                'target_year': history.target_year,
                'target_month': history.target_month,
                'predicted_sales': history.predicted_sales,
                'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'data': history_list
        }), 200
        
    except Exception as e:
        print(f'获取历史记录失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/prediction/history/<int:id>', methods=['GET'])
def get_prediction_history_detail(id):
    try:
        history = PredictionHistory.query.get(id)
        if not history:
            return jsonify({'success': False, 'message': '历史记录不存在'}), 404
        
        result = {
            'id': history.id,
            'dealer_code': history.dealer_code,
            'dimension': history.dimension,
            'change_percentage': history.change_percentage,
            'base_year': history.base_year,
            'base_month': history.base_month,
            'target_year': history.target_year,
            'target_month': history.target_month,
            'predicted_sales': history.predicted_sales,
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取历史记录详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/prediction/history', methods=['POST'])
def save_prediction_history():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        print('接收到的保存历史记录数据:', data)
        
        history = PredictionHistory(
            dealer_code=data.get('dealer_code'),
            dimension=data.get('dimension'),
            change_percentage=data.get('change_percentage'),
            base_year=data.get('base_year', 2024),
            base_month=data.get('base_month'),
            target_year=data.get('target_year', 2024),
            target_month=data.get('target_month'),
            predicted_sales=data.get('predicted_sales')
        )
        
        db.session.add(history)
        db.session.commit()
        
        print('历史记录保存成功:', history.id)
        
        return jsonify({
            'success': True,
            'message': '历史记录保存成功',
            'data': {
                'id': history.id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'保存历史记录失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@app.route('/api/analysis-reports', methods=['POST'])
def save_analysis_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        print('接收到的保存分析报告数据:', data)
        
        report = AnalysisReport(
            username=data.get('username'),
            dealer_code=data.get('dealer_code'),
            selected_cards=data.get('selected_cards'),
            report_content=data.get('report_content')
        )
        
        db.session.add(report)
        db.session.commit()
        
        print('分析报告保存成功:', report.id)
        
        return jsonify({
            'success': True,
            'message': '分析报告保存成功',
            'data': {
                'id': report.id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'保存分析报告失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@app.route('/api/analysis-reports', methods=['GET'])
def get_analysis_reports():
    try:
        username = request.args.get('username')
        
        query = AnalysisReport.query
        if username:
            query = query.filter_by(username=username)
        
        reports = query.order_by(AnalysisReport.report_date.desc()).all()
        
        report_list = []
        for report in reports:
            report_list.append({
                'id': report.id,
                'username': report.username,
                'dealer_code': report.dealer_code,
                'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
                'selected_cards': report.selected_cards,
                'report_content': report.report_content
            })
        
        return jsonify({
            'success': True,
            'data': report_list
        }), 200
        
    except Exception as e:
        print(f'获取分析报告列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/analysis-reports/<int:id>', methods=['GET'])
def get_analysis_report_detail(id):
    try:
        report = AnalysisReport.query.get(id)
        if not report:
            return jsonify({'success': False, 'message': '分析报告不存在'}), 404
        
        result = {
            'id': report.id,
            'username': report.username,
            'dealer_code': report.dealer_code,
            'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
            'selected_cards': report.selected_cards,
            'report_content': report.report_content
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取分析报告详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/analysis-reports/<int:id>', methods=['DELETE'])
def delete_analysis_report(id):
    try:
        report = AnalysisReport.query.get(id)
        if not report:
            return jsonify({'success': False, 'message': '分析报告不存在'}), 404
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '分析报告删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f'删除分析报告失败: {str(e)}')
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/api/policies', methods=['GET'])
def get_policies():
    try:
        policies_query = ConsumptionPolicy.query.all()
        
        policies = []
        for policy in policies_query:
            policy_data = {
                '政策名称': policy.policy_name,
                '省/直辖市/自治区': policy.province or '',
                '地级市/自治州': policy.city or '',
                '区/县/自治县/县级市': policy.district or '',
                '政策分类': policy.policy_category or '',
                '执行时间': policy.start_date or '',
                '结束时间': policy.end_date or '',
                '政策主要内容': policy.policy_content or '',
                '原文链接': policy.source_link or ''
            }
            policies.append(policy_data)
        
        return jsonify(policies), 200
    except Exception as e:
        print(f'获取政策数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': f'获取失败: {str(e)}'}), 500


@app.route('/api/comments', methods=['GET'])
def get_comments():
    try:
        comments_query = TestDriveComment.query.filter(
            TestDriveComment.comment_content.isnot(None),
            TestDriveComment.comment_content != ''
        ).all()
        
        comments = []
        for comment in comments_query:
            score_value = float(comment.overall_score) if comment.overall_score else 3.0
            
            if score_value > 3:
                sentiment = 'positive'
            elif score_value < 3:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            comments.append({
                'content': str(comment.comment_content).strip(),
                'score': score_value,
                'sentiment': sentiment,
                'dealer_code': comment.dealer_code or '',
                'dealer_name': comment.dealer_name or '',
                'car_model': comment.car_model or '',
                'province': comment.province or '',
                'city': comment.city or '',
                'comment_time': comment.comment_time.strftime('%Y-%m-%d %H:%M:%S') if comment.comment_time else ''
            })
        
        print(f'成功从数据库读取 {len(comments)} 条评价')
        return jsonify(comments), 200
    except Exception as e:
        print(f'获取试驾评价失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': f'获取失败: {str(e)}'}), 500


@app.route('/api/wordcloud', methods=['POST'])
def generate_wordcloud():
    try:
        data = request.get_json()
        comments = data.get('comments', [])
        positive_words = data.get('positiveWords', [])
        negative_words = data.get('negativeWords', [])
        neutral_words = data.get('neutralWords', [])
        wordcloud_type = data.get('type', 'all')
        
        if wordcloud_type == 'circular':
            image_base64 = wordcloud_generator.generate_circular_wordcloud(
                positive_words, negative_words, neutral_words,
                width=900, height=600
            )
        else:
            filtered_comments = comments
            if wordcloud_type == 'positive':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'positive']
            elif wordcloud_type == 'negative':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'negative']
            elif wordcloud_type == 'neutral':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'neutral']
            
            image_base64 = wordcloud_generator.generate_wordcloud_for_sentiment(
                filtered_comments, wordcloud_type, width=900, height=550
            )
        
        if image_base64:
            return jsonify({
                'success': True,
                'image': image_base64
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '无法生成词云，数据不足'
            }), 400
            
    except Exception as e:
        print(f'生成词云失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500


@app.get("/api/sales/original")
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


@app.post("/api/sales/predict")
def api_sales_predict():
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
    target_year = _safe_int(payload.get("target_year"), None)
    target_months = _coerce_horizons(payload.get("target_months") or payload.get("horizons"))
    predict_all = bool(payload.get("predict_all"))

    if base_year is not None and base_month is not None:
        try:
            result = _predict_point_single(
                dealer_code,
                dimension,
                change_percentage,
                base_year=base_year,
                base_month=base_month,
            )
            sales_prediction, sales_changes = _sales_predict_payload_from_point_result(result, dealer_data)
            return jsonify({
                "message": "ok",
                "dealer_code": dealer_code,
                "dimension": dimension,
                "change_percentage": change_percentage,
                "base_year": int(base_year),
                "base_month": int(base_month),
                "target_year": int(result["target_year"]),
                "target_month": int(result["target_month"]),
                "point_result": {
                    "scenario": float(result["scenario"]),
                    "baseline": float(result["baseline"]),
                    "delta": float(result["delta"]),
                    "delta_pct": float(result["delta_pct"]),
                },
                "sales_prediction": sales_prediction,
                "sales_changes": sales_changes,
                "original_sales_series": _original_sales_series(dealer_data, base_year),
            })
        except Exception as e:
            traceback.print_exc()
            return jsonify({"message": f"预测失败: {e}"}), 500

    if target_year is None:
        target_year = _infer_default_year(dealer_data)
    if not target_months:
        target_months = list(DEFAULT_QUANTILE_HORIZONS)

    sales_prediction, sales_changes, errors = _predict_point_batch_by_target_months(
        dealer_code,
        dimension,
        change_percentage,
        target_year=int(target_year),
        target_months=target_months,
    )

    return jsonify({
        "message": "ok",
        "dealer_code": dealer_code,
        "dimension": dimension,
        "change_percentage": change_percentage,
        "target_year": int(target_year),
        "target_months": target_months,
        "sales_prediction": sales_prediction,
        "sales_changes": sales_changes,
        "errors": errors,
        "original_sales_series": _original_sales_series(dealer_data, target_year),
    })


@app.post("/api/sales/predict/quantile")
def api_sales_predict_quantile():
    ok, msg = _ensure_ready(require_quantile=True)
    if not ok:
        return jsonify({"message": msg}), 503

    payload = request.get_json(silent=True) or {}
    dealer_code = (payload.get("dealer_code") or "").strip()
    target_year = _safe_int(payload.get("target_year"), None)
    target_months = _coerce_horizons(payload.get("target_months") or payload.get("horizons"))
    quantiles = _coerce_quantiles(payload.get("quantiles"))

    if not dealer_code:
        return jsonify({"message": "缺少 dealer_code"}), 400

    dealer_data = get_dealer_by_code(dealer_code)
    if dealer_data is None:
        return jsonify({"message": "dealer_code 不存在"}), 400

    if target_year is None:
        target_year = _infer_default_year(dealer_data)
    if not target_months:
        target_months = list(DEFAULT_QUANTILE_HORIZONS)

    try:
        quantile_bundle = _get_quantile_bundle()
        result = predict_for_dealer(
            quantile_bundle,
            dealer_data,
            horizons=target_months,
            quantiles=quantiles,
        )

        return jsonify({
            "message": "ok",
            "dealer_code": dealer_code,
            "target_year": int(target_year),
            "target_months": target_months,
            "quantiles": result.get("quantiles"),
            "predictions": result.get("predictions"),
            "original_sales_series": _original_sales_series(dealer_data, target_year),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"分位数预测失败: {e}"}), 500


@app.post("/api/forecast/quantiles")
def api_forecast_quantiles():
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

    horizons = _coerce_horizons(payload.get("horizons", DEFAULT_QUANTILE_HORIZONS))
    quantiles = _coerce_quantiles(payload.get("quantiles", None))
    calib_alpha = _safe_float(payload.get("calib_alpha"), None)

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

    result = {
        "dealer_code": dealer_code,
        "base_year": int(base_year),
        "base_month": int(base_month),
        "meta": {
            "method": "bundle_quantile_forecast",
            "point_model_version": getattr(quantile_bundle, "point_model_version", None),
            "quantile_model_version": getattr(quantile_bundle, "model_version", None),
            "feature_version": getattr(quantile_bundle, "feature_version", None),
            "horizons_supported": getattr(quantile_bundle, "horizons_supported", None),
            "quantiles": quantiles or getattr(quantile_bundle, "quantiles", None),
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
            calib_alpha=calib_alpha,
        )
        if scenario_applied is not None:
            pred["scenario_applied"] = scenario_applied
        result["scenarios"][name] = pred

    return jsonify(convert_numpy(result))


@app.get("/api/dealers")
def api_dealers():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503
    return jsonify({"dealers": _get_dealer_codes()})


@app.get("/api/dealers/<dealer_code>")
def api_dealer_detail(dealer_code: str):
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    dealer_data = get_dealer_by_code(dealer_code)
    if dealer_data is None:
        return jsonify({"message": "dealer_code 不存在"}), 404

    return jsonify({
        "dealer_code": dealer_code,
        "dealer_data": convert_numpy(vars(dealer_data)),
    })


@app.get("/api/years")
def api_years():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503
    return jsonify({"years": _infer_all_years(_get_dealers_raw())})


@app.get("/api/dimensions")
def api_dimensions():
    return jsonify({"dimensions": list(DIMENSIONS)})


@app.get("/api/meta")
def api_meta():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503
    return jsonify(_bundle_meta())


@app.get("/api/radar")
def api_radar():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    dealer_codes_csv = request.args.get("dealer_codes", "")
    dealer_codes = [x.strip() for x in dealer_codes_csv.split(",") if x.strip()]
    if not dealer_codes:
        return jsonify({"message": "缺少 dealer_codes 参数"}), 400

    try:
        img_b64 = plot_dealers_radar(_get_dealers_raw(), dealer_codes)
        scores = dealers_score(_get_dealers_raw(), dealer_codes)
        return jsonify({"image": img_b64, "scores": scores})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"雷达图生成失败: {e}"}), 500


@app.get("/api/wordcloud")
def api_wordcloud():
    ok, msg = _ensure_ready(require_quantile=False)
    if not ok:
        return jsonify({"message": msg}), 503

    dealer_code = (request.args.get("dealer_code") or "").strip()
    if not dealer_code:
        return jsonify({"message": "缺少 dealer_code 参数"}), 400

    try:
        img_b64 = wordcloud_generator(dealer_code)
        return jsonify({"image": img_b64})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"词云生成失败: {e}"}), 500


@app.route("/api/excel-report", methods=["POST", "OPTIONS"])
def api_excel_report():
    if request.method == "OPTIONS":
        return ("", 200)

    if "excel_file" not in request.files:
        return jsonify({"ok": False, "error": "未检测到上传的 Excel 文件。"}), 400

    excel_file = request.files["excel_file"]
    if not excel_file or not excel_file.filename:
        return jsonify({"ok": False, "error": "Excel 文件名为空。"}), 400

    suffix = Path(excel_file.filename).suffix.lower()
    if suffix not in {".xls", ".xlsx"}:
        return jsonify({"ok": False, "error": "仅支持 .xls 或 .xlsx 文件。"}), 400

    temp_dir = AIPLUGIN_RUNTIME_DIR / f"excel_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / excel_file.filename

    try:
        excel_file.save(temp_path)
        analysis_result = analyze_excel_file(temp_path)
        analysis_result["success"] = analysis_result.get("ok", False)
        analysis_result["source_file"] = str(temp_path)
        return jsonify(analysis_result)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def api_analyze():
    if request.method == "OPTIONS":
        return ("", 200)

    payload = request.get_json(silent=True) or {}
    target_url = (payload.get("url") or "").strip()
    max_items = _safe_int(payload.get("max_items"), 20)

    if not target_url:
        return jsonify({"ok": False, "error": "请输入评论页 URL。"}), 400

    try:
        reviews, run_dir = scrape_reviews(target_url, max_items)
        if not reviews:
            return jsonify({"ok": False, "error": "没有爬取到评论，请检查 URL 是否为公开评论页。"}), 400

        markdown, report_path = analyze_reviews(run_dir)

        preview_reviews = []
        for item in reviews[:8]:
            preview_reviews.append({
                "user_name": item.get("user_name", ""),
                "car_name": item.get("car_name", ""),
                "rating": item.get("rating", ""),
                "published_at": item.get("published_at", ""),
                "content": item.get("content", ""),
                "source_url": item.get("source_url", ""),
            })

        return jsonify({
            "ok": True,
            "url": target_url,
            "review_count": len(reviews),
            "preview_reviews": preview_reviews,
            "report_markdown": markdown,
            "report_file": str(report_path),
            "excel_file": str(run_dir / "reviews.xlsx"),
            "summary_excel_file": str(run_dir / "review_analysis_summary.xlsx"),
            "reviews_json_file": str(run_dir / "reviews.json"),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}), 500


@app.route("/api/scrape-reviews", methods=["POST", "OPTIONS"])
def api_scrape_reviews():
    if request.method == "OPTIONS":
        return ("", 200)

    payload = request.get_json(silent=True) or {}
    target_url = (payload.get("target_url") or "").strip()
    max_items = _safe_int(payload.get("max_items"), 20)

    if not target_url:
        return jsonify({"ok": False, "error": "缺少目标 URL。"}), 400

    try:
        reviews, run_dir = scrape_reviews(target_url, max_items)
        return jsonify({
            "ok": True,
            "reviews": reviews,
            "count": len(reviews),
            "run_dir": str(run_dir),
            "excel_path": str(run_dir / "reviews.xlsx"),
            "reviews_json_path": str(run_dir / "reviews.json"),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}), 500


@app.route("/api/analyze-reviews", methods=["POST", "OPTIONS"])
def api_analyze_reviews():
    if request.method == "OPTIONS":
        return ("", 200)

    payload = request.get_json(silent=True) or {}
    run_dir_str = (payload.get("run_dir") or "").strip()

    if not run_dir_str:
        return jsonify({"ok": False, "error": "缺少 run_dir 参数。"}), 400

    run_dir = Path(run_dir_str)
    if not run_dir.exists():
        return jsonify({"ok": False, "error": f"run_dir 不存在: {run_dir}"}), 400

    try:
        markdown, report_path = analyze_reviews(run_dir)
        return jsonify({
            "ok": True,
            "markdown_report": markdown,
            "report_path": str(report_path),
            "summary_excel_path": str(run_dir / "review_analysis_summary.xlsx"),
        })
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}), 500


@app.route("/api/download/<path:filename>", methods=["GET"])
def api_download_file(filename):
    safe_path = AIPLUGIN_RUNTIME_DIR / filename
    if not safe_path.exists():
        return jsonify({"ok": False, "error": "文件不存在"}), 404
    return send_from_directory(safe_path.parent, safe_path.name, as_attachment=True)


AIPLUGIN_STATIC_DIR = Path(__file__).parent / "aiplugin" / "插件"

@app.route("/ai-plugin/<path:filename>", methods=["GET"])
def ai_plugin_static(filename):
    safe_path = AIPLUGIN_STATIC_DIR / filename
    if not safe_path.exists():
        return jsonify({"ok": False, "error": "文件不存在"}), 404
    return send_from_directory(str(AIPLUGIN_STATIC_DIR), filename)


INSIGHT_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-764a502f6eef4b7999800d65212d282f").strip()
INSIGHT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
INSIGHT_MODEL = 'tingwu-automotive-service-insights'
INSIGHT_APP_ID = "tw_bEFSoD4kIq1w"
INSIGHT_MAX_POLL_ATTEMPTS = 30
INSIGHT_POLL_INTERVAL = 5
INSIGHT_OUTPUT_DIR = AIPLUGIN_RUNTIME_DIR / "insight_reports"

# 阿里云 OSS 配置（直接配置，不使用环境变量）
OSS_BUCKET = "my-audio-qc-20260314"
OSS_ENDPOINT = "https://oss-cn-hangzhou.aliyuncs.com"
OSS_ACCESS_KEY_ID = "LTAI5t8ksfxnQp1M2bRAGaKh"
OSS_ACCESS_KEY_SECRET = "51jcEZ18haeWHDmMKbMzmSj5vTuKHP"


def is_audio_file(file_path):
    if not os.path.isfile(file_path):
        return False
    audio_exts = {'.mp3', '.wav', '.pcm', '.aac', '.amr', '.opus', '.speex', '.flac', '.m4a'}
    return Path(file_path).suffix.lower() in audio_exts


def detect_input_type(input_source, hint_type="auto"):
    if hint_type != "auto":
        return hint_type
    if is_audio_file(input_source):
        return "file"
    elif isinstance(input_source, str) and input_source.startswith(("http://", "https://")):
        return "url"
    else:
        return "text"


def download_json_from_oss(oss_url):
    try:
        response = requests.get(oss_url.strip(), timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        return None


def upload_to_oss(local_file_path, oss_bucket, oss_endpoint, oss_access_key_id, oss_access_key_secret, oss_file_key=None):
    try:
        import oss2
        auth = oss2.Auth(oss_access_key_id, oss_access_key_secret)
        bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket)
        if oss_file_key is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(local_file_path)
            oss_file_key = f"tingwu_audio/{timestamp}_{filename}"
        bucket.put_object_from_file(oss_file_key, local_file_path)
        print(f"✅ 文件已上传至 OSS: {oss_file_key}")
        url = bucket.sign_url('GET', oss_file_key, 7 * 24 * 3600)
        return url
    except ImportError:
        print("⚠️ 未安装 oss2 库，请使用：pip install oss2")
        return None
    except Exception as e:
        print(f"❌ OSS 上传失败：{e}")
        return None


def get_audio_url(input_source, input_type):
    if input_type == "text":
        return None
    if input_type == "url":
        return input_source.strip()
    if input_type == "file":
        if not os.path.isfile(input_source):
            print(f"❌ 文件不存在：{input_source}")
            return None
        if not all([OSS_BUCKET, OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET]):
            print("❌ 未配置 OSS，请在代码中设置 OSS_BUCKET, OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET")
            return None
        return upload_to_oss(
            local_file_path=input_source,
            oss_bucket=OSS_BUCKET,
            oss_endpoint=OSS_ENDPOINT,
            oss_access_key_id=OSS_ACCESS_KEY_ID,
            oss_access_key_secret=OSS_ACCESS_KEY_SECRET
        )
    return None


def poll_task_result(api_key, base_url, data_id, model):
    for attempt in range(INSIGHT_MAX_POLL_ATTEMPTS):
        print(f"🔄 轮询 {attempt + 1}/{INSIGHT_MAX_POLL_ATTEMPTS}...")
        try:
            from dashscope.multimodal.tingwu.tingwu import TingWu
            resp = TingWu.call(
                model=model,
                user_defined_input={"task": "getTask", "dataId": data_id},
                api_key=api_key,
                base_address=base_url,
            )
            output = resp.get("output", {})
            status = output.get("status")
            if status == 0:
                print("✅ 任务完成！")
                return output
            elif status == 2:
                print(f"❌ 任务失败：{output.get('errorCode')}")
                return None
        except Exception as e:
            print(f"轮询异常: {e}")
        time.sleep(INSIGHT_POLL_INTERVAL)
    print("⏰ 轮询超时")
    return None


def parse_insights(insights_data):
    if not insights_data:
        return [], []
    items = insights_data if isinstance(insights_data, list) else insights_data.get("serviceInsights", [])
    matched = [i for i in items if isinstance(i, dict) and i.get("matched") is True]
    unmatched = [i for i in items if isinstance(i, dict) and i.get("matched") is not True]
    return matched, unmatched


def format_transcription_md(trans_data, max_show=3):
    if not trans_data:
        return "> ⚠️ 无转写内容"
    paragraphs = trans_data if isinstance(trans_data, list) else trans_data.get("paragraphs", [])
    if not paragraphs:
        return "> ⚠️ 无转写内容"
    lines = []
    for p in paragraphs[:max_show]:
        if not isinstance(p, dict):
            continue
        speaker = p.get("speakerId", "?")
        words = p.get("words", [])
        text = " ".join([w.get("text", " ") if isinstance(w, dict) else str(w) for w in words])
        lines.append(f"**说话人{speaker}**: {text}")
    if len(paragraphs) > max_show:
        lines.append(f"\n> *... 还有 {len(paragraphs) - max_show} 段*")
    return "\n\n".join(lines)


def format_insights_table_md(matched, unmatched, show_unmatched_limit=10):
    lines = []
    lines.append("### ✅ 命中项（符合规范）")
    if matched:
        lines.append("| 序号 | 质检项 | 说明 | 得分 |")
        lines.append("|------|--------|------|------|")
        for i, item in enumerate(matched, 1):
            title = item.get("title", "未知项")
            remarks = item.get("remarks", " ").replace("|", "\\|")[:80]
            score = item.get("score", "-")
            lines.append(f"| {i} | {title} | {remarks}... | {score} |")
    else:
        lines.append("> ⚠️ 本次对话无命中质检项")
    lines.append("")
    lines.append("### ❌ 未命中项（待改进）")
    if unmatched:
        lines.append(f"> 共 {len(unmatched)} 项未命中，以下是前 {min(show_unmatched_limit, len(unmatched))} 项：")
        lines.append("")
        lines.append("| 序号 | 质检项 | 说明 |")
        lines.append("|------|--------|------|")
        for i, item in enumerate(unmatched[:show_unmatched_limit], 1):
            title = item.get("title", "未知项")
            remarks = item.get("remarks", " ").replace("|", "\\|")[:60]
            lines.append(f"| {i} | {title} | {remarks}... |")
        if len(unmatched) > show_unmatched_limit:
            lines.append(f"\n> *... 还有 {len(unmatched) - show_unmatched_limit} 项*")
    else:
        lines.append("> 🎉 全部质检项均命中！")
    return "\n".join(lines)


def format_sale_summary_md(sale_data):
    if not sale_data:
        return "> ⚠️ 无销售分析数据"
    if isinstance(sale_data, dict):
        matched = sale_data.get("matchedSum", 0)
        missed = sale_data.get("missedSum", 0)
        total = matched + missed
        rate = f"{matched / total * 100:.1f}%" if total > 0 else "N/A"
        bar_len = 20
        filled = int(matched / total * bar_len) if total > 0 else 0
        progress = "█" * filled + "░" * (bar_len - filled)
        return f"""| 指标 | 数值 |
| ---|---|
| ✅ 命中项 | {matched} |
| ❌ 未命中项 | {missed} |
| 📊 总计 | {total} |
| 📈 完成率 | {rate} |
进度可视化：`{progress}` {rate}"""
    elif isinstance(sale_data, list):
        return f"> 📋 销售分析记录：{len(sale_data)} 条"
    return "> ⚠️ 数据格式异常"


def generate_insight_markdown_report(trans_data, matched, unmatched, sale_data, data_id, input_info=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_items = len(matched) + len(unmatched)
    hit_rate = f"{len(matched) / total_items * 100:.1f}%" if total_items > 0 else "0%"
    input_line = ""
    if input_info:
        input_line = f"> **输入类型**: {input_info.get('type')}  \n> **输入源**: `{input_info.get('source', 'N/A')[:100]}`  \n"
    report = f"""# 🚗 汽车服务质检分析报告
任务 ID: `{data_id}`  {input_line}> 生成时间：{timestamp}  \n> 分析模型：{INSIGHT_MODEL}

## 📋 报告摘要
| 指标 | 数值 |
| ---|---|
| ✅ 命中项 | {len(matched)} |
| ❌ 未命中项 | {len(unmatched)} |
| 📊 总质检项 | {total_items} |
| 📈 命中率 | {hit_rate} |

## 📝 转写内容预览
{format_transcription_md(trans_data)}

## 🔍 质检详情
{format_insights_table_md(matched, unmatched)}

## 💰 销售分析
{format_sale_summary_md(sale_data)}

---
*报告由 AI 智能分析系统自动生成*
"""
    return report


def analyze_insight_internal(input_source, input_type="auto"):
    print("🚀 开始汽车服务质检分析...")
    try:
        from dashscope.multimodal.tingwu.tingwu import TingWu
    except ImportError:
        print("❌ 未安装 dashscope 库")
        return None
    
    detected_type = detect_input_type(input_source, input_type)
    print(f"📥 输入类型：{detected_type}")

    if detected_type == "text":
        print("📝 使用文本输入模式")
        text_content = input_source.strip()
        has_role_marker = any(marker in text_content for marker in ['销售', '客户', '顾问', '用户', '客服', '坐席'])
        if not has_role_marker:
            text_content = f"销售：{text_content}"
            print("  已自动添加角色标识")
        task_input = {
            "appId": INSIGHT_APP_ID,
            "text": text_content,
            "task": "createTask"
        }
        input_info = {"type": "text", "source": text_content[:100] + "..." if len(text_content) > 100 else text_content}
    else:
        print(f"🎵 使用音频输入模式 ({detected_type})")
        audio_url = get_audio_url(input_source, detected_type)
        if not audio_url:
            return {"error": "无法获取音频文件URL，请检查OSS配置。需要设置环境变量：OSS_BUCKET, OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET"}
        task_input = {
            "appId": INSIGHT_APP_ID,
            "fileUrl": audio_url,
            "task": "createTask"
        }
        input_info = {"type": detected_type, "source": input_source}

    create_resp = TingWu.call(
        model=INSIGHT_MODEL,
        user_defined_input=task_input,
        api_key=INSIGHT_API_KEY,
        base_address=INSIGHT_BASE_URL,
    )

    if create_resp.get("status_code") != 200:
        print(f"❌ 创建失败：{create_resp}")
        return None

    data_id = create_resp.get("output", {}).get("dataId")
    if not data_id:
        print(f"❌ 无 dataId: {create_resp}")
        return None

    print(f"✅ 任务创建：{data_id}")

    output = poll_task_result(INSIGHT_API_KEY, INSIGHT_BASE_URL, data_id, INSIGHT_MODEL)
    if not output:
        return None

    results = {}
    for key, name in [
        ("transcriptionPath", "转写"),
        ("serviceInsightsPath", "质检"),
        ("saleInsightsPath", "销售")
    ]:
        url = output.get(key)
        if url:
            print(f"  📥 {name}...")
            results[key] = download_json_from_oss(url)

    trans = results.get("transcriptionPath")
    matched, unmatched = parse_insights(results.get("serviceInsightsPath"))
    sale = results.get("saleInsightsPath")

    print(f"✅ 命中: {len(matched)}, 未命中: {len(unmatched)}")

    print("\n📝 生成 Markdown 报告...")
    md_content = generate_insight_markdown_report(trans, matched, unmatched, sale, data_id, input_info)
    
    INSIGHT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_file = INSIGHT_OUTPUT_DIR / f"auto_service_report_{data_id}.md"
    md_file.write_text(md_content, encoding='utf-8')
    print(f"💾 报告已保存：{md_file}")

    json_file = INSIGHT_OUTPUT_DIR / f"data_{data_id}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "transcription": trans,
            "matched": matched,
            "unmatched": unmatched,
            "sale": sale,
            "input_info": input_info
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 原始数据已保存：{json_file}")

    return {
        "dataId": data_id,
        "input_type": detected_type,
        "input_source": input_source,
        "matched": matched,
        "unmatched": unmatched,
        "report_md": str(md_file),
        "data_json": str(json_file)
    }


@app.route('/api/insight-analyze', methods=['POST', 'OPTIONS'])
def api_insight_analyze():
    if request.method == 'OPTIONS':
        return ('', 200)
    
    try:
        input_type = request.form.get('input_type', 'text')

        if input_type == 'text':
            text_content = request.form.get('text_content', '')
            if not text_content.strip():
                return jsonify({'ok': False, 'error': '文本内容不能为空'}), 400
            result = analyze_insight_internal(text_content, 'text')
        elif input_type == 'file':
            if 'audio_file' not in request.files:
                return jsonify({'ok': False, 'error': '未找到音频文件'}), 400
            audio_file = request.files['audio_file']
            temp_dir = AIPLUGIN_RUNTIME_DIR / "temp_audio"
            temp_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file_path = temp_dir / f"{timestamp}_{audio_file.filename}"
            audio_file.save(temp_file_path)
            try:
                result = analyze_insight_internal(str(temp_file_path), 'file')
            finally:
                if temp_file_path.exists():
                    temp_file_path.unlink()
        else:
            return jsonify({'ok': False, 'error': '不支持的输入类型'}), 400

        if result:
            if result.get('error'):
                return jsonify({'ok': False, 'error': result['error']}), 400
            report_content = ""
            if os.path.exists(result['report_md']):
                with open(result['report_md'], 'r', encoding='utf-8') as f:
                    report_content = f.read()

            return jsonify({
                'ok': True,
                'success': True,
                'dataId': result.get('dataId'),
                'summary': {
                    'total_items': len(result.get('matched', [])) + len(result.get('unmatched', [])),
                    'matched': len(result.get('matched', [])),
                    'unmatched': len(result.get('unmatched', [])),
                    'hit_rate': f"{len(result.get('matched', [])) / (len(result.get('matched', [])) + len(result.get('unmatched', []))) * 100:.1f}%" if (len(result.get('matched', [])) + len(result.get('unmatched', []))) > 0 else "0%"
                },
                'markdown_report': report_content,
                'report_file': result.get('report_md'),
                'data_json': result.get('data_json')
            })
        else:
            return jsonify({'ok': False, 'error': '分析失败，请检查输入内容或稍后重试'}), 500

    except Exception as e:
        print(f"❌ API 分析错误：{e}")
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/insight-report/<report_id>', methods=['GET'])
def api_get_insight_report(report_id):
    try:
        report_path = INSIGHT_OUTPUT_DIR / f"auto_service_report_{report_id}.md"
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'ok': True, 'content': content})
        else:
            return jsonify({'ok': False, 'error': '报告不存在'}), 404
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/dashboard/years', methods=['GET'])
def get_available_years():
    try:
        years = db.session.query(MonthlyMetrics11d.stat_year).distinct().order_by(MonthlyMetrics11d.stat_year).all()
        year_list = [y[0] for y in years]
        return jsonify({
            'success': True,
            'data': year_list
        }), 200
    except Exception as e:
        print(f'获取可用年份失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        year = request.args.get('year', type=int)
        dealer_code = request.args.get('dealer_code', type=str)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        evaluation_map = {}
        if year == 2024:
            try:
                eval_result = db.session.execute(db.text("""
                    SELECT dealer_code, 
                           evaluation_score_m01, evaluation_score_m02, evaluation_score_m03,
                           evaluation_score_m04, evaluation_score_m05, evaluation_score_m06,
                           evaluation_score_m07, evaluation_score_m08, evaluation_score_m09,
                           evaluation_score_m10
                    FROM radar_source_2024
                """))
                for row in eval_result:
                    evaluation_map[row[0]] = {
                        1: float(row[1]) if row[1] else None,
                        2: float(row[2]) if row[2] else None,
                        3: float(row[3]) if row[3] else None,
                        4: float(row[4]) if row[4] else None,
                        5: float(row[5]) if row[5] else None,
                        6: float(row[6]) if row[6] else None,
                        7: float(row[7]) if row[7] else None,
                        8: float(row[8]) if row[8] else None,
                        9: float(row[9]) if row[9] else None,
                        10: float(row[10]) if row[10] else None,
                    }
            except:
                pass
        
        query = MonthlyMetrics11d.query
        if year:
            query = query.filter(MonthlyMetrics11d.stat_year == year)
        if dealer_code:
            query = query.filter(MonthlyMetrics11d.dealer_code == dealer_code)
        
        records = query.order_by(MonthlyMetrics11d.dealer_code, MonthlyMetrics11d.stat_year, MonthlyMetrics11d.stat_month).all()
        
        dealer_data_map = {}
        for record in records:
            dc = record.dealer_code
            if dc not in dealer_data_map:
                info = dealer_info_map.get(dc, {'province': '', 'fed_level': ''})
                dealer_data_map[dc] = {
                    '经销商代码': dc,
                    '省份': info['province'],
                    '销售FED级别': info['fed_level']
                }
            
            month = record.stat_month
            dealer_data_map[dc][f'{month}月销量'] = float(record.sales) if record.sales else None
            dealer_data_map[dc][f'{month}月客流量'] = float(record.customer_flow) if record.customer_flow else None
            dealer_data_map[dc][f'{month}月潜客量'] = float(record.potential_customers) if record.potential_customers else None
            dealer_data_map[dc][f'{month}月线索量'] = float(record.leads) if record.leads else None
            dealer_data_map[dc][f'{month}月成交率'] = float(record.success_rate) if record.success_rate else None
            dealer_data_map[dc][f'{month}月战败率'] = float(record.defeat_rate) if record.defeat_rate else None
            dealer_data_map[dc][f'{month}月成交响应时间'] = float(record.success_response_time) if record.success_response_time else None
            dealer_data_map[dc][f'{month}月战败响应时间'] = float(record.defeat_response_time) if record.defeat_response_time else None
            dealer_data_map[dc][f'{month}月政策'] = float(record.policy) if record.policy else None
            dealer_data_map[dc][f'{month}月GSEV'] = float(record.gsev) if record.gsev else None
            dealer_data_map[dc][f'{month}月试驾数'] = float(record.test_drives) if record.test_drives else None
            
            if dc in evaluation_map and month in evaluation_map[dc]:
                eval_score = evaluation_map[dc][month]
                dealer_data_map[dc][f'{month}月评价分'] = eval_score
                if eval_score:
                    good_percent = (eval_score / 5.0) * 100
                    bad_percent = 100 - good_percent
                    dealer_data_map[dc][f'{month}月好评率'] = round(good_percent, 1)
                    dealer_data_map[dc][f'{month}月差评率'] = round(bad_percent, 1)
        
        return jsonify({
            'success': True,
            'data': list(dealer_data_map.values())
        }), 200
        
    except Exception as e:
        print(f'获取仪表盘数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/five-forces/radar', methods=['GET'])
def get_five_forces_radar():
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        dealer_code = request.args.get('dealer_code', type=str)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        query = MonthlyRadarScores.query
        if year:
            query = query.filter(MonthlyRadarScores.stat_year == year)
        if month:
            query = query.filter(MonthlyRadarScores.stat_month == month)
        if dealer_code:
            query = query.filter(MonthlyRadarScores.dealer_code == dealer_code)
        
        records = query.order_by(MonthlyRadarScores.dealer_code, MonthlyRadarScores.stat_year, MonthlyRadarScores.stat_month).all()
        
        result = []
        for record in records:
            info = dealer_info_map.get(record.dealer_code, {'province': '', 'fed_level': ''})
            result.append({
                '经销商代码': record.dealer_code,
                '省份': info['province'],
                '年份': record.stat_year,
                '月份': record.stat_month,
                '传播获客力': float(record.spread_force) if record.spread_force else None,
                '体验力': float(record.experience_force) if record.experience_force else None,
                '转化力': float(record.conversion_force) if record.conversion_force else None,
                '服务力': float(record.service_force) if record.service_force else None,
                '经营力': float(record.operation_force) if record.operation_force else None
            })
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取五力雷达数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/five-forces/years', methods=['GET'])
def get_radar_available_years():
    try:
        years = db.session.query(MonthlyRadarScores.stat_year).distinct().order_by(MonthlyRadarScores.stat_year).all()
        year_list = [y[0] for y in years]
        return jsonify({
            'success': True,
            'data': year_list
        }), 200
    except Exception as e:
        print(f'获取雷达可用年份失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/dealer/yearly-data', methods=['GET'])
def get_dealer_yearly_data():
    try:
        dealer_code = request.args.get('dealer_code', type=str, default='')
        year = request.args.get('year', type=int, default=2024)
        
        if not dealer_code:
            return jsonify({'success': False, 'message': '缺少经销商代码'}), 400
        
        dealer_info = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info WHERE dealer_code = :code"), {'code': dealer_code})
            row = dealer_info_result.fetchone()
            if row:
                dealer_info = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_records = MonthlyRadarScores.query.filter(
            MonthlyRadarScores.dealer_code == dealer_code,
            MonthlyRadarScores.stat_year == year
        ).all()
        
        if not radar_records:
            return jsonify({
                'success': True,
                'data': {
                    'dealer_code': dealer_code,
                    'province': dealer_info.get('province', ''),
                    'avg_score': 0,
                    'radar_avg': {},
                    'monthly_avg': {}
                }
            }), 200
        
        spread_forces = [float(r.spread_force or 0) for r in radar_records]
        experience_forces = [float(r.experience_force or 0) for r in radar_records]
        conversion_forces = [float(r.conversion_force or 0) for r in radar_records]
        service_forces = [float(r.service_force or 0) for r in radar_records]
        operation_forces = [float(r.operation_force or 0) for r in radar_records]
        
        radar_avg = {
            '传播获客力': round(sum(spread_forces) / len(spread_forces), 2) if spread_forces else 0,
            '体验力': round(sum(experience_forces) / len(experience_forces), 2) if experience_forces else 0,
            '转化力': round(sum(conversion_forces) / len(conversion_forces), 2) if conversion_forces else 0,
            '服务力': round(sum(service_forces) / len(service_forces), 2) if service_forces else 0,
            '经营力': round(sum(operation_forces) / len(operation_forces), 2) if operation_forces else 0
        }
        
        total_scores = []
        for r in radar_records:
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + \
                    float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + \
                    float(r.operation_force or 0) * 0.1
            total_scores.append(total)
        avg_score = round(sum(total_scores) / len(total_scores), 2) if total_scores else 0
        
        metrics_records = MonthlyMetrics11d.query.filter(
            MonthlyMetrics11d.dealer_code == dealer_code,
            MonthlyMetrics11d.stat_year == year
        ).order_by(MonthlyMetrics11d.stat_month).all()
        
        monthly_avg = {}
        for r in metrics_records:
            month = r.stat_month
            monthly_avg[month] = {
                '销量': round(float(r.sales or 0), 2),
                '客流量': round(float(r.customer_flow or 0), 2),
                '线索量': round(float(r.leads or 0), 2),
                '潜客量': round(float(r.potential_customers or 0), 2)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'dealer_code': dealer_code,
                'province': dealer_info.get('province', ''),
                'city': dealer_info.get('city', ''),
                'avg_score': avg_score,
                'radar_avg': radar_avg,
                'monthly_avg': monthly_avg
            }
        }), 200
        
    except Exception as e:
        print(f'获取经销商年度数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


PROVINCE_REGION_MAP = {
    '辽宁省': '东北',
    '山东省': '华东',
    '湖北省': '华中',
    '广东省': '华南',
    '广西壮族自治区': '华南'
}


@app.route('/api/index/overview', methods=['GET'])
def get_index_overview():
    try:
        year = request.args.get('year', type=int, default=2024)
        province = request.args.get('province', type=str, default='')
        city = request.args.get('city', type=str, default='')
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        if province:
            radar_records = [r for r in radar_records if dealer_info_map.get(r.dealer_code, {}).get('province', '') == province]
        if city:
            radar_records = [r for r in radar_records if dealer_info_map.get(r.dealer_code, {}).get('city', '') == city or 
                             (dealer_info_map.get(r.dealer_code, {}).get('city', '') and dealer_info_map.get(r.dealer_code, {}).get('city', '') in city) or
                             (city and city in dealer_info_map.get(r.dealer_code, {}).get('city', ''))]
        
        avg_spread = sum(float(r.spread_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_experience = sum(float(r.experience_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_conversion = sum(float(r.conversion_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_service = sum(float(r.service_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_operation = sum(float(r.operation_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        
        radar_avg = {
            '传播获客力': round(avg_spread, 2),
            '体验力': round(avg_experience, 2),
            '转化力': round(avg_conversion, 2),
            '服务力': round(avg_service, 2),
            '经营力': round(avg_operation, 2)
        }
        
        metrics_query = MonthlyMetrics11d.query.filter(MonthlyMetrics11d.stat_year == year)
        metrics_records = metrics_query.all()
        
        if province:
            metrics_records = [r for r in metrics_records if dealer_info_map.get(r.dealer_code, {}).get('province', '') == province]
        if city:
            metrics_records = [r for r in metrics_records if dealer_info_map.get(r.dealer_code, {}).get('city', '') == city or 
                             (dealer_info_map.get(r.dealer_code, {}).get('city', '') and dealer_info_map.get(r.dealer_code, {}).get('city', '') in city) or
                             (city and city in dealer_info_map.get(r.dealer_code, {}).get('city', ''))]
        
        monthly_avg = {}
        for month in range(1, 13):
            month_records = [r for r in metrics_records if r.stat_month == month]
            if month_records:
                monthly_avg[month] = {
                    '销量': round(sum(float(r.sales or 0) for r in month_records) / len(month_records), 0),
                    '客流量': round(sum(float(r.customer_flow or 0) for r in month_records) / len(month_records), 0),
                    '线索量': round(sum(float(r.leads or 0) for r in month_records) / len(month_records), 0),
                    '潜客量': round(sum(float(r.potential_customers or 0) for r in month_records) / len(month_records), 0)
                }
        
        ranking_data = []
        dealer_all_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in dealer_all_scores:
                dealer_all_scores[dc] = []
            dealer_all_scores[dc].append(total)
        
        dealer_scores = {}
        for dc, scores in dealer_all_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            dealer_scores[dc] = {
                'code': dc,
                'province': dealer_info_map.get(dc, {}).get('province', ''),
                'city': dealer_info_map.get(dc, {}).get('city', ''),
                'totalScore': round(avg_score, 2)
            }
        
        ranking_data = sorted(dealer_scores.values(), key=lambda x: x['totalScore'], reverse=True)
        
        warning_red = sorted([d for d in dealer_scores.values() if d['totalScore'] < 3], key=lambda x: x['totalScore'])
        warning_orange = sorted([d for d in dealer_scores.values() if 3 <= d['totalScore'] < 4], key=lambda x: x['totalScore'])
        warning_green = sorted([d for d in dealer_scores.values() if d['totalScore'] >= 4], key=lambda x: -x['totalScore'])
        
        province_count = {}
        city_count = {}
        warning_province_count = {}
        warning_city_count = {}
        for dc, info in dealer_scores.items():
            p = info.get('province', '')
            c = info.get('city', '')
            if p:
                province_count[p] = province_count.get(p, 0) + 1
            if c:
                city_count[c] = city_count.get(c, 0) + 1
            if info['totalScore'] < 3:
                if p:
                    warning_province_count[p] = warning_province_count.get(p, 0) + 1
                if c:
                    warning_city_count[c] = warning_city_count.get(c, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'radar_avg': radar_avg,
                'monthly_avg': monthly_avg,
                'warning': {
                    'red': warning_red,
                    'orange': warning_orange,
                    'green': warning_green
                },
                'province_count': province_count,
                'city_count': city_count,
                'warning_province_count': warning_province_count,
                'warning_city_count': warning_city_count,
                'total_dealers': len(dealer_scores)
            }
        }), 200
        
    except Exception as e:
        print(f'获取概览数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/ranking', methods=['GET'])
def get_ranking():
    try:
        year = request.args.get('year', type=int, default=2024)
        sort_by = request.args.get('sort_by', type=str, default='total')
        province = request.args.get('province', type=str, default='')
        city = request.args.get('city', type=str, default='')
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        if province:
            radar_records = [r for r in radar_records if dealer_info_map.get(r.dealer_code, {}).get('province', '') == province]
        if city:
            radar_records = [r for r in radar_records if dealer_info_map.get(r.dealer_code, {}).get('city', '') == city or 
                           (dealer_info_map.get(r.dealer_code, {}).get('city', '') and dealer_info_map.get(r.dealer_code, {}).get('city', '') in city) or
                           (city and city in dealer_info_map.get(r.dealer_code, {}).get('city', ''))]
        
        dealer_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                dealer_scores[dc] = {
                    'spread': [],
                    'experience': [],
                    'conversion': [],
                    'service': [],
                    'operation': [],
                    'total': []
                }
            
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            
            dealer_scores[dc]['spread'].append(float(r.spread_force or 0))
            dealer_scores[dc]['experience'].append(float(r.experience_force or 0))
            dealer_scores[dc]['conversion'].append(float(r.conversion_force or 0))
            dealer_scores[dc]['service'].append(float(r.service_force or 0))
            dealer_scores[dc]['operation'].append(float(r.operation_force or 0))
            dealer_scores[dc]['total'].append(total)
        
        ranking_data = []
        for dc, scores in dealer_scores.items():
            avg_spread = sum(scores['spread']) / len(scores['spread']) if scores['spread'] else 0
            avg_experience = sum(scores['experience']) / len(scores['experience']) if scores['experience'] else 0
            avg_conversion = sum(scores['conversion']) / len(scores['conversion']) if scores['conversion'] else 0
            avg_service = sum(scores['service']) / len(scores['service']) if scores['service'] else 0
            avg_operation = sum(scores['operation']) / len(scores['operation']) if scores['operation'] else 0
            avg_total = sum(scores['total']) / len(scores['total']) if scores['total'] else 0
            
            score_map = {
                'total': avg_total,
                'spread': avg_spread,
                'experience': avg_experience,
                'conversion': avg_conversion,
                'service': avg_service,
                'operation': avg_operation
            }
            
            ranking_data.append({
                'code': dc,
                'province': dealer_info_map.get(dc, {}).get('province', ''),
                'city': dealer_info_map.get(dc, {}).get('city', ''),
                'score': round(score_map.get(sort_by, avg_total), 2)
            })
        
        ranking_data = sorted(ranking_data, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': ranking_data
        }), 200
        
    except Exception as e:
        print(f'获取排名数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/header-kpi', methods=['GET'])
def get_header_kpi():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_all_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in dealer_all_scores:
                dealer_all_scores[dc] = []
            dealer_all_scores[dc].append(total)
        
        dealer_scores = {}
        for dc, scores in dealer_all_scores.items():
            dealer_scores[dc] = sum(scores) / len(scores) if scores else 0
        
        total_dealers = len(dealer_info_map)
        avg_score = round(sum(dealer_scores.values()) / len(dealer_scores), 2) if dealer_scores else 0
        
        warning_count = len([s for s in dealer_scores.values() if s < 3])
        
        province_avg_scores = {}
        for dc, score in dealer_scores.items():
            province = dealer_info_map.get(dc, {}).get('province', '')
            if province:
                if province not in province_avg_scores:
                    province_avg_scores[province] = []
                province_avg_scores[province].append(score)
        
        top_province = ''
        top_province_score = 0
        for province, scores in province_avg_scores.items():
            avg = sum(scores) / len(scores)
            if avg > top_province_score:
                top_province_score = avg
                top_province = province
        
        active_dealers = total_dealers - warning_count
        
        return jsonify({
            'success': True,
            'data': {
                'totalDealers': total_dealers,
                'avgScore': avg_score,
                'warningCount': warning_count,
                'warningRatio': round(warning_count / total_dealers * 100, 1) if total_dealers > 0 else 0,
                'topProvince': top_province,
                'topProvinceScore': round(top_province_score, 2),
                'activeDealers': active_dealers,
                'activeRatio': round(active_dealers / total_dealers * 100, 1) if total_dealers > 0 else 0
            }
        }), 200
        
    except Exception as e:
        print(f'获取头部KPI失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/region-dashboard', methods=['GET'])
def get_region_dashboard():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        region_data = {}
        for r in radar_records:
            dc = r.dealer_code
            province = dealer_info_map.get(dc, {}).get('province', '')
            region = PROVINCE_REGION_MAP.get(province, '其他')
            
            if region not in region_data:
                region_data[region] = {
                    'dealers': set(),
                    'dealer_scores': {},
                    'provinces': set(),
                    'spread_forces': [],
                    'experience_forces': [],
                    'conversion_forces': [],
                    'service_forces': [],
                    'operation_forces': []
                }
            
            region_data[region]['dealers'].add(dc)
            region_data[region]['provinces'].add(province)
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in region_data[region]['dealer_scores']:
                region_data[region]['dealer_scores'][dc] = []
            region_data[region]['dealer_scores'][dc].append(total)
            region_data[region]['spread_forces'].append(float(r.spread_force or 0))
            region_data[region]['experience_forces'].append(float(r.experience_force or 0))
            region_data[region]['conversion_forces'].append(float(r.conversion_force or 0))
            region_data[region]['service_forces'].append(float(r.service_force or 0))
            region_data[region]['operation_forces'].append(float(r.operation_force or 0))
        
        force_names = {
            'spread': '传播获客力',
            'experience': '体验力',
            'conversion': '转化力',
            'service': '服务力',
            'operation': '经营力'
        }
        
        region_list = []
        for region, data in region_data.items():
            dealer_count = len(data['dealers'])
            
            dealer_avg_scores = {}
            for dc, scores in data['dealer_scores'].items():
                dealer_avg_scores[dc] = sum(scores) / len(scores) if scores else 0
            
            avg_score = round(sum(dealer_avg_scores.values()) / len(dealer_avg_scores), 2) if dealer_avg_scores else 0
            
            warning_count = len([s for s in dealer_avg_scores.values() if s < 3])
            
            avg_spread = sum(data['spread_forces']) / len(data['spread_forces']) if data['spread_forces'] else 0
            avg_experience = sum(data['experience_forces']) / len(data['experience_forces']) if data['experience_forces'] else 0
            avg_conversion = sum(data['conversion_forces']) / len(data['conversion_forces']) if data['conversion_forces'] else 0
            avg_service = sum(data['service_forces']) / len(data['service_forces']) if data['service_forces'] else 0
            avg_operation = sum(data['operation_forces']) / len(data['operation_forces']) if data['operation_forces'] else 0
            
            forces = {
                'spread': avg_spread,
                'experience': avg_experience,
                'conversion': avg_conversion,
                'service': avg_service,
                'operation': avg_operation
            }
            top_force = max(forces, key=forces.get)
            bottom_force = min(forces, key=forces.get)
            top_score = forces[top_force]
            bottom_score = forces[bottom_force]
            
            if avg_score >= 4:
                insight = f'综合表现优秀，{force_names[top_force]}达{top_score:.2f}分，建议保持并推广成功经验'
            elif avg_score >= 3:
                insight = f'{force_names[top_force]}表现较好({top_score:.2f}分)，建议重点提升{force_names[bottom_force]}({bottom_score:.2f}分)'
            else:
                insight = f'整体评分偏低，{force_names[bottom_force]}({bottom_score:.2f}分)急需改善，建议全面诊断'
            
            region_list.append({
                'region': region,
                'dealer_count': dealer_count,
                'avg_score': avg_score,
                'warning_count': warning_count,
                'provinces': list(data['provinces']),
                'insight': insight,
                'top_force': force_names[top_force],
                'bottom_force': force_names[bottom_force]
            })
        
        region_list.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': region_list
        }), 200
        
    except Exception as e:
        print(f'获取区域业绩看板失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/metrics-comparison', methods=['GET'])
def get_metrics_comparison():
    try:
        year = request.args.get('year', type=int, default=2024)
        month = request.args.get('month', type=int, default=10)
        
        metrics_records = MonthlyMetrics11d.query.filter(
            MonthlyMetrics11d.stat_year == year,
            MonthlyMetrics11d.stat_month == month
        ).all()
        
        total_sales = sum(float(r.sales or 0) for r in metrics_records)
        total_flow = sum(float(r.customer_flow or 0) for r in metrics_records)
        total_leads = sum(float(r.leads or 0) for r in metrics_records)
        total_potential = sum(float(r.potential_customers or 0) for r in metrics_records)
        
        sales_list = [float(r.sales or 0) for r in metrics_records if r.sales]
        flow_list = [float(r.customer_flow or 0) for r in metrics_records if r.customer_flow]
        leads_list = [float(r.leads or 0) for r in metrics_records if r.leads]
        potential_list = [float(r.potential_customers or 0) for r in metrics_records if r.potential_customers]
        
        return jsonify({
            'success': True,
            'data': {
                'sales': {
                    'total': int(total_sales),
                    'max': int(max(sales_list)) if sales_list else 0,
                    'min': int(min(sales_list)) if sales_list else 0,
                    'avg': int(sum(sales_list) / len(sales_list)) if sales_list else 0
                },
                'flow': {
                    'total': int(total_flow),
                    'max': int(max(flow_list)) if flow_list else 0,
                    'min': int(min(flow_list)) if flow_list else 0,
                    'avg': int(sum(flow_list) / len(flow_list)) if flow_list else 0
                },
                'leads': {
                    'total': int(total_leads),
                    'max': int(max(leads_list)) if leads_list else 0,
                    'min': int(min(leads_list)) if leads_list else 0,
                    'avg': int(sum(leads_list) / len(leads_list)) if leads_list else 0
                },
                'potential': {
                    'total': int(total_potential),
                    'max': int(max(potential_list)) if potential_list else 0,
                    'min': int(min(potential_list)) if potential_list else 0,
                    'avg': int(sum(potential_list) / len(potential_list)) if potential_list else 0
                }
            }
        }), 200
        
    except Exception as e:
        print(f'获取核心指标对比失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/insights', methods=['GET'])
def get_insights():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_scores = {}
        dealer_forces = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
                dealer_scores[dc] = total
                dealer_forces[dc] = {
                    'spread': float(r.spread_force or 0),
                    'experience': float(r.experience_force or 0),
                    'conversion': float(r.conversion_force or 0),
                    'service': float(r.service_force or 0),
                    'operation': float(r.operation_force or 0)
                }
        
        region_scores = {}
        for dc, score in dealer_scores.items():
            province = dealer_info_map.get(dc, {}).get('province', '')
            region = PROVINCE_REGION_MAP.get(province, '其他')
            if region not in region_scores:
                region_scores[region] = []
            region_scores[region].append(score)
        
        region_avg = {r: sum(s)/len(s) for r, s in region_scores.items()}
        top_region = max(region_avg, key=region_avg.get) if region_avg else ''
        bottom_region = min(region_avg, key=region_avg.get) if region_avg else ''
        
        avg_forces = {
            'spread': sum(f['spread'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'experience': sum(f['experience'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'conversion': sum(f['conversion'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'service': sum(f['service'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'operation': sum(f['operation'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0
        }
        top_force = max(avg_forces, key=avg_forces.get)
        bottom_force = min(avg_forces, key=avg_forces.get)
        
        force_names = {
            'spread': '传播获客力',
            'experience': '体验力',
            'conversion': '转化力',
            'service': '服务力',
            'operation': '经营力'
        }
        
        warning_dealers = [dc for dc, score in dealer_scores.items() if score < 15]
        warning_provinces = {}
        for dc in warning_dealers:
            province = dealer_info_map.get(dc, {}).get('province', '')
            if province:
                warning_provinces[province] = warning_provinces.get(province, 0) + 1
        
        top_warning_province = max(warning_provinces, key=warning_provinces.get) if warning_provinces else ''
        
        insights = []
        
        if top_region:
            insights.append({
                'type': 'highlight',
                'icon': '💡',
                'content': f'{top_region}区域表现优异，平均评分{region_avg[top_region]:.2f}分，建议其他区域参考其运营经验'
            })
        
        if bottom_region and bottom_region != top_region:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'content': f'{bottom_region}区域评分相对较低（{region_avg[bottom_region]:.2f}分），建议加强培训和运营支持'
            })
        
        insights.append({
            'type': 'trend',
            'icon': '📈',
            'content': f'全国五力分析中，{force_names[top_force]}表现最佳，{force_names[bottom_force]}有待提升'
        })
        
        if top_warning_province:
            insights.append({
                'type': 'suggestion',
                'icon': '🎯',
                'content': f'{top_warning_province}预警门店数最多（{warning_provinces[top_warning_province]}家），建议重点关注'
            })
        
        return jsonify({
            'success': True,
            'data': insights
        }), 200
        
    except Exception as e:
        print(f'获取数据洞察失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/radar/data', methods=['GET'])
def get_radar_data():
    try:
        year = request.args.get('year', type=int, default=2024)
        month = request.args.get('month', type=int, default=1)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = row[1]
        except:
            pass
        
        query = MonthlyRadarScores.query.filter(
            MonthlyRadarScores.stat_year == year,
            MonthlyRadarScores.stat_month == month
        )
        records = query.all()
        
        data = []
        for record in records:
            data.append({
                'dealer_code': record.dealer_code,
                'province': dealer_info_map.get(record.dealer_code, ''),
                'spread_force': float(record.spread_force) if record.spread_force else 0,
                'experience_force': float(record.experience_force) if record.experience_force else 0,
                'conversion_force': float(record.conversion_force) if record.conversion_force else 0,
                'service_force': float(record.service_force) if record.service_force else 0,
                'operation_force': float(record.operation_force) if record.operation_force else 0
            })
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
        
    except Exception as e:
        print(f'获取雷达数据失败: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


if __name__ == "__main__":
    freeze_support()
    init_app()
    print(f"统一后端服务启动，端口: 5002")
    app.run(host="0.0.0.0", port=5002, debug=False, use_reloader=False)
