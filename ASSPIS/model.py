# model.py
# ------------------------------------------------------------
# 目标（保持 main.py / 前端完全不动）：
# 1) train_model() / predict_sales_change() 的函数签名与返回结构不变
# 2) Step 2：目标变换 log1p(sales) 训练，预测端 expm1 逆变换并 clip(min=0)
# 3) Step 3：新增“严格只用过去信息”的销量 lag/rolling 特征（不引入未来信息）
# 4) Step 4：dealer_bias_（hierarchical calibration）在 log 空间做偏置校准，
#            且在滚动/交叉验证中严格按训练窗口计算（避免评估泄漏）
# 5) 评估：保留现有 KFold CV（用于整体稳定性），新增 rolling 多折回测（主评估）
# 6) what-if：仍在“原子特征空间”修改 -> 重新计算派生特征 -> scaler.transform -> 预测
# ------------------------------------------------------------

import os
import time
from collections import defaultdict
from dataclasses import dataclass
from sklearn.base import clone

import numpy as np
import xgboost as xgb
from scipy.stats import uniform
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
)
from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# 训练档位：conservative / standard / advanced
TRAIN_MODE = os.getenv("TRAIN_MODE", "conservative").strip().lower()
PHASE2_SEASONAL_FEATURES = os.getenv("PHASE2_SEASONAL_FEATURES", "1").strip() not in ("0", "false", "False")
# Phase2.1: 鲁棒化开关（针对 1/2 月尤其容易出现的比率爆炸问题）
PHASE2_ROBUST_RATIOS = os.getenv("PHASE2_ROBUST_RATIOS", "1").strip() not in ("0", "false", "False")
# 消融：仅关闭 yoy 派生特征（lag12/roll12 仍保留），用于定位 2 月恶化是否由 yoy 特征导致
PHASE2_DISABLE_YOY = os.getenv("PHASE2_DISABLE_YOY", "0").strip() not in ("0", "false", "False")
# clip 阈值（log-ratio/变化率）：可按数据尺度微调
CLIP_LOG_RATIO = float(os.getenv("CLIP_LOG_RATIO", "2.0"))
CLIP_PCT_CHANGE = float(os.getenv("CLIP_PCT_CHANGE", "3.0"))
CLIP_RATE_MAX = float(os.getenv("CLIP_RATE_MAX", "5.0"))
CLIP_STORE2SALES_MAX = float(os.getenv("CLIP_STORE2SALES_MAX", "2.0"))
PHASE_STORE_CALIB = os.getenv("PHASE_STORE_CALIB", "1").strip() not in ("0", "false", "False")
# =========================
# Phase 2.8：ratio 特征鲁棒化（safe_divide / log-ratio / ratio missing flag）
# - 只改特征构造，不改主模型结构；用于缓解“分母很小/缺失填补”导致的抖动
# - 四组消融：
#   R0: 全关（保持当前 Phase2.7 行为）
#   R1: SAFE_DIVIDE=1
#   R2: SAFE_DIVIDE=1 + LOG_RATIO=1（仅对“尺度比率”启用 log1p 差分）
#   R3: R2 + MISSING_FLAG=1（为 ratio 的 denom 缺失/裁剪增加 flag）
# =========================
PHASE28_SAFE_DIVIDE = os.getenv('PHASE28_SAFE_DIVIDE', '0').strip() not in ('0','false','False')
PHASE28_LOG_RATIO = os.getenv('PHASE28_LOG_RATIO', '0').strip() not in ('0','false','False')
PHASE28_MISSING_FLAG = os.getenv('PHASE28_MISSING_FLAG', '0').strip() not in ('0','false','False')
PHASE28_EPS = float(os.getenv('PHASE28_EPS', '1e-6'))
# =========================
# Phase 3.2：目标对齐与样本加权消融开关
# =========================
PHASE32_LOSS_L1 = os.getenv("PHASE32_LOSS_L1", "1").strip() not in ("0", "false", "False")
PHASE32_USE_WEIGHT = os.getenv("PHASE32_USE_WEIGHT", "1").strip() not in ("0", "false", "False")
# =========================
# Phase 3.0: 冻结基线（仅用于评估协议固化，不改变模型训练逻辑）
# - 该函数用于 eval 脚本写 run_manifest.json / 结果可复现
# =========================
# Phase 3.4：方案 A + 小网格定树数
# - A：禁用 early stopping（避免 test fold 泄漏/不一致）
# - 小网格：仅在“最终选定的超参”上搜索 n_estimators
# =========================
PHASE34_DISABLE_EARLY_STOP = os.getenv("PHASE34_DISABLE_EARLY_STOP", "1").strip() not in ("0", "false", "False")

# Optuna 阶段固定树数（不搜 n_estimators，降低维度）
PHASE34_BASE_TREES = int(os.getenv("PHASE34_BASE_TREES", "650"))

# 小网格：最终定树数（逗号分隔）
PHASE34_TREES_GRID = os.getenv("PHASE34_TREES_GRID", "450,650,900,1150").strip()

# Optuna 轮数与权衡系数（避免写死）
OPTUNA_N_TRIALS = int(os.getenv("OPTUNA_N_TRIALS", "300"))
TRADE_OFF_WEIGHT = float(os.getenv("TRADE_OFF_WEIGHT", "1.0"))

MODEL_STAGE = "phase3_0_frozen_baseline"

def get_runtime_config() -> dict:
    """返回“已解析后的运行配置”（包含默认值解析结果）。用于复现与审计。"""
    return {
        # core
        "MODEL_STAGE": MODEL_STAGE,
        "TRAIN_MODE": TRAIN_MODE,
        "ROLL_MODE": ROLL_MODE,
        "ROLL_WINDOW_MONTHS": ROLL_WINDOW_MONTHS,
        "ROLL_MIN_TRAIN_PERIODS": ROLL_MIN_TRAIN_PERIODS,
        "ROLL_START_TEST_MONTH": ROLL_START_TEST_MONTH,
        "ROLL_GAP": ROLL_GAP,

        # phase2 switches
        "PHASE2_JANFEB_GATE": PHASE2_JANFEB_GATE,
        "PHASE2_JANFEB_GATE_LAG12": PHASE2_JANFEB_GATE_LAG12,
        "PHASE2_JANFEB_ANCHOR": PHASE2_JANFEB_ANCHOR,
        "PHASE2_DISABLE_YOY": PHASE2_DISABLE_YOY,
        "PHASE2_SEASONAL_FEATURES": PHASE2_SEASONAL_FEATURES,
        "PHASE2_ROBUST_RATIOS": PHASE2_ROBUST_RATIOS,
        "PHASE2_ADD_MISSING_FLAGS": PHASE2_ADD_MISSING_FLAGS,

        "PHASE_STORE_CALIB": PHASE_STORE_CALIB,

        # phase2.3 base history
        "PHASE23_ENABLE": PHASE23_ENABLE,
        "PHASE23_HIST_WINDOW": PHASE23_HIST_WINDOW,
        "PHASE23_LOOKBACK_LAST": PHASE23_LOOKBACK_LAST,
        "PHASE23_MIN_BASE_SIGNAL": PHASE23_MIN_BASE_SIGNAL,
        "PHASE23_STALENESS_CAP": PHASE23_STALENESS_CAP,
        "PHASE23_ADD_BASE_MISSING_FLAGS": PHASE23_ADD_BASE_MISSING_FLAGS,
        "PHASE23_ADD_BASE_STALENESS": PHASE23_ADD_BASE_STALENESS,

        # phase2.4 CNY soft-missing
        "PHASE24_SOFT_MISSING": PHASE24_SOFT_MISSING,
        "PHASE24_CNY_FEATURES": PHASE24_CNY_FEATURES,
        "PHASE24_CNY_WINDOW": PHASE24_CNY_WINDOW,
        "PHASE24_CNY_MONTH_MAP": PHASE24_CNY_MONTH_MAP,

        # phase2.8 ratio safety
        "PHASE28_SAFE_DIVIDE": PHASE28_SAFE_DIVIDE,
        "PHASE28_LOG_RATIO": PHASE28_LOG_RATIO,
        "PHASE28_MISSING_FLAG": PHASE28_MISSING_FLAG,
        "PHASE28_EPS": PHASE28_EPS,

        "PHASE32_LOSS_L1": PHASE32_LOSS_L1,
        "PHASE32_USE_WEIGHT": PHASE32_USE_WEIGHT,
        # phase3.4 tuning controls
        "PHASE34_DISABLE_EARLY_STOP": PHASE34_DISABLE_EARLY_STOP,
        "PHASE34_BASE_TREES": PHASE34_BASE_TREES,
        "PHASE34_TREES_GRID": PHASE34_TREES_GRID,
        "OPTUNA_N_TRIALS": OPTUNA_N_TRIALS,
        "TRADE_OFF_WEIGHT": TRADE_OFF_WEIGHT,
        # clip settings
        "CLIP_RATE_MAX": CLIP_RATE_MAX,
        "CLIP_STORE2SALES_MAX": CLIP_STORE2SALES_MAX,
        "CLIP_LOG_RATIO": CLIP_LOG_RATIO,
        "CLIP_JF_LOG": CLIP_JF_LOG,
        "CLIP_PCT_CHANGE": CLIP_PCT_CHANGE,
    }

# =========================
# Phase 2.2：春节错位修复（Jan/Feb gate + JanFeb 2M 锚点 + 缺失标记）
# =========================
# Jan/Feb gate：在 1/2 月将 yoy 派生特征置零（避免“同月同比”在春节漂移时语义错位）
PHASE2_JANFEB_GATE = os.getenv("PHASE2_JANFEB_GATE", "1").strip() not in ("0", "false", "False")
# 可选：在 1/2 月同时将 lag12 置零（更激进，默认关闭；建议用消融验证）
PHASE2_JANFEB_GATE_LAG12 = os.getenv("PHASE2_JANFEB_GATE_LAG12", "0").strip() not in ("0", "false", "False")
# JanFeb 2M 锚点：利用上一年 1+2 月合计及其结构，缓解春节在 1/2 月漂移造成的错位
PHASE2_JANFEB_ANCHOR = os.getenv("PHASE2_JANFEB_ANCHOR", "1").strip() not in ("0", "false", "False")
# 缺失标记：为关键季节锚点/JanFeb 锚点追加 missing flag（避免“缺失填 0”被当作真实 0）
PHASE2_ADD_MISSING_FLAGS = os.getenv("PHASE2_ADD_MISSING_FLAGS", "1").strip() not in ("0", "false", "False")
# JanFeb 锚点 log 特征 clip（log1p 尺度），默认足够大以覆盖常见销量范围
CLIP_JF_LOG = float(os.getenv("CLIP_JF_LOG", "12.0"))

# =========================
# Phase 2.3：覆盖断崖修复（缺失容忍 + 时序安全填补 + 缺失/陈旧度标记）
# 目标：尽量保留“销量标签存在但部分特征缺失”的样本，缓解 2024 年样本覆盖断崖导致的 WMAPE 爆炸。
# 说明：填补严格只使用当前月之前的历史（last/median over past），不引入未来信息。
# =========================
PHASE23_ENABLE = os.getenv("PHASE23_ENABLE", "1").strip() not in ("0", "false", "False")
# 当月原子特征缺失时：优先用最近一次观测（过去 lookback 月），再退化到过去 hist_window 月中位数，最后 0。
PHASE23_LOOKBACK_LAST = int(os.getenv("PHASE23_LOOKBACK_LAST", "3"))
PHASE23_HIST_WINDOW = int(os.getenv("PHASE23_HIST_WINDOW", "12"))
# 允许进入样本构造的最小“可用原子特征”数量（可用=当月有值或历史窗口内有值可填补）
PHASE23_MIN_BASE_SIGNAL = int(os.getenv("PHASE23_MIN_BASE_SIGNAL", "1"))
# 附加缺失标记（对 10 个原子维度）
PHASE23_ADD_BASE_MISSING_FLAGS = os.getenv("PHASE23_ADD_BASE_MISSING_FLAGS", "1").strip() not in ("0", "false", "False")
# 附加陈旧度（缺失时距离最近一次观测的月数；0 表示当月有值）
PHASE23_ADD_BASE_STALENESS = os.getenv("PHASE23_ADD_BASE_STALENESS", "1").strip() not in ("0", "false", "False")
PHASE23_STALENESS_CAP = int(os.getenv("PHASE23_STALENESS_CAP", "12"))

# =========================
# Phase 2.4：春节（CNY）日历特征 + 消融开关
# 目标：在不扩数据的前提下，为 1/2 月提供“节假日所在月”显式信号，缓解春节跨月漂移导致的同月同比语义错位。
# =========================
PHASE24_CNY_FEATURES = os.getenv("PHASE24_CNY_FEATURES", "1").strip() not in ("0", "false", "False")
# 可选：自定义 CNY 月份映射（仅需给出年份->月份），例如 "2022:2,2023:1,2024:2"
PHASE24_CNY_MONTH_MAP = os.getenv("PHASE24_CNY_MONTH_MAP", "").strip()
# CNY 影响窗口（按月）：默认 1 表示 [前一月, 当月, 后一月]
PHASE24_CNY_WINDOW = int(os.getenv("PHASE24_CNY_WINDOW", "1"))

# 软缺失建模别名开关：若设置了 PHASE24_SOFT_MISSING，则覆盖 PHASE23_ENABLE
PHASE24_SOFT_MISSING = os.getenv("PHASE24_SOFT_MISSING", "").strip()
_PH24_SOFT = PHASE24_SOFT_MISSING  # backward alias（历史变量名）

# 只要用户显式设置了该 env（非空），就覆盖 PHASE23_ENABLE
if PHASE24_SOFT_MISSING != "":
    PHASE23_ENABLE = PHASE24_SOFT_MISSING not in ("0", "false", "False")

# rolling 多折评估：默认从 t=6 开始（保证历史更稳定），可用环境变量调整
ROLL_START_TEST_MONTH = int(os.getenv("ROLL_START_TEST_MONTH", "22"))
# Phase1+：rolling 采用 time_key(year,month) 作为时间轴；提供 expanding/sliding 两种训练窗
ROLL_MODE = os.getenv("ROLL_MODE", "expanding").strip().lower()  # expanding | sliding
ROLL_WINDOW_MONTHS = int(os.getenv("ROLL_WINDOW_MONTHS", "24"))  # sliding 用
# 兼容旧变量名：ROLL_START_TEST_MONTH 在旧实现里是“起测月份”；在 time_key 版本里等价于“至少有多少个月历史”
ROLL_MIN_TRAIN_PERIODS = int(os.getenv("ROLL_MIN_TRAIN_PERIODS", str(ROLL_START_TEST_MONTH)))
ROLL_GAP = int(os.getenv("ROLL_GAP", "0"))


# =========================
# Step 2：目标变换（log1p）
# =========================
def get_prev_year_month(year: int, month: int, lag: int) -> tuple:
    """
    计算前 lag 个月的年份和月份 (处理跨年逻辑)
    例如：(2024, 1, 1) -> (2023, 12)
    """
    total_months = year * 12 + (month - 1) - lag
    new_year = total_months // 12
    new_month = total_months % 12 + 1
    return new_year, new_month


def make_time_key(year: int, month: int) -> int:
    """将 (year, month) 映射到单调递增的整数时间轴（按月）。等价于 year*12 + (month-1)。"""
    return int(year) * 12 + (int(month) - 1)


def time_key_to_ym(time_key: int) -> tuple[int, int]:
    """make_time_key 的逆变换：time_key -> (year, month)。"""
    y = int(time_key) // 12
    m = int(time_key) % 12 + 1
    return y, m


# =========================
# Phase 2.4：春节（CNY）日历特征（按月）
# - 只依赖 (year, month)；不引入未来销售/外生数据
# - 用“最近一次春节事件”的 time_key 距离（按月）构造特征，天然处理“春节在 1 月/2 月漂移”
# =========================
CNY_FEATURE_DIM = 6


def _parse_cny_month_map(s: str) -> dict[int, int]:
    mp: dict[int, int] = {}
    s = (s or "").strip()
    if not s:
        return mp
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            continue
        ys, ms = part.split(":", 1)
        try:
            y = int(ys.strip())
            m = int(ms.strip())
        except Exception:
            continue
        if 1 <= m <= 12:
            mp[y] = m
    return mp


# 默认仅内置训练数据覆盖年份（避免引入不确定信息）
_CNY_MONTH_BASE: dict[int, int] = {
    2022: 2,  # 2022 春节在 2 月
    2023: 1,  # 2023 春节在 1 月
    2024: 2,  # 2024 春节在 2 月
}
_CNY_MONTH_OVR = _parse_cny_month_map(PHASE24_CNY_MONTH_MAP)
_CNY_MONTH = {**_CNY_MONTH_BASE, **_CNY_MONTH_OVR}


def _cny_month(year: int) -> int:
    return int(_CNY_MONTH.get(int(year), 0))


def _cny_event_time_keys_around(year: int) -> list[int]:
    """取 year-1/year/year+1 的春节 time_key（若可得），用于解决跨年（如 12 月靠近次年 1 月春节）。"""
    tks: list[int] = []
    for y in (year - 1, year, year + 1):
        m = _cny_month(y)
        if m:
            tks.append(make_time_key(y, m))
    return tks


def _cny_feature_vector(year: int, month: int) -> list[float]:
    """
    返回 6 维：
      0 cny_rel_d   : 最近春节事件的相对距离（按月），clip 到 [-3,3]
      1 cny_in_win  : |d|<=window
      2 cny_pre     : d==-1
      3 cny_in      : d==0
      4 cny_post    : d==+1
      5 cny_is_jan  : 最近春节事件发生在 1 月
    """
    tk = make_time_key(year, month)
    cand = _cny_event_time_keys_around(year)
    if not cand:
        return [0.0] * CNY_FEATURE_DIM

    # 选最近事件
    best = min(cand, key=lambda x: abs(tk - x))
    d = int(tk - best)
    # clip
    d_clip = float(max(-3, min(3, d)))
    win = int(max(0, PHASE24_CNY_WINDOW))
    in_win = 1.0 if abs(d) <= win else 0.0
    pre = 1.0 if d == -1 else 0.0
    inn = 1.0 if d == 0 else 0.0
    post = 1.0 if d == 1 else 0.0

    # 最近事件是否为 1 月春节
    ey, em = time_key_to_ym(best)
    is_jan = 1.0 if int(em) == 1 else 0.0
    return [d_clip, in_win, pre, inn, post, is_jan]


def _to_log_target(y_raw: np.ndarray) -> np.ndarray:
    """log1p 目标，兼容 0。"""
    return np.log1p(np.maximum(y_raw, 0.0))


def _from_log_target(y_hat_log: np.ndarray) -> np.ndarray:
    """expm1 逆变换，并保证非负。"""
    return np.maximum(np.expm1(y_hat_log), 0.0)


# =========================
# 指标
# =========================
def _smape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    denom = np.maximum(np.abs(y_true) + np.abs(y_pred), eps)
    return float(np.mean(2.0 * np.abs(y_pred - y_true) / denom) * 100.0)


def _wmape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    den = float(np.sum(np.abs(y_true)))
    if den <= eps:
        return float("nan")
    return float(np.sum(np.abs(y_true - y_pred)) / den * 100.0)


# =========================
# Phase2.1：鲁棒工具（防止比率/变化率爆炸）
# =========================
def _clip(x: float, lo: float, hi: float) -> float:
    try:
        return float(np.clip(float(x), lo, hi))
    except Exception:
        return 0.0


def _safe_div(num: float, den: float, default: float = 0.0, den_min: float = 1.0) -> float:
    try:
        num = float(num)
        den = float(den)
    except Exception:
        return float(default)
    if den < den_min:
        return float(default)
    return float(num / den)


def _log1p_safe(x: float) -> float:
    try:
        return float(np.log1p(max(float(x), 0.0)))
    except Exception:
        return 0.0


def _log_ratio(a: float, b: float) -> float:
    # log1p(a) - log1p(b)，比 a/b 更稳；并且天然处理 0
    return _log1p_safe(a) - _log1p_safe(b)


# Phase2.8：统一的 ratio 计算（返回：value, flag）
# flag=1 表示 denom 缺失/<=0 或发生 clip（让模型区分“真 0”与“缺失/爆炸被压扁”）
def _ratio_value_and_flag(num: float, den: float, *,
                          default: float = 0.0,
                          eps: float = 1e-6,
                          clip_low: float | None = None,
                          clip_high: float | None = None,
                          use_log_ratio: bool = False,
                          log_clip: float | None = None) -> tuple[float, float]:
    try:
        num_f = float(num)
        den_f = float(den)
    except Exception:
        return float(default), 1.0

    # denom 缺失或无效
    if (not (den_f == den_f)) or den_f <= 0:
        return float(default), 1.0

    flag = 0.0

    if use_log_ratio:
        # log1p(num) - log1p(den)，更稳（对 0 友好）
        try:
            v = _log_ratio(max(0.0, num_f), max(0.0, den_f))
        except Exception:
            return float(default), 1.0
        if log_clip is not None:
            v2 = _clip(v, -float(log_clip), float(log_clip))
            if v2 != v:
                flag = 1.0
            v = v2
        return float(v), float(flag)

    # safe_divide: den + eps
    v = num_f / (den_f + float(eps))

    if (clip_low is not None) or (clip_high is not None):
        lo = float(clip_low) if clip_low is not None else v
        hi = float(clip_high) if clip_high is not None else v
        v2 = _clip(v, lo, hi)
        if v2 != v:
            flag = 1.0
        v = v2

    return float(v), float(flag)


# =========================
# Step 3：历史销量特征（严格只用过去月份）
# =========================
def _map_at(mp: dict, year: int, month: int):
    """
    兼容两种存储：
      1) mp[(year, month)]
      2) mp[month]
    """
    if mp is None:
        return None
    if (year, month) in mp:
        return mp.get((year, month))
    return mp.get(month)


# =========================
# Phase 2.3：时序安全缺失填补工具
# =========================
_BASE_ATOMS = [
    ("potential_customers", "potential_customers"),
    ("test_drives", "test_drives"),
    ("leads", "leads"),
    ("customer_flow", "customer_flow"),
    ("defeat_rate", "defeat_rate"),
    ("success_rate", "success_rate"),
    ("success_response_time", "success_response_time"),
    ("defeat_response_time", "defeat_response_time"),
    ("policy", "policy"),
    ("gsev", "gsev"),
]


def _is_nan(x) -> bool:
    try:
        return x is None or (isinstance(x, float) and np.isnan(x))
    except Exception:
        return x is None


def _get_map(dealer_data, attr: str) -> dict:
    return getattr(dealer_data, attr, {}) or {}


def _past_values(mp: dict, year: int, month: int, window: int):
    vals = []
    for k in range(1, window + 1):
        py, pm = get_prev_year_month(year, month, k)
        v = _map_at(mp, py, pm)
        if not _is_nan(v):
            try:
                vals.append(float(v))
            except Exception:
                continue
    return vals

def _impute_atom_value(dealer_data, attr: str, year: int, month: int, default: float = 0.0,global_default: float = 0.0):
    """返回 (value, miss_flag, staleness_months, has_signal_flag)

    - miss_flag: 当月缺失=1，否则 0
    - staleness: 当月有值=0；用最近观测填补时=lag(1..lookback)；用中位数/默认填补时=PHASE23_STALENESS_CAP
    - has_signal_flag: 当月或历史窗口内存在可用值（用于样本保留判定）
    """
    mp = _get_map(dealer_data, attr)
    v0 = _map_at(mp, year, month)
    if not _is_nan(v0):
        try:
            return float(v0), 0.0, 0.0, 1.0
        except Exception:
            pass

    # 当月缺失
    miss = 1.0

    # 1) 最近一次观测（lookback）
    for lag in range(1, max(1, PHASE23_LOOKBACK_LAST) + 1):
        py, pm = get_prev_year_month(year, month, lag)
        vv = _map_at(mp, py, pm)
        if not _is_nan(vv):
            try:
                st = float(min(lag, max(1, PHASE23_STALENESS_CAP)))
                return float(vv), miss, st, 1.0
            except Exception:
                continue

    # 2) 过去窗口中位数（hist window）
    vals = _past_values(mp, year, month, window=max(1, PHASE23_HIST_WINDOW))
    if vals:
        try:
            v_med = float(np.median(vals))
        except Exception:
            v_med = float(default)
        st = float(max(1, PHASE23_STALENESS_CAP))
        return v_med, miss, st, 1.0

    # 3) 无信号：默认值
    st = float(max(1, PHASE23_STALENESS_CAP))
    final_val = global_default if global_default != 0.0 else default
    return float(final_val), 1.0, st, 0.0


def _base_signal_count(dealer_data, year: int, month: int) -> int:
    """统计该 dealer 在该月能构造多少个“有信号”的原子特征（当月有值或历史窗口内有值）。"""
    cnt = 0
    for _, attr in _BASE_ATOMS:
        mp = _get_map(dealer_data, attr)
        v0 = _map_at(mp, year, month)
        if not _is_nan(v0):
            cnt += 1
            continue
        # 历史窗口内存在即视为可填补
        vals = _past_values(mp, year, month, window=max(1, PHASE23_HIST_WINDOW))
        if vals:
            cnt += 1
    return int(cnt)


def _sales_at(dealer_data, year: int, month: int) -> float | None:
    """获取指定年月的销量，兼容 (year,month) / month-key。"""
    v = _map_at(getattr(dealer_data, "sales", {}), year, month)
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def sales_lag(dealer_data, year: int, month: int, lag: int, default: float = 0.0) -> float:
    """sales_{m-lag}（缺失->default，支持跨年）"""
    prev_year, prev_month = get_prev_year_month(year, month, lag)
    # 可选：限制最早年份，避免查询过远历史
    if prev_year < 2020:
        return default
    v = _sales_at(dealer_data, prev_year, prev_month)
    return default if v is None else float(v)


def sales_roll_mean(dealer_data, year: int, month: int, window: int = 3, default: float = 0.0) -> float:
    """mean(sales_{m-1}..sales_{m-window})（支持跨年）"""
    vals = []
    for k in range(1, window + 1):
        py, pm = get_prev_year_month(year, month, k)
        v = _sales_at(dealer_data, py, pm)
        if v is not None:
            vals.append(v)
    if len(vals) == 0:
        return default
    return float(np.mean(vals))


def sales_roll_std(dealer_data, year: int, month: int, window: int = 3, default: float = 0.0) -> float:
    """std(sales_{m-1}..sales_{m-window})（支持跨年）"""
    vals = []
    for k in range(1, window + 1):
        py, pm = get_prev_year_month(year, month, k)
        v = _sales_at(dealer_data, py, pm)
        if v is not None:
            vals.append(v)
    if len(vals) < 2:
        return default
    return float(np.std(vals, ddof=0))


def dealer_hist_mean(dealer_data, year: int, month: int, default: float = 0.0) -> float:
    """mean(sales_1..sales_{m-1})（当前实现简化为最近 12 个月均值，避免遍历所有历史）"""
    vals = []
    for k in range(1, 13):  # 取过去 12 个月
        py, pm = get_prev_year_month(year, month, k)
        v = _sales_at(dealer_data, py, pm)
        if v is not None:
            vals.append(v)
    if len(vals) == 0:
        return default
    return float(np.mean(vals))


def lagged_store_to_sales_rate(dealer_data, year: int, month: int, lag: int = 1) -> float:
    """
    store_to_sales_rate 使用上一个月(t-1)的 sales/flow，严格只用过去信息（支持跨年）。
    """
    py, pm = get_prev_year_month(year, month, lag)

    sales_prev = _map_at(getattr(dealer_data, "sales", {}), py, pm)
    flow_prev = _map_at(getattr(dealer_data, "customer_flow", {}), py, pm)

    if sales_prev is None or flow_prev is None:
        return 0.0

    try:
        sales_prev = float(sales_prev)
        flow_prev = float(flow_prev)
    except Exception:
        return 0.0

    if flow_prev <= 0:
        return 0.0

    return float(sales_prev) / float(flow_prev)


# =========================
# 字段检查：训练需要 sales[month]，预测不需要 sales[month]
# =========================

# =========================
# 字段检查：训练需要 sales[month]，预测不需要 sales[month]
# Phase 2.3：不再要求当月所有原子特征齐全；允许缺失并在 build_features 内做“只用过去信息”的填补。
# =========================
def _has_required_month_fields(dealer_data, year: int, month: int, *, include_target: bool = True) -> bool:
    """
    include_target=True  : 训练（需要 sales[year,month] 作为 y）
    include_target=False : 预测（不要求 sales[year,month]，但仍需能构造出至少部分特征）

    Phase2.3 逻辑（PHASE23_ENABLE=True）：
    - 训练：要求当月销量存在；同时要求“可用原子特征数”>= PHASE23_MIN_BASE_SIGNAL
    - 预测：要求“可用原子特征数”>= PHASE23_MIN_BASE_SIGNAL
    """
    if include_target:
        if _map_at(getattr(dealer_data, "sales", {}), year, month) is None:
            return False

    if not PHASE23_ENABLE:
        # 保持旧逻辑：当月原子特征必须齐全
        required_maps = [
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
        for mp in required_maps:
            if _map_at(mp, year, month) is None:
                return False
        return True

    # Phase2.3：允许缺失，但至少要能从当月/历史构造出一些信号
    sig = _base_signal_count(dealer_data, year, month)
    return sig >= int(max(0, PHASE23_MIN_BASE_SIGNAL))


# =========================
# 特征工程（前 13 维顺序保持不变；新增历史特征追加在末尾）
# =========================


def build_features(dealer_data, year: int, month: int, overrides: dict | None = None, global_medians: dict | None = None) -> list:
    """
    原 13 维特征顺序（保持不变）：
      0 potential_customers
      1 test_drives
      2 leads
      3 customer_flow
      4 defeat_rate
      5 success_rate
      6 success_response_time
      7 defeat_response_time
      8 policy
      9 gsev
      10 lead_to_potential_rate (leads / potential_customers)
      11 potential_to_store_rate (customer_flow / potential_customers)
      12 store_to_sales_rate (lagged sales/flow, t-1)

    Step 3 追加的历史销量特征（严格只用 <month 的销量）：
      13 sales_lag1
      14 sales_lag2
      15 sales_lag3
      16 sales_roll3_mean
      17 sales_roll6_mean
      18 sales_roll3_std
      19 sales_roll6_std
      20 sales_diff_1 (lag1 - lag2)
      21 sales_pct_change_1 ((lag1-lag2)/max(lag2,1))
      22 dealer_hist_mean (mean(sales[1..month-1]))
      23 month_sin  (sin(2π*month/12))
      24 month_cos  (cos(2π*month/12))

    Phase 2 追加的长周期锚点（追加在末尾）：
      25 sales_lag6
      26 sales_lag12 (同比同月锚点)
      27 sales_roll12_mean
      28 sales_roll12_std
      29 yoy_mom_ratio (lag12/lag13)
      30 yoy_mom_diff  (lag12-lag13)
      31 yoy_level_ratio (lag12/roll12_mean)
      32 time_trend (time_key)
      33 is_peak (11/12)
      34 is_dec (12)


    Phase 2.2 追加（追加在末尾；用于 1/2 月春节错位）：
      35 is_janfeb (month in {1,2})
      36 janfeb_gate_active
      37 jf_ly_total_log (log1p(sales_{y-1,1}+sales_{y-1,2}))
      38 jf_ly_feb_share (sales_{y-1,2} / (sales_{y-1,1}+sales_{y-1,2}))
      39 jf_ly_feb_to_jan_logratio (log1p(Feb_{y-1})-log1p(Jan_{y-1}))
      40 jf_cur_jan_log (仅 month==2：log1p(Jan_y))
      41 jf_cur_jan_vs_ly_jan_logdiff (仅 month==2)
      42 jf_proj_feb_log (仅 month==2：jf_cur_jan_log + jf_ly_feb_to_jan_logratio)
      43 miss_cur_jan (仅 month==2)
      44 miss_ly_jan (仅 month in {1,2})
      45 miss_ly_feb (仅 month in {1,2})
      46 miss_lag12
      47 miss_lag13
      48 roll12_coverage (过去 12 个月销量可用比例)
      49 miss_roll12 (coverage<1)


Phase 2.3 追加（追加在末尾；用于缓解 2024 覆盖断崖）：
  50 base_cur_present（当月原子特征存在数量，0-10）
  51 base_signal_cnt（当月或历史可填补的原子特征数量，0-10）
  52..61 base_miss_*（10 个原子维度的当月缺失标记，1=缺失）
  62..71 base_stale_*（10 个原子维度的陈旧度，0=当月有值，>0=用历史填补）

    说明（对应“细节修改”优先级 2：为 h>=2 提供更强的自回归/趋势/季节性锚点）：
    - 在不引入未来信息的前提下，补足更长窗口(6)的滚动统计与相对变化率。
    - 保持前 13 维索引不变，避免影响前端 what-if 维度映射。
    """
    # Phase2.3：允许当月原子特征缺失，使用“只用过去信息”的策略进行填补，并生成缺失/陈旧度标记
    base = {}
    base_miss = {}
    base_stale = {}
    base_has_signal = {}

    # 默认值：计数类(潜客/试驾/线索/客流/GSEV/政策)缺失用 0；率/时间类缺失同样先用历史填补，最后 0。
    defaults = {
        "potential_customers": 0.0,
        "test_drives": 0.0,
        "leads": 0.0,
        "customer_flow": 0.0,
        "defeat_rate": 0.0,
        "success_rate": 0.0,
        "success_response_time": 0.0,
        "defeat_response_time": 0.0,
        "policy": 0.0,
        "gsev": 0.0,
    }

    global_medians = global_medians or {}
    for k, attr in _BASE_ATOMS:
        # 获取该维度的全局中位数
        g_def = global_medians.get(k, 0.0)
        v, miss, stale, has_sig = _impute_atom_value(
            dealer_data, attr=attr, year=int(year), month=int(month),
            default=float(defaults[k]), global_default=float(g_def)
        )
        base[k] = float(v)
        base_miss[k] = float(miss)
        base_stale[k] = float(stale)
        base_has_signal[k] = float(has_sig)
    # what-if 覆盖：只覆盖“原子特征”，历史特征仍然从历史数据计算（避免泄漏/逻辑错误）
    if overrides:
        for k, v in overrides.items():
            if k in base:
                base[k] = float(v)
                base_miss[k] = 0.0
                base_stale[k] = 0.0
                base_has_signal[k] = 1.0

    pc = base["potential_customers"]
    leads = base["leads"]
    flow = base["customer_flow"]

    # Phase2.8：ratio flags（仅在 PHASE28_MISSING_FLAG=1 时输出到特征末尾）
    ratio_flag_lead_pc = 0.0
    ratio_flag_flow_pc = 0.0
    ratio_flag_store_sales = 0.0
    ratio_flag_pct_change = 0.0
    ratio_flag_yoy_mom = 0.0
    ratio_flag_yoy_level = 0.0
    ratio_flag_jf_share = 0.0

    # ===== ratio 特征（Phase2.8 可消融：safe_divide / log-ratio / flag） =====
    if PHASE28_SAFE_DIVIDE:
        # lead_to_potential_rate = leads / potential_customers
        lead_to_potential_rate, ratio_flag_lead_pc = _ratio_value_and_flag(
            leads, pc,
            default=0.0,
            eps=PHASE28_EPS,
            clip_low=0.0,
            clip_high=CLIP_RATE_MAX if PHASE2_ROBUST_RATIOS else None,
            use_log_ratio=False,
        )

        # potential_to_store_rate = customer_flow / potential_customers
        potential_to_store_rate, ratio_flag_flow_pc = _ratio_value_and_flag(
            flow, pc,
            default=0.0,
            eps=PHASE28_EPS,
            clip_low=0.0,
            clip_high=CLIP_RATE_MAX if PHASE2_ROBUST_RATIOS else None,
            use_log_ratio=False,
        )

        # store_to_sales_rate = sales_{t-1} / flow_{t-1}
        py1, pm1 = get_prev_year_month(year, month, 1)
        sales_prev = _map_at(getattr(dealer_data, 'sales', {}), py1, pm1)
        flow_prev = _map_at(getattr(dealer_data, 'customer_flow', {}), py1, pm1)
        sales_prev = 0.0 if sales_prev is None else float(sales_prev)
        flow_prev = 0.0 if flow_prev is None else float(flow_prev)

        # 对 store_to_sales 允许 log-ratio（R2/R3）：log1p(sales_prev)-log1p(flow_prev)
        if PHASE28_LOG_RATIO:
            store_to_sales_rate, ratio_flag_store_sales = _ratio_value_and_flag(
                sales_prev, flow_prev,
                default=0.0,
                eps=PHASE28_EPS,
                use_log_ratio=True,
                log_clip=CLIP_LOG_RATIO,
            )
        else:
            store_to_sales_rate, ratio_flag_store_sales = _ratio_value_and_flag(
                sales_prev, flow_prev,
                default=0.0,
                eps=PHASE28_EPS,
                clip_low=0.0,
                clip_high=CLIP_STORE2SALES_MAX if PHASE2_ROBUST_RATIOS else None,
                use_log_ratio=False,
            )
    else:
        # 保持 Phase2.7 原实现（R0）
        lead_to_potential_rate = (leads / pc) if pc > 0 else 0.0
        if PHASE2_ROBUST_RATIOS:
            lead_to_potential_rate = _clip(lead_to_potential_rate, 0.0, CLIP_RATE_MAX)
        potential_to_store_rate = (flow / pc) if pc > 0 else 0.0
        if PHASE2_ROBUST_RATIOS:
            potential_to_store_rate = _clip(potential_to_store_rate, 0.0, CLIP_RATE_MAX)
        store_to_sales_rate = lagged_store_to_sales_rate(dealer_data, year, month, lag=1)
        if PHASE2_ROBUST_RATIOS:
            store_to_sales_rate = _clip(store_to_sales_rate, 0.0, CLIP_STORE2SALES_MAX)

    # Step 3：销量历史特征（仅用过去月；缺失用 0）
    s_lag1 = sales_lag(dealer_data, year, month, lag=1, default=0.0)
    s_lag2 = sales_lag(dealer_data, year, month, lag=2, default=0.0)
    s_lag3 = sales_lag(dealer_data, year, month, lag=3, default=0.0)

    s_roll3_mean = sales_roll_mean(dealer_data, year, month, window=3, default=0.0)
    s_roll6_mean = sales_roll_mean(dealer_data, year, month, window=6, default=0.0)

    s_roll3_std = sales_roll_std(dealer_data, year, month, window=3, default=0.0)
    s_roll6_std = sales_roll_std(dealer_data, year, month, window=6, default=0.0)

    s_diff_1 = s_lag1 - s_lag2
    # pct_change: (lag1-lag2)/max(lag2,1)
    if PHASE28_SAFE_DIVIDE:
        denom = (s_lag2 if s_lag2 >= 1.0 else 1.0)
        s_pct_change_1, ratio_flag_pct_change = _ratio_value_and_flag(
            s_diff_1, denom,
            default=0.0,
            eps=PHASE28_EPS,
            clip_low=-CLIP_PCT_CHANGE if PHASE2_ROBUST_RATIOS else None,
            clip_high=CLIP_PCT_CHANGE if PHASE2_ROBUST_RATIOS else None,
            use_log_ratio=False,
        )
        # 若 lag2<1 触发分母保护，也视作 flag
        if s_lag2 < 1.0:
            ratio_flag_pct_change = 1.0
    else:
        s_pct_change_1 = s_diff_1 / (s_lag2 if s_lag2 >= 1.0 else 1.0)
        if PHASE2_ROBUST_RATIOS:
            s_pct_change_1 = _clip(s_pct_change_1, -CLIP_PCT_CHANGE, CLIP_PCT_CHANGE)


    d_hist_mean = dealer_hist_mean(dealer_data, year, month, default=0.0)

    # 轻量季节性编码（不依赖年份，只依赖 month 索引；不引入未来信息）
    import math
    ang = 2.0 * math.pi * (float(month) / 12.0)
    month_sin = math.sin(ang)
    month_cos = math.cos(ang)

    # ===== Phase 2：追加季节性/趋势特征（新增；严格只用过去信息）=====
    # 目标：提升旺季（尤其 12 月）稳定性；同时降低整体 WMAPE。
    # 说明：对历史不足 12 个月的早期样本，会回退到 d_hist_mean（仍只用过去信息）。
    s_lag6 = sales_lag(dealer_data, year, month, lag=6, default=d_hist_mean)
    s_lag12 = sales_lag(dealer_data, year, month, lag=12, default=d_hist_mean)

    s_roll12_mean = sales_roll_mean(dealer_data, year, month, window=12, default=d_hist_mean)
    s_roll12_std = sales_roll_std(dealer_data, year, month, window=12, default=0.0)

    s_lag13 = sales_lag(dealer_data, year, month, lag=13, default=d_hist_mean)

    # 同比/年周期锚点（Phase2.1：用 log-ratio + clip 替代 raw ratio，缓解 1/2 月（春节错位）导致的极端比率）
    if PHASE2_ROBUST_RATIOS:
        # log1p(lag12) - log1p(lag13)
        yoy_mom_ratio = _clip(_log_ratio(s_lag12, s_lag13), -CLIP_LOG_RATIO, CLIP_LOG_RATIO)
        # 用 roll12_mean 归一化的同比差，避免绝对差在高销量 dealer 上过大
        yoy_mom_diff = _clip(
            _safe_div((s_lag12 - s_lag13), (s_roll12_mean if s_roll12_mean >= 1.0 else 1.0), default=0.0, den_min=1.0),
            -CLIP_PCT_CHANGE, CLIP_PCT_CHANGE)
        # log1p(lag12) - log1p(roll12_mean)
        yoy_level_ratio = _clip(_log_ratio(s_lag12, s_roll12_mean), -CLIP_LOG_RATIO, CLIP_LOG_RATIO)
        # Phase2.8 flags：触发 clip 视作需要标记
        ratio_flag_yoy_mom = 1.0 if abs(yoy_mom_ratio) >= CLIP_LOG_RATIO else 0.0
        ratio_flag_yoy_level = 1.0 if abs(yoy_level_ratio) >= CLIP_LOG_RATIO else 0.0
    else:
        # 原始版本（可能在 1/2 月出现比率爆炸）
        yoy_mom_ratio = _safe_div(s_lag12, (s_lag13 if s_lag13 >= 1.0 else 1.0), default=0.0, den_min=1.0)
        yoy_mom_diff = s_lag12 - s_lag13
        yoy_level_ratio = _safe_div(s_lag12, (s_roll12_mean if s_roll12_mean >= 1.0 else 1.0), default=0.0, den_min=1.0)

    if PHASE2_DISABLE_YOY:
        yoy_mom_ratio = 0.0
        yoy_mom_diff = 0.0
        yoy_level_ratio = 0.0

    # =========================
    # Phase 2.2：春节错位修复（仅对 1/2 月生效）
    # =========================
    is_janfeb = 1.0 if int(month) in (1, 2) else 0.0
    janfeb_gate_active = 1.0 if (PHASE2_JANFEB_GATE and is_janfeb > 0.0) else 0.0

    # Jan/Feb gate：在 1/2 月屏蔽 yoy 派生特征（可选同时屏蔽 lag12）
    if janfeb_gate_active > 0.0:
        yoy_mom_ratio = 0.0
        yoy_mom_diff = 0.0
        yoy_level_ratio = 0.0
        if PHASE2_JANFEB_GATE_LAG12:
            # 用更“中性”的滚动均值替代（避免强行置 0 改变尺度分布）
            s_lag12 = float(s_roll12_mean)

    # 关键季节锚点的缺失/覆盖信息（用于让模型识别“填均值”与真实值的差异）
    py12, pm12 = get_prev_year_month(year, month, 12)
    py13, pm13 = get_prev_year_month(year, month, 13)
    miss_lag12 = 1.0 if _sales_at(dealer_data, py12, pm12) is None else 0.0
    miss_lag13 = 1.0 if _sales_at(dealer_data, py13, pm13) is None else 0.0

    roll12_count = 0
    for k in range(1, 13):
        py, pm = get_prev_year_month(year, month, k)
        if _sales_at(dealer_data, py, pm) is not None:
            roll12_count += 1
    roll12_coverage = float(roll12_count) / 12.0
    miss_roll12 = 1.0 if roll12_count < 12 else 0.0

    # JanFeb 2M 锚点：利用上一年 1/2 月合计及其结构，缓解春节漂移
    jf_ly_total_log = 0.0
    jf_ly_feb_share = 0.0
    jf_ly_feb_to_jan_logratio = 0.0
    jf_cur_jan_log = 0.0
    jf_cur_jan_vs_ly_jan_logdiff = 0.0
    jf_proj_feb_log = 0.0

    miss_cur_jan = 0.0
    miss_ly_jan = 0.0
    miss_ly_feb = 0.0

    if PHASE2_JANFEB_ANCHOR and is_janfeb > 0.0:
        ly_jan_raw = _sales_at(dealer_data, int(year) - 1, 1)
        ly_feb_raw = _sales_at(dealer_data, int(year) - 1, 2)
        miss_ly_jan = 1.0 if ly_jan_raw is None else 0.0
        miss_ly_feb = 1.0 if ly_feb_raw is None else 0.0

        # 用 dealer 历史均值兜底（比 0 更中性）
        ly_jan = float(d_hist_mean if ly_jan_raw is None else ly_jan_raw)
        ly_feb = float(d_hist_mean if ly_feb_raw is None else ly_feb_raw)

        ly_total = max(0.0, ly_jan + ly_feb)
        jf_ly_total_log = _clip(_log1p_safe(ly_total), 0.0, CLIP_JF_LOG)

        if PHASE28_SAFE_DIVIDE:
            jf_ly_feb_share, ratio_flag_jf_share = _ratio_value_and_flag(
                ly_feb, ly_total,
                default=0.0,
                eps=PHASE28_EPS,
                clip_low=0.0,
                clip_high=1.0,
                use_log_ratio=False,
            )
        else:
            jf_ly_feb_share = _safe_div(ly_feb, ly_total, default=0.0, den_min=1.0)
            jf_ly_feb_share = _clip(jf_ly_feb_share, 0.0, 1.0)

        jf_ly_feb_to_jan_logratio = _clip(_log_ratio(ly_feb, ly_jan), -CLIP_LOG_RATIO, CLIP_LOG_RATIO)

        # 仅对 2 月：当年 1 月销量已观测，可用来“迁移”上一年 1/2 月结构
        if int(month) == 2:
            cur_jan_raw = _sales_at(dealer_data, int(year), 1)
            miss_cur_jan = 1.0 if cur_jan_raw is None else 0.0
            cur_jan = float(s_lag1 if cur_jan_raw is None else cur_jan_raw)

            jf_cur_jan_log = _clip(_log1p_safe(cur_jan), 0.0, CLIP_JF_LOG)
            jf_cur_jan_vs_ly_jan_logdiff = _clip(_log1p_safe(cur_jan) - _log1p_safe(ly_jan), -CLIP_LOG_RATIO,
                                                 CLIP_LOG_RATIO)

            # 投影 Feb：log1p(Jan_y) + log-ratio(Feb_{y-1}/Jan_{y-1})
            jf_proj_feb_log = _clip(jf_cur_jan_log + jf_ly_feb_to_jan_logratio, 0.0, CLIP_JF_LOG)

    if not PHASE2_ADD_MISSING_FLAGS:
        miss_cur_jan = 0.0
        miss_ly_jan = 0.0
        miss_ly_feb = 0.0
        miss_lag12 = 0.0
        miss_lag13 = 0.0
        roll12_coverage = 0.0
        miss_roll12 = 0.0

    # 趋势特征（给树模型一个可分裂的“时间轴”）
    time_trend = float(make_time_key(year, month))

    # 旺季/12月指示（树模型非常吃这种“开关”变量）
    is_peak = 1.0 if int(month) in (11, 12) else 0.0
    is_dec = 1.0 if int(month) == 12 else 0.0

    if not PHASE2_SEASONAL_FEATURES:
        s_lag6 = 0.0
        s_lag12 = 0.0
        s_roll12_mean = 0.0
        s_roll12_std = 0.0
        yoy_mom_ratio = 0.0
        yoy_mom_diff = 0.0
        yoy_level_ratio = 0.0
        time_trend = 0.0
        is_peak = 0.0
        is_dec = 0.0

    # ===== Phase 2.3：覆盖断崖修复 - 追加缺失/陈旧度特征（追加在末尾，不影响前 13 维 what-if 映射）=====
    base_cur_present = float(sum((1.0 - base_miss[k]) for k, _ in _BASE_ATOMS))
    base_signal_cnt = float(sum(base_has_signal[k] for k, _ in _BASE_ATOMS))

    if PHASE23_ADD_BASE_MISSING_FLAGS:
        base_miss_out = [float(base_miss[k]) for k, _ in _BASE_ATOMS]
    else:
        base_miss_out = [0.0 for _ in _BASE_ATOMS]

    if PHASE23_ADD_BASE_STALENESS:
        base_stale_out = [float(min(base_stale[k], float(PHASE23_STALENESS_CAP))) for k, _ in _BASE_ATOMS]
    else:
        base_stale_out = [0.0 for _ in _BASE_ATOMS]

    # Phase2.4：春节（CNY）日历特征（全局，不依赖经销商；只依赖 year-month）
    cny_feats = _cny_feature_vector(int(year), int(month)) if PHASE24_CNY_FEATURES else [0.0] * CNY_FEATURE_DIM

    feats = [
        base["potential_customers"],
        base["test_drives"],
        base["leads"],
        base["customer_flow"],
        base["defeat_rate"],
        base["success_rate"],
        base["success_response_time"],
        base["defeat_response_time"],
        base["policy"],
        base["gsev"],
        lead_to_potential_rate,
        potential_to_store_rate,
        store_to_sales_rate,
        # appended historical features
        s_lag1,
        s_lag2,
        s_lag3,
        s_roll3_mean,
        s_roll6_mean,
        s_roll3_std,
        s_roll6_std,
        s_diff_1,
        s_pct_change_1,
        d_hist_mean,
        month_sin,
        month_cos,
        # ===== Phase 2：新增（追加在末尾，不影响前 13 维 what-if 映射）=====
        s_lag6,
        s_lag12,
        s_roll12_mean,
        s_roll12_std,
        yoy_mom_ratio,
        yoy_mom_diff,
        yoy_level_ratio,
        time_trend,
        is_peak,
        is_dec,
        # ===== Phase 2.2：Jan/Feb gate + JanFeb 2M 锚点 + 缺失标记（追加在末尾）=====
        is_janfeb,
        janfeb_gate_active,
        jf_ly_total_log,
        jf_ly_feb_share,
        jf_ly_feb_to_jan_logratio,
        jf_cur_jan_log,
        jf_cur_jan_vs_ly_jan_logdiff,
        jf_proj_feb_log,
        miss_cur_jan,
        miss_ly_jan,
        miss_ly_feb,
        miss_lag12,
        miss_lag13,
        roll12_coverage,
        miss_roll12,
        # Phase 2.3 appended (coverage / missingness)
        base_cur_present,
        base_signal_cnt,
        *base_miss_out,
        *base_stale_out,
        *cny_feats,
    ]

    # Phase2.8：ratio missing/clip flags（默认关闭；仅 R3 开启）
    if PHASE28_MISSING_FLAG:
        feats.extend([
            float(ratio_flag_lead_pc),
            float(ratio_flag_flow_pc),
            float(ratio_flag_store_sales),
            float(ratio_flag_pct_change),
            float(ratio_flag_yoy_mom),
            float(ratio_flag_yoy_level),
            float(ratio_flag_jf_share),
        ])

    return feats



# =========================
# 模型参数
# =========================
def _get_default_xgb_params(mode: str) -> dict:
    # Phase 3.2: 目标函数对齐为绝对误差 (L1 损失)，更贴合 WMAPE
    # 替换对应的字典构建逻辑
    common = dict(
        objective="reg:absoluteerror" if PHASE32_LOSS_L1 else "reg:squarederror",
        eval_metric="mae" if PHASE32_LOSS_L1 else "rmse",
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )

    if mode == "advanced":
        return dict(
            **common,
            learning_rate=0.05,
            n_estimators=900,
            max_depth=5,
            min_child_weight=2,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=2.0,
            reg_alpha=0.5,
            gamma=0.2,
        )

    if mode == "standard":
        return dict(
            **common,
            learning_rate=0.06,
            n_estimators=650,
            max_depth=4,
            min_child_weight=3,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=3.0,
            reg_alpha=0.8,
            gamma=0.3,
        )

    # conservative
    return dict(
        **common,
        learning_rate=0.08,
        n_estimators=450,
        max_depth=3,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=5.0,
        reg_alpha=1.0,
        gamma=0.5,
    )


def _get_param_dist_for_search(mode: str) -> dict:
    if mode == "advanced":
        return {
            "model__learning_rate": uniform(0.01, 0.12),
            "model__max_depth": [3, 4, 5, 6],
            "model__n_estimators": [400, 700, 900, 1300],
            "model__min_child_weight": [1, 2, 3, 5, 8],
            "model__subsample": uniform(0.6, 0.4),
            "model__colsample_bytree": uniform(0.6, 0.4),
            "model__reg_lambda": uniform(1.0, 8.0),
            "model__reg_alpha": uniform(0.0, 2.0),
            "model__gamma": uniform(0.0, 1.0),
            "alpha": uniform(0.0, 2.5)  # 用于复合得分
        }

    # standard
    return {
        "model__learning_rate": uniform(0.01, 0.10),
        "model__max_depth": [3, 4, 5],
        "model__n_estimators": [250, 450, 650, 950],
        "model__min_child_weight": [2, 3, 5, 8],
        "model__subsample": uniform(0.65, 0.35),
        "model__colsample_bytree": uniform(0.65, 0.35),
        "model__reg_lambda": uniform(1.0, 6.0),
        "model__reg_alpha": uniform(0.0, 1.5),
        "model__gamma": uniform(0.0, 0.8),
        "alpha": uniform(0.0, 2.5)  # 用于复合得分
    }


# =========================
# Step 4：dealer_bias_（严格按训练窗口统计）
# =========================
def _fit_dealer_bias(
        y_log: np.ndarray,
        yhat_log: np.ndarray,
        dealer_codes: np.ndarray,
        min_count: int = 1,
        shrink_alpha: float = 0.0,
) -> dict:
    """
    b_d = E[y_log - yhat_log | dealer=d]
    可选 shrink：b_d = sum(res) / (n + shrink_alpha)（小样本更稳）
    """
    sum_res = defaultdict(float)
    cnt = defaultdict(int)
    for d, r in zip(dealer_codes, (y_log - yhat_log)):
        sum_res[str(d)] += float(r)
        cnt[str(d)] += 1

    bias = {}
    for d in sum_res.keys():
        n = cnt[d]
        if n < min_count:
            continue
        denom = float(n + max(shrink_alpha, 0.0))
        bias[d] = float(sum_res[d] / denom) if denom > 0 else 0.0
    return bias


# =========================
# Phase3.1: Tuning 接口（Optuna / Random Search）
# - prepare_training_data(): 只做一次特征展开
# - rolling_backtest_prepared(): 给定一组 xgb_params，跑 time_key rolling，返回 rows/summary
# 说明：此处默认不引入“早停”，保证与当前 train_model 的训练逻辑一致；
#      如需早停，可在 Phase3.2 再引入（避免 Phase3.1 变量过多难归因）。
# =========================

@dataclass
class PreparedData:
    X_raw: np.ndarray
    y_raw: np.ndarray
    y_log: np.ndarray
    time_keys: np.ndarray
    dealer_codes: np.ndarray
    feature_dim: int


def prepare_training_data(dealers) -> PreparedData:
    """把 dealers 字典展开成训练矩阵（与 train_model 内部保持一致）。"""
    X_raw = []
    y_raw = []
    time_keys = []
    dealer_codes = []

    for dealer_code, dealer_data in dealers.items():
        sales_map = getattr(dealer_data, "sales", {}) or {}
        tuple_keys = [k for k in sales_map.keys() if isinstance(k, tuple) and len(k) == 2]

        if tuple_keys:
            keys_iter = tuple_keys
        else:
            # 兼容旧 month-key：默认认为 year=2024
            keys_iter = [(2024, int(m)) for m in sales_map.keys() if isinstance(m, (int, np.integer))]

        for year, month in keys_iter:
            if _has_required_month_fields(dealer_data, int(year), int(month), include_target=True):
                X_raw.append(build_features(dealer_data, int(year), int(month)))
                yv = _sales_at(dealer_data, int(year), int(month))
                if yv is None:
                    continue
                y_raw.append(float(yv))
                time_keys.append(make_time_key(int(year), int(month)))
                dealer_codes.append(str(dealer_code))

    if len(X_raw) == 0:
        raise ValueError("未构造出任何训练样本：请检查 dealers 数据是否包含足够月份的完整字段。")

    X_raw = np.asarray(X_raw, dtype=float)
    y_raw = np.asarray(y_raw, dtype=float)
    time_keys = np.asarray(time_keys, dtype=int)
    dealer_codes = np.asarray(dealer_codes, dtype=str)
    y_log = _to_log_target(y_raw)

    return PreparedData(
        X_raw=X_raw,
        y_raw=y_raw,
        y_log=y_log,
        time_keys=time_keys,
        dealer_codes=dealer_codes,
        feature_dim=int(X_raw.shape[1]) if X_raw.ndim == 2 else 0,
    )


def rolling_backtest_prepared(
        prep: PreparedData,
        xgb_params: dict,
        *,
        last_n_folds: int | None = None,
        quiet: bool = True,
) -> tuple[list[dict], dict]:
    """给定参数跑 time_key rolling（与 train_model 内 rolling 同协议）。"""
    X_raw = prep.X_raw
    y_raw = prep.y_raw
    y_log = prep.y_log
    time_keys = prep.time_keys
    dealer_codes = prep.dealer_codes

    # Phase 3.2 修复写死的 objective，对齐绝对误差
    common = dict(objective="reg:absoluteerror" if PHASE32_LOSS_L1 else "reg:squarederror", eval_metric="mae" if PHASE32_LOSS_L1 else "rmse", random_state=42, n_jobs=-1, tree_method="hist")
    params = dict(common)
    if isinstance(xgb_params, dict):
        params.update(xgb_params)

    pipe = Pipeline([("scaler", MinMaxScaler()), ("model", xgb.XGBRegressor(**params))])

    uniq_t = np.unique(time_keys)
    uniq_t = np.array(sorted([int(t) for t in uniq_t]), dtype=int)
    fold_rows: list[dict] = []
    best_iters: list[int] = []

    start_idx = int(ROLL_MIN_TRAIN_PERIODS + ROLL_GAP)
    if last_n_folds is not None and int(last_n_folds) > 0:
        start_idx = max(start_idx, len(uniq_t) - int(last_n_folds))

    for idx in range(start_idx, len(uniq_t)):
        test_t = int(uniq_t[idx])

        train_end = idx - ROLL_GAP
        if train_end <= 0:
            continue

        if ROLL_MODE == "sliding":
            train_start = max(0, train_end - int(ROLL_WINDOW_MONTHS))
        else:
            train_start = 0

        train_times = uniq_t[train_start:train_end]
        train_mask = np.isin(time_keys, train_times)
        test_mask = time_keys == test_t
        if np.sum(train_mask) == 0 or np.sum(test_mask) == 0:
            continue


        # Phase 3.2: 引入销量权重进行训练折拟合
        weights_train = np.expm1(y_log[train_mask]) if PHASE32_USE_WEIGHT else None
        weights_test = np.expm1(y_log[test_mask]) if PHASE32_USE_WEIGHT else None

        # --- 方案 A：禁用 Early Stopping，保证与最终训练一致，且避免 test fold 泄漏 ---
        pipe_fold = clone(pipe)
        pipe_fold.fit(
            X_raw[train_mask],
            y_log[train_mask],
            model__sample_weight=weights_train
        )
        best_iters.append(int(params.get("n_estimators", 0)))

        # train residual -> dealer bias（仅训练窗口）
        yhat_train_log = pipe_fold.predict(X_raw[train_mask])

        if PHASE_STORE_CALIB:
            bias = _fit_dealer_bias(
                y_log=y_log[train_mask],
                yhat_log=yhat_train_log,
                dealer_codes=dealer_codes[train_mask],
                shrink_alpha=0.0,
            )
        else:
            bias = None
        # test predict -> bias -> inverse
        yhat_test_log = pipe_fold.predict(X_raw[test_mask])
        yhat_test_log_cal = _apply_dealer_bias(yhat_test_log, dealer_codes[test_mask], bias)
        yhat_sales = _from_log_target(yhat_test_log_cal)

        y_true = y_raw[test_mask]
        y_pred = yhat_sales
        sum_abs_y = float(np.sum(np.abs(y_true)))

        wmape_t = _wmape(y_true, y_pred)
        smape_t = _smape(y_true, y_pred)
        mae_t = float(np.mean(np.abs(y_true - y_pred)))
        rmse_t = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

        y_t, m_t = time_key_to_ym(test_t)
        if not quiet:
            print(
                f"[tune] Test {y_t}-{m_t:02d} | n={int(len(y_true))} | sum|y|={sum_abs_y:.2f} | "
                f"WMAPE={wmape_t:.2f}% | SMAPE={smape_t:.2f}% | MAE={mae_t:.2f} | RMSE={rmse_t:.2f}"
            )

        fold_rows.append(
            {
                "time_key": int(test_t),
                "year": int(y_t),
                "month": int(m_t),
                "n_test": int(len(y_true)),
                "sum_abs_y": float(sum_abs_y),
                "wmape": float(wmape_t),
                "smape": float(smape_t),
                "mae": float(mae_t),
                "rmse": float(rmse_t),
            }
        )

    if not fold_rows:
        return [], {}

    wmapes = np.array([r["wmape"] for r in fold_rows], dtype=float)
    dec_wmapes = np.array([r["wmape"] for r in fold_rows if r["month"] == 12], dtype=float)
    peak_wmapes = np.array([r["wmape"] for r in fold_rows if r["month"] in (11, 12)], dtype=float)

    summary = {
        "roll_mode": str(ROLL_MODE),
        "roll_window_months": int(ROLL_WINDOW_MONTHS),
        "roll_min_train_periods": int(ROLL_MIN_TRAIN_PERIODS),
        "roll_gap": int(ROLL_GAP),
        "n_folds": int(len(fold_rows)),
        "wmape_mean": float(np.nanmean(wmapes)),
        "wmape_std": float(np.nanstd(wmapes)),
        "wmape_dec_mean": float(np.nanmean(dec_wmapes)) if len(dec_wmapes) else float("nan"),
        "wmape_dec_std": float(np.nanstd(dec_wmapes)) if len(dec_wmapes) else float("nan"),
        "wmape_peak_mean": float(np.nanmean(peak_wmapes)) if len(peak_wmapes) else float("nan"),
        "wmape_peak_std": float(np.nanstd(peak_wmapes)) if len(peak_wmapes) else float("nan"),
        "optimal_trees": int(np.mean(best_iters)) if best_iters else params.get("n_estimators", 400),
    }

    return fold_rows, summary

def _parse_int_list(csv: str) -> list[int]:
    out = []
    for p in (csv or "").split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except Exception:
            pass
    return out


def select_n_estimators_by_grid(
    prep: PreparedData,
    base_params: dict,
    *,
    trees_grid_csv: str,
    trade_off_weight: float,
    quiet: bool = True,
) -> tuple[int, list[dict]]:
    """
    固定除 n_estimators 外的参数，用小网格选择树数：
      score = wmape_mean + trade_off_weight * wmape_peak_std
    返回：best_trees, rows（可用于落盘/画图）
    """
    grid = _parse_int_list(trees_grid_csv)
    if not grid:
        grid = [450, 650, 900, 1150]

    rows: list[dict] = []
    best_score = float("inf")
    best_trees = int(base_params.get("n_estimators", grid[0]))

    for n in grid:
        p = dict(base_params)
        p["n_estimators"] = int(n)

        _, summ = rolling_backtest_prepared(prep, xgb_params=p, quiet=quiet)
        wm = float(summ.get("wmape_mean", 1e9))
        ps = float(summ.get("wmape_peak_std", 1e9))
        score = wm + float(trade_off_weight) * ps

        rows.append({
            "n_estimators": int(n),
            "wmape_mean": wm,
            "peak_std": ps,
            "score": score,
        })

        if score < best_score:
            best_score = score
            best_trees = int(n)

    rows = sorted(rows, key=lambda r: r["score"])
    return best_trees, rows


def _apply_dealer_bias(
        yhat_log: np.ndarray,
        dealer_codes: np.ndarray,
        bias_dict: dict | None,
) -> np.ndarray:
    if not bias_dict:
        return yhat_log
    out = np.array(yhat_log, dtype=float, copy=True)
    for i, d in enumerate(dealer_codes):
        bd = bias_dict.get(str(d), 0.0)
        out[i] += float(bd)
    return out


# =========================
# train_model：接口不变，但内部使用 log1p 目标 + dealer_bias_ 校准
# =========================
def train_model(dealers, xgb_params_override: dict | None = None, skip_kfold: bool = False, quiet: bool = False):
    """
    返回值保持与原代码一致：
      best_model, scaler, X, y, y_pred

    - best_model：仍返回 xgb.XGBRegressor，并附加：
        best_model.target_transform_ = "log1p"
        best_model.dealer_bias_ = {dealer_code: bias_in_log_space}
    - y / y_pred：保持“销量原尺度”（sales），避免前端/绘图逻辑被破坏
    """
    import sklearn
    import time
    from sklearn.model_selection import KFold
    from sklearn.pipeline import Pipeline
    import xgboost as xgb

    print("训练开始...")
    t0 = time.time()

    all_atom_values = {k: [] for k, _ in _BASE_ATOMS}
    for _, d_data in dealers.items():
        for _, attr in _BASE_ATOMS:
            mp = getattr(d_data, attr, {}) or {}
            for val in mp.values():
                if not _is_nan(val): all_atom_values[attr].append(float(val))

    global_medians = {k: (float(np.median(v)) if v else 0.0) for k, v in all_atom_values.items()}
    if not quiet: print(f"已计算全局中位数作为三级填补: {global_medians}")

    X_raw = []
    y_raw = []
    time_keys = []
    dealer_codes = []

    # 收集训练样本：默认 1..10（与你当前实现一致）
    for dealer_code, dealer_data in dealers.items():
        sales_map = getattr(dealer_data, "sales", {}) or {}
        tuple_keys = [k for k in sales_map.keys() if isinstance(k, tuple) and len(k) == 2]

        if tuple_keys:
            keys_iter = tuple_keys
        else:
            # 兼容旧 month-key：默认认为 year=2024
            keys_iter = [(2024, int(m)) for m in sales_map.keys() if isinstance(m, (int, np.integer))]

        for year, month in keys_iter:
            if _has_required_month_fields(dealer_data, int(year), int(month), include_target=True):
                feat = build_features(dealer_data, int(year), int(month), overrides=None, global_medians=global_medians)
                X_raw.append(feat)
                # 删除了多余的 append
                yv = _sales_at(dealer_data, int(year), int(month))
                if yv is None:
                    continue
                y_raw.append(float(yv))
                time_keys.append(make_time_key(int(year), int(month)))
                dealer_codes.append(str(dealer_code))

    if len(X_raw) == 0:
        raise ValueError("未构造出任何训练样本：请检查 dealers 数据是否包含 1-10 月的完整字段。")

    # ====== 关键修复：把 list 全部转为 numpy array，才能用 train_idx/test_idx 切片 ======
    X_raw = np.asarray(X_raw, dtype=float)  # shape: (N, d)
    y_raw = np.asarray(y_raw, dtype=float)  # shape: (N,)
    time_keys = np.asarray(time_keys, dtype=int)  # shape: (N,)  # year-month time axis
    dealer_codes = np.asarray(dealer_codes, dtype=str)  # shape: (N,)

    # Step 2：log1p 训练目标
    y_log = _to_log_target(y_raw)

    # =========================
    # 1) KFold CV（整体稳定性）
    # =========================
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)

    base_model = xgb.XGBRegressor(**{**_get_default_xgb_params(TRAIN_MODE), **(xgb_params_override or {})})
    pipe = Pipeline([("scaler", MinMaxScaler()), ("model", base_model)])

    if skip_kfold:
        # ✅ 修复目标：只跳过 KFold/搜参，不跳过后面的 rolling 回测
        # 说明：rolling 依赖 best_pipe（clone(best_pipe)），所以这里必须把 best_pipe 准备好
        best_pipe = pipe

        # 给返回值占位：做一次全量 in-sample 预测（不作为评估口径；主评估看 rolling_rows_/rolling_summary_）
        weights_full = np.expm1(y_log) if PHASE32_USE_WEIGHT else None
        best_pipe.fit(X_raw, y_log, model__sample_weight=weights_full)

        yhat_log_full = best_pipe.predict(X_raw)

        if PHASE_STORE_CALIB:
            bias_full = _fit_dealer_bias(
                y_log=y_log,
                yhat_log=yhat_log_full,
                dealer_codes=dealer_codes,
                shrink_alpha=0.0,
            )
            yhat_log_full_cal = _apply_dealer_bias(yhat_log_full, dealer_codes, bias_full)
        else:
            bias_full = None
            yhat_log_full_cal = yhat_log_full

        y_pred_sales = _from_log_target(yhat_log_full_cal)

        if not quiet:
            print("************************ skip_kfold=True：已跳过 KFold（仍会执行 rolling 回测）**********************")
            print(f"TRAIN_MODE: {TRAIN_MODE}")
            print(f"XGB override: {xgb_params_override or {} }")

    else:

        if TRAIN_MODE in ("standard", "advanced") and not xgb_params_override:
            import optuna
            import pandas as pd
            print("************************ 启动 Optuna 多目标智能搜索 **********************")
            print(f"TRAIN_MODE: {TRAIN_MODE}")

            prep_data = PreparedData(
                X_raw=X_raw, y_raw=y_raw, y_log=y_log,
                time_keys=time_keys, dealer_codes=dealer_codes, feature_dim=X_raw.shape[1]
            )

            def objective(trial):
                params = {
                    "objective": "reg:absoluteerror" if PHASE32_LOSS_L1 else "reg:squarederror",
                    "eval_metric": "mae" if PHASE32_LOSS_L1 else "rmse",
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.12, log=True),
                    "max_depth": trial.suggest_int("max_depth", 3, 7),
                    "n_estimators": PHASE34_BASE_TREES,
                    "min_child_weight": trial.suggest_int("min_child_weight", 1, 8),
                    "subsample": trial.suggest_float("subsample", 0.4, 0.9),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 0.9),
                    "reg_lambda": trial.suggest_float("reg_lambda", 1.0, 8.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 2.0),
                    "gamma": trial.suggest_float("gamma", 0.0, 1.0),
                    "tree_method": "hist",
                    "random_state": 42
                }

                # 跑严格的时序验证
                _, summary = rolling_backtest_prepared(prep_data, xgb_params=params, quiet=True)
                wmape = summary.get("wmape_mean", 100.0)
                peak_std = summary.get("wmape_peak_std", 100.0)
                trial.set_user_attr("optimal_trees", summary.get("optimal_trees", params["n_estimators"]))

                # 防御 NaN 或 None 导致复合得分计算异常，直接赋予高额惩罚值
                if peak_std is None or np.isnan(peak_std):
                    peak_std = 100.0

                # ========== 完美对齐论文：计算复合得分 (Composite Score) ==========
                # 把这三个关键指标都记录进 Trial 的扩展属性里，方便后面导出 CSV 画图
                trial.set_user_attr("wmape", wmape)
                trial.set_user_attr("peak_std", peak_std)

                # Optuna 执行双目标优化（寻找 Pareto 前沿）
                return wmape, peak_std

            # 开启双目标优化
            study = optuna.create_study(
                study_name="sales_forecast_tuning_phase1",
                storage="sqlite:///optuna_journal.db",
                load_if_exists=True,
                directions=["minimize", "minimize"]
            )

            n_trials = OPTUNA_N_TRIALS

            save_dir = r"E:\07Journals\experiment\Optunaphase1"
            os.makedirs(save_dir, exist_ok=True)
            realtime_csv_path = os.path.join(save_dir, "optuna_realtime_backup.csv")

            def backup_callback(study, trial):
                """每完成一次 trial，就自动将结果写入 CSV，充当实时存档"""
                import pandas as pd
                df = study.trials_dataframe()
                df = df.rename(columns={"values_0": "WMAPE", "values_1": "Peak_Std"})
                if "WMAPE" in df.columns and "Peak_Std" in df.columns:
                    df["Composite_Score"] = df["WMAPE"] + TRADE_OFF_WEIGHT * df["Peak_Std"]
                    df = df.sort_values(by="Composite_Score")
                df.to_csv(realtime_csv_path, index=False, encoding='utf-8-sig')

            optuna.logging.set_verbosity(optuna.logging.WARNING)
            print(f"开始 {n_trials} 轮双目标滚动搜索...")
            print(f"实时备份路径(CSV)：{realtime_csv_path}")
            print(f"实时断点续传库(DB)：当前目录下的 optuna_journal.db")

            study.optimize(objective, n_trials=n_trials, show_progress_bar=True, callbacks=[backup_callback])
            print("************************ Optuna 搜索完成 **********************")

            # 最终读取并保存最终版
            df_final = study.trials_dataframe()
            df_final = df_final.rename(columns={"values_0": "WMAPE", "values_1": "Peak_Std"})
            if "WMAPE" in df_final.columns and "Peak_Std" in df_final.columns:
                df_final["Composite_Score"] = df_final["WMAPE"] + TRADE_OFF_WEIGHT * df_final["Peak_Std"]
                df_final = df_final.sort_values(by="Composite_Score")

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            final_csv_path = os.path.join(save_dir, f"optuna_final_results_{timestamp}.csv")
            df_final.to_csv(final_csv_path, index=False, encoding='utf-8-sig')
            print(f"✅ Optuna 最终实验记录已保存至：{final_csv_path}")
            # ========== 完美对齐论文：基于固定商业权衡挑选最终模型 ==========
            best_trials = study.best_trials

            def calc_fixed_composite(t):
                # t.values[0] 是 wmape, t.values[1] 是 peak_std
                return t.values[0] + TRADE_OFF_WEIGHT * t.values[1]

            # 在帕累托前沿的优胜者中，挑选固定权重下得分最小的一组
            best_trial = min(best_trials, key=calc_fixed_composite)
            final_composite_score = calc_fixed_composite(best_trial)

            print(f"\n✅ 帕累托最优解挑选完毕 (Trade-off Weight = {TRADE_OFF_WEIGHT}):")
            print(f"最终采纳的参数组合: {best_trial.params}")
            print(
                f"对应的性能指标: WMAPE = {best_trial.values[0]:.2f}%, Peak Std = {best_trial.values[1]:.2f}, 最终复合得分 = {final_composite_score:.2f}"
            )

            # 把这组“复合得分最佳”的参数塞进后续流程
            best_params = dict(_get_default_xgb_params(TRAIN_MODE))
            best_params.update(best_trial.params)

            # ===== Phase3.4：小网格定树数（只做一次，不放进 Optuna trial 循环）=====
            best_trees, grid_rows = select_n_estimators_by_grid(
                prep_data,
                best_params,
                trees_grid_csv=PHASE34_TREES_GRID,
                trade_off_weight=TRADE_OFF_WEIGHT,
                quiet=True,
            )
            best_params["n_estimators"] = int(best_trees)
            print(f"🔥 [小网格定树数] best n_estimators={best_trees} | top1={grid_rows[0] if grid_rows else None}")

            best_model_opt = xgb.XGBRegressor(**best_params)
            best_pipe = Pipeline([("scaler", MinMaxScaler()), ("model", best_model_opt)])

        else:
            print("************************ 使用保守档位训练（不进行搜参）：**********************")
            print(f"TRAIN_MODE: {TRAIN_MODE}")
            best_pipe = pipe

        # KFold 逐折预测（严格：bias 只用 train fold 统计）
        y_pred_sales = np.empty_like(y_raw)
        for train_idx, test_idx in kfold.split(X_raw, y_log):
            weights_train_kf = np.expm1(y_log[train_idx]) if PHASE32_USE_WEIGHT else None
            best_pipe.fit(X_raw[train_idx], y_log[train_idx], model__sample_weight=weights_train_kf)

            # 训练折 in-sample 预测 -> 统计 dealer_bias（仅训练折）
            yhat_train_log = best_pipe.predict(X_raw[train_idx])
            if PHASE_STORE_CALIB:
                bias_fold = _fit_dealer_bias(
                    y_log=y_log[train_idx],
                    yhat_log=yhat_train_log,
                    dealer_codes=dealer_codes[train_idx],
                    shrink_alpha=0.0,
                )
            else:
                bias_fold = None

            # 测试折预测 + bias + inverse
            yhat_test_log = best_pipe.predict(X_raw[test_idx])
            yhat_test_log_cal = _apply_dealer_bias(yhat_test_log, dealer_codes[test_idx], bias_fold)
            y_pred_sales[test_idx] = _from_log_target(yhat_test_log_cal)

        # 指标：在销量原尺度上算（论文/业务解释统一）
        overall_r2 = r2_score(y_raw, y_pred_sales)
        mae = mean_absolute_error(y_raw, y_pred_sales)
        rmse = float(np.sqrt(mean_squared_error(y_raw, y_pred_sales)))
        medae = median_absolute_error(y_raw, y_pred_sales)
        smape = _smape(y_raw, y_pred_sales)
        wmape = _wmape(y_raw, y_pred_sales)

        print("\n===== KFold CV 指标（销量原尺度）=====")
        print(f"样本量 N={len(y_raw)}, 特征维度 d={X_raw.shape[1]}")
        print(f"R²   : {overall_r2:.4f}")
        print(f"MAE  : {mae:.4f}")
        print(f"RMSE : {rmse:.4f}")
        print(f"MedAE: {medae:.4f}")
        print(f"SMAPE: {smape:.2f}%")
        print(f"WMAPE: {wmape:.2f}%")

        # =========================
    # 2) Rolling 多折回测（主评估，严格时间因果）
    # =========================

    # =========================
    # 2) Rolling 多折回测（主评估，严格时间因果：train_time < test_time）
    # =========================
    from sklearn.base import clone

    def _rolling_backtest_timekey():
        """
        以唯一月份(time_key)为折，逐月向前滚动：
        - expanding: 训练窗从起点不断扩张
        - sliding:   固定窗口长度（ROLL_WINDOW_MONTHS）
        - gap:       训练与测试之间留空 (ROLL_GAP) 个月，降低泄露风险（可选）
        """
        uniq_t = np.sort(np.unique(time_keys))
        if len(uniq_t) <= (ROLL_MIN_TRAIN_PERIODS + ROLL_GAP):
            print(
                f"Rolling: unique months={len(uniq_t)} 不足以启动回测（min_train={ROLL_MIN_TRAIN_PERIODS}, gap={ROLL_GAP}）。"
            )
            return [], {}

        fold_rows = []
        # idx 指向测试月在 uniq_t 的位置
        for idx in range(ROLL_MIN_TRAIN_PERIODS + ROLL_GAP, len(uniq_t)):
            test_t = int(uniq_t[idx])

            train_end = idx - ROLL_GAP  # 训练窗包含 [0, train_end)
            if train_end <= 0:
                continue

            if ROLL_MODE == "sliding":
                train_start = max(0, train_end - int(ROLL_WINDOW_MONTHS))
            else:
                train_start = 0

            train_times = uniq_t[train_start:train_end]
            train_mask = np.isin(time_keys, train_times)
            test_mask = time_keys == test_t
            if np.sum(train_mask) == 0 or np.sum(test_mask) == 0:
                continue

            rolling_pipe = clone(best_pipe)
            weights_train_roll = np.expm1(y_log[train_mask]) if PHASE32_USE_WEIGHT else None
            rolling_pipe.fit(X_raw[train_mask], y_log[train_mask], model__sample_weight=weights_train_roll)

            # train residual -> dealer bias（仅训练窗口）
            yhat_train_log = rolling_pipe.predict(X_raw[train_mask])
            if PHASE_STORE_CALIB:
                bias = _fit_dealer_bias(
                    y_log=y_log[train_mask],
                    yhat_log=yhat_train_log,
                    dealer_codes=dealer_codes[train_mask],
                    shrink_alpha=0.0,
                )
            else:
                bias = None

            # test predict -> bias -> inverse
            yhat_test_log = rolling_pipe.predict(X_raw[test_mask])
            yhat_test_log_cal = _apply_dealer_bias(yhat_test_log, dealer_codes[test_mask], bias)
            yhat_sales = _from_log_target(yhat_test_log_cal)

            y_true = y_raw[test_mask]
            y_pred = yhat_sales
            sum_abs_y = float(np.sum(np.abs(y_true)))

            wmape_t = _wmape(y_true, y_pred)
            smape_t = _smape(y_true, y_pred)
            mae_t = float(np.mean(np.abs(y_true - y_pred)))
            rmse_t = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

            y_t, m_t = time_key_to_ym(test_t)
            print(
                f"Test {y_t}-{m_t:02d} | n={int(len(y_true))} | sum|y|={sum_abs_y:.2f} | WMAPE={wmape_t:.2f}% | SMAPE={smape_t:.2f}% | MAE={mae_t:.2f} | RMSE={rmse_t:.2f}"
            )

            fold_rows.append(
                {
                    "time_key": int(test_t),
                    "year": int(y_t),
                    "month": int(m_t),
                    "n_test": int(len(y_true)),
                    "sum_abs_y": float(sum_abs_y),
                    "wmape": float(wmape_t),
                    "smape": float(smape_t),
                    "mae": float(mae_t),
                    "rmse": float(rmse_t),
                }
            )

        if not fold_rows:
            return [], {}

        wmapes = np.array([r["wmape"] for r in fold_rows], dtype=float)
        dec_wmapes = np.array([r["wmape"] for r in fold_rows if r["month"] == 12], dtype=float)
        peak_wmapes = np.array([r["wmape"] for r in fold_rows if r["month"] in (11, 12)], dtype=float)

        summary = {
            "roll_mode": str(ROLL_MODE),
            "roll_window_months": int(ROLL_WINDOW_MONTHS),
            "roll_min_train_periods": int(ROLL_MIN_TRAIN_PERIODS),
            "roll_gap": int(ROLL_GAP),
            "n_folds": int(len(fold_rows)),
            "wmape_mean": float(np.nanmean(wmapes)),
            "wmape_std": float(np.nanstd(wmapes)),
            "wmape_dec_mean": float(np.nanmean(dec_wmapes)) if len(dec_wmapes) else float("nan"),
            "wmape_dec_std": float(np.nanstd(dec_wmapes)) if len(dec_wmapes) else float("nan"),
            "wmape_peak_mean": float(np.nanmean(peak_wmapes)) if len(peak_wmapes) else float("nan"),
            "wmape_peak_std": float(np.nanstd(peak_wmapes)) if len(peak_wmapes) else float("nan"),
        }

        print("\n[Rolling Summary]")
        print(
            f"WMAPE mean±std: {summary['wmape_mean']:.2f}% ± {summary['wmape_std']:.2f}% | "
            f"Dec mean±std: {summary['wmape_dec_mean']:.2f}% ± {summary['wmape_dec_std']:.2f}% | "
            f"Peak(11/12) mean±std: {summary['wmape_peak_mean']:.2f}% ± {summary['wmape_peak_std']:.2f}%"
        )

        # 月份聚合（按 month-of-year）
        by_m = {}
        for m in range(1, 13):
            vals = [r["wmape"] for r in fold_rows if r["month"] == m]
            if vals:
                by_m[m] = float(np.mean(vals))
        if by_m:
            s = " | ".join([f"{m:02d}:{by_m[m]:.1f}%" for m in sorted(by_m.keys())])
            print("WMAPE by month-of-year:", s)

        return fold_rows, summary

    rolling_rows, rolling_summary = _rolling_backtest_timekey()

    # =========================
    # 3) 最终训练（返回裸 model + 全量 scaler；并附加 dealer_bias_）
    # =========================
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # 取出“裸模型”并在 log 目标上重新 fit
    if hasattr(best_pipe, "named_steps"):
        best_model = best_pipe.named_steps["model"]
    else:
        best_model = base_model

    # Phase 3.2: 最终训练也必须挂载实际销量权重
    # 加入消融开关判断
    final_weights = np.expm1(y_log) if PHASE32_USE_WEIGHT else None
    best_model.fit(X_scaled, y_log, sample_weight=final_weights)

    # 在全训练集上统计 dealer_bias_（log 空间）
    yhat_log_full = best_model.predict(X_scaled)

    if PHASE_STORE_CALIB:
        dealer_bias_full = _fit_dealer_bias(
            y_log=y_log,
            yhat_log=yhat_log_full,
            dealer_codes=dealer_codes,
            shrink_alpha=0.0,
        )
    else:
        dealer_bias_full = None

    # 挂载到模型对象上（不改 main 也能拿到）
    best_model.target_transform_ = "log1p"
    best_model.dealer_bias_ = dealer_bias_full

    # 可选：把 rolling 回测结果挂到模型对象上，便于外部脚本导出报表（不影响 main）
    best_model.rolling_rows_ = rolling_rows
    best_model.rolling_summary_ = rolling_summary

    print(f"\n训练与评估耗时: {time.time() - t0:.2f}s")
    # Phase3.0: attach resolved config snapshot for reproducibility (no effect on inference)
    try:
        best_model.config_ = get_runtime_config()
    except Exception:
        pass

    return best_model, scaler, X_scaled, y_raw, y_pred_sales


# =========================
# predict_sales_change：接口不变，但内部做 log 预测 + dealer bias + inverse
# =========================
def predict_sales_change(best_model, scaler, dealers, dealer_code, dimension, change_percentage, month=None, year=2024):
    """
    返回值保持与原代码一致：
      original_sales(dict), y_changed(np.array)

    关键点：
    - 预测端如果检测到 best_model.target_transform_ == "log1p"：
        y_hat_log -> (+dealer_bias_) -> expm1 -> y_hat_sales
    - what-if：仍在“原始特征空间”改原子维度，历史特征保持由历史月计算
    """
    dealer_data = dealers.get(dealer_code)
    if not dealer_data:
        print(f"未找到经销商代码 {dealer_code} 的数据。")
        return None, None

    # 原销量（可能未来月缺失 -> None）
    sales_map = getattr(dealer_data, "sales", {}) or {}
    original_sales = {m: _map_at(sales_map, year, m) for m in range(1, 11)}

    print(f"经销商 {dealer_code} 的数据：")
    for m, s in original_sales.items():
        if s is not None:
            print(f"第 {m} 月销量: {s}")

    if month is None:
        months_to_process = range(1, 11)
    else:
        months_to_process = [month]

    # 维度映射仅覆盖“原 13 维”，新增历史特征不参与 what-if 维度选择
    dimension_index_map = {
        "potential_customers": 0,
        "test_drives": 1,
        "leads": 2,
        "customer_flow": 3,
        "defeat_rate": 4,
        "success_rate": 5,
        "success_response_time": 6,
        "defeat_response_time": 7,
        "policy": 8,
        "gsev": 9,
        "lead_to_potential_rate": 10,
        "potential_to_store_rate": 11,
        "store_to_sales_rate": 12,
    }

    if dimension not in dimension_index_map:
        print(f"无效的维度 '{dimension}'，请确保输入正确。")
        return None, None

    atomic_dims = {
        "potential_customers", "test_drives", "leads", "customer_flow",
        "defeat_rate", "success_rate", "success_response_time", "defeat_response_time",
        "policy", "gsev"
    }

    X_raw_original_list = []
    X_raw_changed_list = []
    valid_months = []

    # ========== 请用以下代码替换原有的 for m in months_to_process: 循环 ==========
    for m in months_to_process:
        # 预测阶段不要求当月销量存在，但当月特征必须齐全
        if not _has_required_month_fields(dealer_data, year, m, include_target=False):
            continue

        # 1. 必须先计算原始特征 (feats_orig)
        feats_orig = build_features(dealer_data, year, m, overrides=None, global_medians=None)

        # 2. 根据原始特征和修改比例，构造 overrides 字典
        overrides = None
        if dimension in atomic_dims:
            overrides = {
                dimension: feats_orig[dimension_index_map[dimension]] * (1.0 + change_percentage / 100.0)
            }
        else:
            if dimension == "lead_to_potential_rate":
                pc = feats_orig[0]
                cur_rate = feats_orig[10]
                target_rate = cur_rate * (1.0 + change_percentage / 100.0)
                overrides = {"leads": target_rate * pc}
            elif dimension == "potential_to_store_rate":
                pc = feats_orig[0]
                cur_rate = feats_orig[11]
                target_rate = cur_rate * (1.0 + change_percentage / 100.0)
                overrides = {"customer_flow": target_rate * pc}
            elif dimension == "store_to_sales_rate":
                # 来自历史销量/流量，强行 what-if 不可靠
                overrides = None

        # 3. 使用构造好的 overrides 重新计算特征 (feats_changed)
        feats_changed = build_features(dealer_data, year, m, overrides=overrides, global_medians=None)

        X_raw_original_list.append(feats_orig)
        X_raw_changed_list.append(feats_changed)
        valid_months.append(m)
    # ========== 循环替换结束 ==========

    if len(valid_months) == 0:
        print("没有找到有效的特征数据，可能是因为该月份的特征数据不完整或缺失。")
        return None, None

    X_raw_original = np.array(X_raw_original_list, dtype=float)
    X_raw_changed = np.array(X_raw_changed_list, dtype=float)

    try:
        X_original_scaled = scaler.transform(X_raw_original)
        X_changed_scaled = scaler.transform(X_raw_changed)

        yhat_orig = best_model.predict(X_original_scaled)
        yhat_changed = best_model.predict(X_changed_scaled)

        if getattr(best_model, "target_transform_", "") == "log1p":
            store_calib = PHASE_STORE_CALIB
            try:
                cfg = getattr(best_model, "config_", None)
                if isinstance(cfg, dict) and ("PHASE_STORE_CALIB" in cfg):
                    store_calib = bool(cfg["PHASE_STORE_CALIB"])
            except Exception:
                pass

            if store_calib:
                bias_dict = getattr(best_model, "dealer_bias_", None)
                if isinstance(bias_dict, dict):
                    bd = float(bias_dict.get(str(dealer_code), 0.0))
                    yhat_orig = yhat_orig + bd
                    yhat_changed = yhat_changed + bd

            yhat_orig = _from_log_target(yhat_orig)
            yhat_changed = _from_log_target(yhat_changed)

    except Exception as e:
        print(f"模型预测失败: {e}")
        return None, None

    print("\n销量变化：")
    for i, m in enumerate(valid_months):
        print(f"第 {m} 月销量变化：")
        print(f"改变前销量: {original_sales.get(m, None)}")
        print(f"改变后销量: {yhat_changed[i]:.2f}")
        if original_sales.get(m, None) is not None:
            try:
                print(f"销量变化量: {yhat_changed[i] - float(original_sales[m]):.2f}\n")
            except Exception:
                print("销量变化量: (原销量非数值，无法计算差值)\n")
        else:
            print("销量变化量: (原销量缺失，无法计算差值)\n")

    return original_sales, yhat_changed


# ============================================================
# Refactor Layer (runtime config + feature context + bundle API)
# 说明：
# - 保留既有训练/评估主体逻辑，新增统一配置、统一特征上下文、point bundle 与 what-if 正式接口
# - 采用“后置覆盖”方式定义同名函数，尽量减少对旧代码的大面积侵入
# ============================================================
import json
import joblib
from pathlib import Path
from typing import Any, Iterable


# 先保留旧实现引用，便于兼容包装
_legacy_build_features = build_features
_legacy_prepare_training_data = prepare_training_data
_legacy_rolling_backtest_prepared = rolling_backtest_prepared
_legacy_train_model = train_model
_legacy_predict_sales_change = predict_sales_change


def _safe_json_default(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    return str(obj)


@dataclass
class RuntimeConfig:
    """
    显式运行配置。
    当前阶段仍兼容旧版 env 解析，但 selector / service 层可显式传 config，
    避免“改 os.environ + reload 模块”的硬依赖。
    """
    values: dict

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(values=dict(get_runtime_config()))

    @classmethod
    def from_dict(cls, data: dict | None = None) -> "RuntimeConfig":
        base = dict(get_runtime_config())
        if data:
            base.update(data)
        return cls(values=base)

    def to_dict(self) -> dict:
        return dict(self.values)

    def get(self, key: str, default=None):
        return self.values.get(key, default)


_RUNTIME_CONFIG_KEYS = set(get_runtime_config().keys())


def apply_runtime_config(config: RuntimeConfig | dict | None = None) -> RuntimeConfig:
    """
    将 RuntimeConfig 显式写回当前模块全局变量。
    这样旧 build_features / rolling_backtest_prepared 依然可以工作，
    同时 selector_service 不再需要通过 import-time env 控制配置。
    """
    if config is None:
        cfg = RuntimeConfig.from_env()
    elif isinstance(config, RuntimeConfig):
        cfg = config
    else:
        cfg = RuntimeConfig.from_dict(config)

    for key, value in cfg.to_dict().items():
        if key in _RUNTIME_CONFIG_KEYS:
            globals()[key] = value
    return cfg


@dataclass
class FeatureContext:
    global_medians: dict
    config: RuntimeConfig
    feature_names: list[str]
    feature_version: str = "point_features_v2"

    def to_dict(self) -> dict:
        return {
            "global_medians": dict(self.global_medians),
            "config": self.config.to_dict(),
            "feature_names": list(self.feature_names),
            "feature_version": self.feature_version,
        }


@dataclass
class PreparedData:
    X_raw: np.ndarray
    y_raw: np.ndarray
    y_log: np.ndarray
    time_keys: np.ndarray
    dealer_codes: np.ndarray
    feature_dim: int
    years: np.ndarray | None = None
    months: np.ndarray | None = None
    feature_names: list[str] | None = None
    feature_context: FeatureContext | None = None
    sample_index: list[dict] | None = None

    def to_dict(self) -> dict:
        return {
            "X_raw_shape": list(self.X_raw.shape),
            "y_raw_shape": list(self.y_raw.shape),
            "feature_dim": int(self.feature_dim),
            "feature_names": list(self.feature_names or []),
            "sample_index_size": int(len(self.sample_index or [])),
            "feature_context": self.feature_context.to_dict() if self.feature_context else None,
        }


@dataclass
class PointModelBundle:
    model: Any
    scaler: Any
    dealer_bias: dict | None
    global_medians: dict
    config: RuntimeConfig
    feature_names: list[str]
    feature_dim: int
    xgb_params: dict
    rolling_summary: dict
    model_version: str
    trained_at: str
    train_years_months: list[dict]
    feature_version: str = "point_features_v2"

    @property
    def feature_context(self) -> FeatureContext:
        return FeatureContext(
            global_medians=dict(self.global_medians),
            config=self.config,
            feature_names=list(self.feature_names),
            feature_version=self.feature_version,
        )

    def to_metadata_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "trained_at": self.trained_at,
            "feature_version": self.feature_version,
            "feature_dim": int(self.feature_dim),
            "feature_names": list(self.feature_names),
            "xgb_params": dict(self.xgb_params or {}),
            "rolling_summary": dict(self.rolling_summary or {}),
            "train_years_months": list(self.train_years_months or []),
            "config": self.config.to_dict(),
        }


def compute_global_medians(dealers, config: RuntimeConfig | dict | None = None) -> dict:
    """
    抽出训练态全局中位数计算，供 prepare / train / quantile 共用。
    """
    apply_runtime_config(config)
    all_atom_values = {k: [] for k, _ in _BASE_ATOMS}
    for _, d_data in dealers.items():
        for feat_name, attr in _BASE_ATOMS:
            mp = getattr(d_data, attr, {}) or {}
            for val in mp.values():
                if not _is_nan(val):
                    try:
                        all_atom_values[feat_name].append(float(val))
                    except Exception:
                        continue
    return {k: (float(np.median(v)) if v else 0.0) for k, v in all_atom_values.items()}


def get_feature_names(config: RuntimeConfig | dict | None = None) -> list[str]:
    """
    与当前 build_features 输出顺序严格对齐。
    """
    apply_runtime_config(config)
    names = [
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
        "sales_lag1",
        "sales_lag2",
        "sales_lag3",
        "sales_roll3_mean",
        "sales_roll6_mean",
        "sales_roll3_std",
        "sales_roll6_std",
        "sales_diff_1",
        "sales_pct_change_1",
        "dealer_hist_mean",
        "month_sin",
        "month_cos",
        "sales_lag6",
        "sales_lag12",
        "sales_roll12_mean",
        "sales_roll12_std",
        "yoy_mom_ratio",
        "yoy_mom_diff",
        "yoy_level_ratio",
        "time_trend",
        "is_peak",
        "is_dec",
        "is_janfeb",
        "janfeb_gate_active",
        "jf_ly_total_log",
        "jf_ly_feb_share",
        "jf_ly_feb_to_jan_logratio",
        "jf_cur_jan_log",
        "jf_cur_jan_vs_ly_jan_logdiff",
        "jf_proj_feb_log",
        "miss_cur_jan",
        "miss_ly_jan",
        "miss_ly_feb",
        "miss_lag12",
        "miss_lag13",
        "roll12_coverage",
        "miss_roll12",
        "base_cur_present",
        "base_signal_cnt",
    ]
    names.extend([f"base_miss_{k}" for k, _ in _BASE_ATOMS])
    names.extend([f"base_stale_{k}" for k, _ in _BASE_ATOMS])
    names.extend([
        "cny_rel_d",
        "cny_in_win",
        "cny_pre",
        "cny_in",
        "cny_post",
        "cny_is_jan",
    ])
    if PHASE28_MISSING_FLAG:
        names.extend([
            "ratio_flag_lead_pc",
            "ratio_flag_flow_pc",
            "ratio_flag_store_sales",
            "ratio_flag_pct_change",
            "ratio_flag_yoy_mom",
            "ratio_flag_yoy_level",
            "ratio_flag_jf_share",
        ])
    return names


def build_feature_context(
    dealers,
    config: RuntimeConfig | dict | None = None,
    global_medians: dict | None = None,
) -> FeatureContext:
    cfg = apply_runtime_config(config)
    gmed = dict(global_medians or compute_global_medians(dealers, cfg))
    return FeatureContext(
        global_medians=gmed,
        config=cfg,
        feature_names=get_feature_names(cfg),
        feature_version="point_features_v2",
    )


def build_features(
    dealer_data,
    year: int,
    month: int,
    overrides: dict | None = None,
    global_medians: dict | None = None,
    feature_context: FeatureContext | None = None,
    config: RuntimeConfig | dict | None = None,
) -> list:
    """
    扩展签名：
    - 支持显式传 feature_context / config
    - 内部优先复用 feature_context.global_medians
    - 兼容旧接口调用方式
    """
    cfg = config
    if feature_context is not None:
        if global_medians is None:
            global_medians = feature_context.global_medians
        if cfg is None:
            cfg = feature_context.config
    apply_runtime_config(cfg)
    return _legacy_build_features(
        dealer_data=dealer_data,
        year=year,
        month=month,
        overrides=overrides,
        global_medians=global_medians,
    )


def prepare_training_data(
    dealers,
    config: RuntimeConfig | dict | None = None,
    feature_context: FeatureContext | None = None,
) -> PreparedData:
    """
    统一训练数据准备：
    - 显式复用训练态 global_medians
    - 返回 feature_names / years / months / sample_index / feature_context
    """
    cfg = apply_runtime_config(config)
    feature_context = feature_context or build_feature_context(dealers, cfg)

    X_raw = []
    y_raw = []
    time_keys = []
    dealer_codes = []
    years = []
    months = []
    sample_index = []

    for dealer_code, dealer_data in dealers.items():
        sales_map = getattr(dealer_data, "sales", {}) or {}
        tuple_keys = [k for k in sales_map.keys() if isinstance(k, tuple) and len(k) == 2]
        if tuple_keys:
            keys_iter = sorted(tuple_keys, key=lambda x: (int(x[0]), int(x[1])))
        else:
            keys_iter = sorted(
                [(2024, int(m)) for m in sales_map.keys() if isinstance(m, (int, np.integer))],
                key=lambda x: (int(x[0]), int(x[1])),
            )

        for year, month in keys_iter:
            year = int(year)
            month = int(month)
            if not _has_required_month_fields(dealer_data, year, month, include_target=True):
                continue

            feat = build_features(
                dealer_data,
                year,
                month,
                overrides=None,
                feature_context=feature_context,
            )
            yv = _sales_at(dealer_data, year, month)
            if yv is None:
                continue

            X_raw.append(feat)
            y_raw.append(float(yv))
            time_keys.append(make_time_key(year, month))
            dealer_codes.append(str(dealer_code))
            years.append(year)
            months.append(month)
            sample_index.append(
                {
                    "dealer_code": str(dealer_code),
                    "year": year,
                    "month": month,
                    "time_key": make_time_key(year, month),
                }
            )

    if len(X_raw) == 0:
        raise ValueError("未构造出任何训练样本：请检查 dealers 数据或当前 RuntimeConfig。")

    X_raw = np.asarray(X_raw, dtype=float)
    y_raw = np.asarray(y_raw, dtype=float)
    time_keys = np.asarray(time_keys, dtype=int)
    dealer_codes = np.asarray(dealer_codes, dtype=str)
    years = np.asarray(years, dtype=int)
    months = np.asarray(months, dtype=int)
    y_log = _to_log_target(y_raw)

    feat_names = list(feature_context.feature_names)
    if len(feat_names) != int(X_raw.shape[1]):
        feat_names = [f"f{i}" for i in range(int(X_raw.shape[1]))]

    return PreparedData(
        X_raw=X_raw,
        y_raw=y_raw,
        y_log=y_log,
        time_keys=time_keys,
        dealer_codes=dealer_codes,
        feature_dim=int(X_raw.shape[1]),
        years=years,
        months=months,
        feature_names=feat_names,
        feature_context=feature_context,
        sample_index=sample_index,
    )


def rolling_backtest_prepared(
    prep: PreparedData,
    xgb_params: dict,
    *,
    last_n_folds: int | None = None,
    quiet: bool = True,
    runtime_config: RuntimeConfig | dict | None = None,
) -> tuple[list[dict], dict]:
    cfg = runtime_config
    if cfg is None and getattr(prep, "feature_context", None) is not None:
        cfg = prep.feature_context.config
    apply_runtime_config(cfg)
    return _legacy_rolling_backtest_prepared(
        prep=prep,
        xgb_params=xgb_params,
        last_n_folds=last_n_folds,
        quiet=quiet,
    )


def _collect_train_years_months(prep: PreparedData) -> list[dict]:
    if prep.years is None or prep.months is None:
        uniq = sorted(set(int(t) for t in prep.time_keys.tolist()))
        out = []
        for tk in uniq:
            y, m = time_key_to_ym(tk)
            out.append({"year": int(y), "month": int(m), "time_key": int(tk)})
        return out

    uniq = sorted({(int(y), int(m)) for y, m in zip(prep.years.tolist(), prep.months.tolist())})
    return [
        {"year": int(y), "month": int(m), "time_key": int(make_time_key(y, m))}
        for y, m in uniq
    ]


def train_point_model_from_prepared(
    prep: PreparedData,
    xgb_params_override: dict | None = None,
    *,
    model_version: str | None = None,
    quiet: bool = False,
    runtime_config: RuntimeConfig | dict | None = None,
) -> PointModelBundle:
    """
    基于共享 PreparedData 训练正式点模型，避免 selector 对每个候选重复 prepare。
    """
    cfg = runtime_config
    if cfg is None and prep.feature_context is not None:
        cfg = prep.feature_context.config
    cfg = apply_runtime_config(cfg)

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(prep.X_raw)

    final_params = dict(_get_default_xgb_params(cfg.get("TRAIN_MODE", TRAIN_MODE)))
    if xgb_params_override:
        final_params.update(xgb_params_override)

    best_model = xgb.XGBRegressor(**final_params)
    final_weights = np.expm1(prep.y_log) if PHASE32_USE_WEIGHT else None
    best_model.fit(X_scaled, prep.y_log, sample_weight=final_weights)

    yhat_log = best_model.predict(X_scaled)
    dealer_bias_full = (
        _fit_dealer_bias(
            y_log=prep.y_log,
            yhat_log=yhat_log,
            dealer_codes=prep.dealer_codes,
            shrink_alpha=0.0,
        )
        if PHASE_STORE_CALIB
        else None
    )

    best_model.target_transform_ = "log1p"
    best_model.dealer_bias_ = dealer_bias_full
    best_model.config_ = cfg.to_dict()
    best_model.global_medians_ = dict(prep.feature_context.global_medians if prep.feature_context else {})
    best_model.feature_names_ = list(prep.feature_names or [])
    best_model.feature_version_ = getattr(prep.feature_context, "feature_version", "point_features_v2")
    best_model.feature_context_ = prep.feature_context

    bundle = PointModelBundle(
        model=best_model,
        scaler=scaler,
        dealer_bias=dealer_bias_full,
        global_medians=dict(prep.feature_context.global_medians if prep.feature_context else {}),
        config=cfg,
        feature_names=list(prep.feature_names or []),
        feature_dim=int(prep.feature_dim),
        xgb_params=final_params,
        rolling_summary={},
        model_version=model_version or f"point_{time.strftime('%Y%m%d_%H%M%S')}",
        trained_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        train_years_months=_collect_train_years_months(prep),
        feature_version=getattr(prep.feature_context, "feature_version", "point_features_v2"),
    )
    if not quiet:
        print(f"[point] trained point bundle: version={bundle.model_version} | feature_dim={bundle.feature_dim}")
    return bundle


def _predict_from_raw_features(
    model_obj,
    scaler_obj,
    X_raw: np.ndarray,
    dealer_code: str | Iterable[str] | None = None,
) -> np.ndarray:
    X_scaled = scaler_obj.transform(np.asarray(X_raw, dtype=float))
    yhat = model_obj.predict(X_scaled)

    if getattr(model_obj, "target_transform_", "") == "log1p":
        store_calib = PHASE_STORE_CALIB
        try:
            cfg = getattr(model_obj, "config_", None)
            if isinstance(cfg, dict) and ("PHASE_STORE_CALIB" in cfg):
                store_calib = bool(cfg["PHASE_STORE_CALIB"])
        except Exception:
            pass

        if store_calib:
            bias_dict = getattr(model_obj, "dealer_bias_", None)
            if isinstance(bias_dict, dict):
                if dealer_code is None:
                    pass
                elif isinstance(dealer_code, str):
                    yhat = yhat + float(bias_dict.get(str(dealer_code), 0.0))
                else:
                    dc_list = [str(x) for x in dealer_code]
                    yhat = np.asarray(yhat, dtype=float)
                    for i, dc in enumerate(dc_list):
                        yhat[i] = yhat[i] + float(bias_dict.get(dc, 0.0))

        yhat = _from_log_target(yhat)

    return np.asarray(yhat, dtype=float)


def build_single_dimension_overrides(
    dealer_data,
    dimension: str,
    change_percentage: float,
    *,
    year: int,
    month: int,
    feature_context: FeatureContext | None = None,
    config: RuntimeConfig | dict | None = None,
) -> dict | None:
    """
    将前端 scenario（单维度 + 百分比）解释为原子 overrides。
    """
    apply_runtime_config(config or (feature_context.config if feature_context else None))

    feats_orig = build_features(
        dealer_data,
        int(year),
        int(month),
        overrides=None,
        feature_context=feature_context,
    )

    dimension_index_map = {
        "potential_customers": 0,
        "test_drives": 1,
        "leads": 2,
        "customer_flow": 3,
        "defeat_rate": 4,
        "success_rate": 5,
        "success_response_time": 6,
        "defeat_response_time": 7,
        "policy": 8,
        "gsev": 9,
        "lead_to_potential_rate": 10,
        "potential_to_store_rate": 11,
        "store_to_sales_rate": 12,
    }
    atomic_dims = {
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
    }

    if dimension not in dimension_index_map:
        raise ValueError(f"无效维度: {dimension}")

    if dimension in atomic_dims:
        return {
            dimension: feats_orig[dimension_index_map[dimension]] * (1.0 + float(change_percentage) / 100.0)
        }

    if dimension == "lead_to_potential_rate":
        pc = feats_orig[0]
        cur_rate = feats_orig[10]
        target_rate = cur_rate * (1.0 + float(change_percentage) / 100.0)
        return {"leads": target_rate * pc}

    if dimension == "potential_to_store_rate":
        pc = feats_orig[0]
        cur_rate = feats_orig[11]
        target_rate = cur_rate * (1.0 + float(change_percentage) / 100.0)
        return {"customer_flow": target_rate * pc}

    if dimension == "store_to_sales_rate":
        # 依赖历史销量/历史客流，不建议强行在 t+1 what-if 中直接改
        return None

    return None


def _resolve_bundle_components(point_bundle_or_model, scaler=None):
    if isinstance(point_bundle_or_model, PointModelBundle):
        return point_bundle_or_model.model, point_bundle_or_model.scaler, point_bundle_or_model.feature_context
    model_obj = point_bundle_or_model
    scaler_obj = scaler
    if model_obj is None or scaler_obj is None:
        raise ValueError("当未传 PointModelBundle 时，必须同时传 model 和 scaler。")
    feature_context = getattr(model_obj, "feature_context_", None)
    if feature_context is None:
        cfg = RuntimeConfig.from_dict(getattr(model_obj, "config_", None) or get_runtime_config())
        feature_context = FeatureContext(
            global_medians=dict(getattr(model_obj, "global_medians_", {}) or {}),
            config=cfg,
            feature_names=list(getattr(model_obj, "feature_names_", []) or []),
            feature_version=getattr(model_obj, "feature_version_", "point_features_v2"),
        )
    return model_obj, scaler_obj, feature_context


def predict_t1_what_if(
    point_bundle_or_model,
    dealers,
    dealer_code,
    base_year: int,
    base_month: int,
    dimension: str,
    change_percentage: float,
    *,
    scaler=None,
) -> dict:
    """
    功能一正式接口：
    - 输入 base_year/base_month
    - 自动推目标月 t+1
    - 返回 baseline / scenario / delta / delta_pct / target_year / target_month
    """
    model_obj, scaler_obj, feature_context = _resolve_bundle_components(point_bundle_or_model, scaler=scaler)
    dealer_data = dealers.get(dealer_code)
    if dealer_data is None:
        raise KeyError(f"未找到经销商: {dealer_code}")

    target_year, target_month = get_prev_year_month(int(base_year), int(base_month), -1)
    apply_runtime_config(feature_context.config)

    if not _has_required_month_fields(dealer_data, int(target_year), int(target_month), include_target=False):
        raise ValueError(f"dealer={dealer_code} 在目标月 {target_year}-{target_month:02d} 无法构造有效特征。")

    baseline_raw = np.asarray([
        build_features(
            dealer_data,
            int(target_year),
            int(target_month),
            overrides=None,
            feature_context=feature_context,
        )
    ], dtype=float)

    overrides = build_single_dimension_overrides(
        dealer_data,
        dimension=dimension,
        change_percentage=float(change_percentage),
        year=int(target_year),
        month=int(target_month),
        feature_context=feature_context,
    )

    scenario_raw = np.asarray([
        build_features(
            dealer_data,
            int(target_year),
            int(target_month),
            overrides=overrides,
            feature_context=feature_context,
        )
    ], dtype=float)

    baseline_pred = float(_predict_from_raw_features(model_obj, scaler_obj, baseline_raw, dealer_code=str(dealer_code))[0])
    scenario_pred = float(_predict_from_raw_features(model_obj, scaler_obj, scenario_raw, dealer_code=str(dealer_code))[0])
    delta = float(scenario_pred - baseline_pred)
    delta_pct = float(delta / baseline_pred * 100.0) if abs(baseline_pred) > 1e-8 else float("nan")

    return {
        "dealer_code": str(dealer_code),
        "base_year": int(base_year),
        "base_month": int(base_month),
        "target_year": int(target_year),
        "target_month": int(target_month),
        "dimension": str(dimension),
        "change_percentage": float(change_percentage),
        "baseline": baseline_pred,
        "scenario": scenario_pred,
        "delta": delta,
        "delta_pct": delta_pct,
        "scenario_applied": {
            "dimension": str(dimension),
            "change_percentage": float(change_percentage),
            "overrides": overrides,
        },
        "feature_version": getattr(feature_context, "feature_version", "point_features_v2"),
        "model_version": getattr(point_bundle_or_model, "model_version", None),
    }


def save_point_bundle(point_bundle: PointModelBundle, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(point_bundle, path)
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    meta_path.write_text(
        json.dumps(point_bundle.to_metadata_dict(), ensure_ascii=False, indent=2, default=_safe_json_default),
        encoding="utf-8",
    )
    return path


def load_point_bundle(path: str | Path) -> PointModelBundle:
    path = Path(path)
    obj = joblib.load(path)
    if isinstance(obj, PointModelBundle):
        return obj
    # 兼容 legacy dict 结构
    if isinstance(obj, dict):
        cfg = obj.get("config")
        if not isinstance(cfg, RuntimeConfig):
            cfg = RuntimeConfig.from_dict(cfg if isinstance(cfg, dict) else None)
        return PointModelBundle(
            model=obj["model"],
            scaler=obj["scaler"],
            dealer_bias=obj.get("dealer_bias"),
            global_medians=dict(obj.get("global_medians", {}) or {}),
            config=cfg,
            feature_names=list(obj.get("feature_names", []) or []),
            feature_dim=int(obj.get("feature_dim", len(obj.get("feature_names", []) or []))),
            xgb_params=dict(obj.get("xgb_params", {}) or {}),
            rolling_summary=dict(obj.get("rolling_summary", {}) or {}),
            model_version=str(obj.get("model_version", path.stem)),
            trained_at=str(obj.get("trained_at", "")),
            train_years_months=list(obj.get("train_years_months", []) or []),
            feature_version=str(obj.get("feature_version", "point_features_v2")),
        )
    raise TypeError(f"无法识别的 point bundle 类型: {type(obj)!r}")


def train_model(
    dealers,
    xgb_params_override: dict | None = None,
    skip_kfold: bool = False,
    quiet: bool = False,
    config: RuntimeConfig | dict | None = None,
):
    """
    兼容旧接口，同时补充训练态上下文挂载：
    - global_medians_
    - feature_names_
    - feature_context_
    - point_bundle_metadata_
    """
    cfg = apply_runtime_config(config)
    feature_context = build_feature_context(dealers, cfg)

    best_model, scaler, X_scaled, y_raw, y_pred_sales = _legacy_train_model(
        dealers=dealers,
        xgb_params_override=xgb_params_override,
        skip_kfold=skip_kfold,
        quiet=quiet,
    )

    best_model.config_ = cfg.to_dict()
    best_model.global_medians_ = dict(feature_context.global_medians)
    best_model.feature_names_ = list(feature_context.feature_names)
    best_model.feature_dim_ = int(len(feature_context.feature_names))
    best_model.feature_version_ = feature_context.feature_version
    best_model.feature_context_ = feature_context
    best_model.point_bundle_metadata_ = {
        "feature_version": feature_context.feature_version,
        "feature_dim": int(len(feature_context.feature_names)),
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "xgb_params_override": dict(xgb_params_override or {}),
    }

    return best_model, scaler, X_scaled, y_raw, y_pred_sales


def predict_sales_change(
    best_model,
    scaler,
    dealers,
    dealer_code,
    dimension,
    change_percentage,
    month=None,
    year=2024,
):
    """
    兼容旧接口，但推理阶段显式复用训练态 feature_context / global_medians。
    """
    dealer_data = dealers.get(dealer_code)
    if not dealer_data:
        print(f"未找到经销商代码 {dealer_code} 的数据。")
        return None, None

    feature_context = getattr(best_model, "feature_context_", None)
    if feature_context is None:
        cfg = RuntimeConfig.from_dict(getattr(best_model, "config_", None) or get_runtime_config())
        feature_context = FeatureContext(
            global_medians=dict(getattr(best_model, "global_medians_", {}) or {}),
            config=cfg,
            feature_names=list(getattr(best_model, "feature_names_", []) or []),
            feature_version=getattr(best_model, "feature_version_", "point_features_v2"),
        )
    apply_runtime_config(feature_context.config)

    sales_map = getattr(dealer_data, "sales", {}) or {}
    original_sales = {m: _map_at(sales_map, int(year), m) for m in range(1, 11)}

    if month is None:
        months_to_process = range(1, 11)
    else:
        months_to_process = [int(month)]

    X_raw_original_list = []
    X_raw_changed_list = []
    valid_months = []

    for m in months_to_process:
        if not _has_required_month_fields(dealer_data, int(year), int(m), include_target=False):
            continue

        feats_orig = build_features(
            dealer_data,
            int(year),
            int(m),
            overrides=None,
            feature_context=feature_context,
        )
        try:
            overrides = build_single_dimension_overrides(
                dealer_data,
                dimension=str(dimension),
                change_percentage=float(change_percentage),
                year=int(year),
                month=int(m),
                feature_context=feature_context,
            )
        except Exception:
            print(f"无效的维度 '{dimension}'，请确保输入正确。")
            return None, None

        feats_changed = build_features(
            dealer_data,
            int(year),
            int(m),
            overrides=overrides,
            feature_context=feature_context,
        )

        X_raw_original_list.append(feats_orig)
        X_raw_changed_list.append(feats_changed)
        valid_months.append(int(m))

    if len(valid_months) == 0:
        print("没有找到有效的特征数据，可能是因为该月份的特征数据不完整或缺失。")
        return None, None

    try:
        _ = _predict_from_raw_features(best_model, scaler, np.asarray(X_raw_original_list, dtype=float), str(dealer_code))
        yhat_changed = _predict_from_raw_features(best_model, scaler, np.asarray(X_raw_changed_list, dtype=float), str(dealer_code))
    except Exception as e:
        print(f"模型预测失败: {e}")
        return None, None

    print("\n销量变化：")
    for i, m in enumerate(valid_months):
        print(f"第 {m} 月销量变化：")
        print(f"改变前销量: {original_sales.get(m, None)}")
        print(f"改变后销量: {yhat_changed[i]:.2f}")
        if original_sales.get(m, None) is not None:
            try:
                print(f"销量变化量: {yhat_changed[i] - float(original_sales[m]):.2f}\n")
            except Exception:
                print("销量变化量: (原销量非数值，无法计算差值)\n")
        else:
            print("销量变化量: (原销量缺失，无法计算差值)\n")

    return original_sales, np.asarray(yhat_changed, dtype=float)


def build_point_bundle_from_trained_model(
    best_model,
    scaler,
    prep: PreparedData,
    *,
    xgb_params: dict | None = None,
    model_version: str | None = None,
) -> PointModelBundle:
    """
    将 train_model 训练出的 model/scaler 封装为 PointModelBundle。
    """
    feature_context = getattr(best_model, "feature_context_", None) or prep.feature_context
    cfg = RuntimeConfig.from_dict(getattr(best_model, "config_", None) or (feature_context.config.to_dict() if feature_context else None))
    return PointModelBundle(
        model=best_model,
        scaler=scaler,
        dealer_bias=getattr(best_model, "dealer_bias_", None),
        global_medians=dict(getattr(best_model, "global_medians_", {}) or (feature_context.global_medians if feature_context else {})),
        config=cfg,
        feature_names=list(getattr(best_model, "feature_names_", []) or (prep.feature_names or [])),
        feature_dim=int(getattr(best_model, "feature_dim_", prep.feature_dim)),
        xgb_params=dict(xgb_params or {}),
        rolling_summary=dict(getattr(best_model, "rolling_summary_", {}) or {}),
        model_version=model_version or f"point_{time.strftime('%Y%m%d_%H%M%S')}",
        trained_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        train_years_months=_collect_train_years_months(prep),
        feature_version=getattr(best_model, "feature_version_", "point_features_v2"),
    )
