import os
import warnings
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message=".*columns*")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app_db: Optional[Flask] = None
db_instance: Optional[SQLAlchemy] = None


def init_db_app(app: Optional[Flask] = None, db: Optional[SQLAlchemy] = None) -> None:
    global app_db, db_instance
    app_db = app
    db_instance = db


def get_db_app() -> Tuple[Optional[Flask], Optional[SQLAlchemy]]:
    return app_db, db_instance


DB_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'mysql+pymysql://root:123456@localhost:3306/dealer_management',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
}


def _ensure_db_app():
    global app_db, db_instance
    if app_db is None or db_instance is None:
        from models import db as models_db
        app_db = Flask(__name__)
        app_db.config.update(DB_CONFIG)
        models_db.init_app(app_db)
        db_instance = models_db
    return app_db, db_instance

# matplotlib 中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# =========================
# 可配置路径（当前用 Excel，后续可替换为数据库）
# =========================
RADAR_SOURCE_EXCEL = os.getenv("RADAR_SOURCE_EXCEL", "2024test.xlsx")
RADAR_SCORES_EXCEL = os.getenv("RADAR_SCORES_EXCEL", "quantified_scores_with_monthly_forces_v2.xlsx")
RADAR_STATIC_DIR = os.getenv("RADAR_STATIC_DIR", "static")

# 当前 radar 只覆盖 2024 年 1-10 月
SUPPORTED_MONTHS = [str(i) for i in range(1, 11)]
MONTH_LABELS = [f"{i}月" for i in range(1, 11)]

# 五力标签顺序
FORCE_LABELS = ['传播获客力', '体验力', '转化力', '服务力', '经营力']

# 五力构成权重（与原始脚本保持一致）
FORCES_WEIGHTS: Dict[str, Dict[str, float]] = {
    '传播获客力': {'客流量': 50, '潜客量': 20, '线索量': 30},
    '体验力': {'成交率': 40, '战败率': 40, '评价分': 20},
    '转化力': {
        '销量': 50,
        '成交率': 10,
        '成交响应时间': 2.5,
        '战败响应时间': 2.5,
        '试驾数': 5,
        '政策': 5,
        'GSEV': 10,
        '评价分': 5,
        '终端检核平均分': 10,
    },
    '服务力': {'评价分': 40, '试驾数': 30, '终端检核平均分': 30},
    '经营力': {},  # 当前逻辑：固定为 3.5
}

# 前端展示用综合得分权重（与原始 dealers_score 保持一致）
DISPLAY_SCORE_WEIGHTS: Dict[str, float] = {
    '传播获客力': 0.20,
    '体验力': 0.20,
    '转化力': 0.40,
    '服务力': 0.10,
    '经营力': 0.10,
}

# 这些列不参与归一化，直接作为评分值使用
NON_NORMALIZED_COLUMNS = [f'{i}月评价分' for i in range(1, 11)]

# 原始标识列
ID_COLUMNS = ['经销商代码', '省份', '销售FED级别']


# =========================
# 基础工具函数
# =========================
def normalize_month(month: Union[str, int]) -> str:
    """允许 1 / '1' / '1月'，统一返回 '1' 这样的数字字符串。"""
    m = str(month).strip()
    if m.endswith('月'):
        m = m[:-1]
    if not m.isdigit():
        raise ValueError(f"月份格式无效：{month}")
    return str(int(m))



def month_label(month: Union[str, int]) -> str:
    m = normalize_month(month)
    if m not in SUPPORTED_MONTHS:
        raise ValueError(f"当前 radar 仅支持 1-10 月，收到月份：{month}")
    return f"{m}月"



def _ensure_required_columns(df: pd.DataFrame, required_columns: Sequence[str], file_desc: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{file_desc} 缺少必要列：{missing}")



def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce')



def _rank_to_score(series: pd.Series) -> pd.Series:
    """把一列值映射到 1~5 分；空值保持为空。"""
    series = _safe_numeric(series)
    valid = series.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    if valid.nunique() == 1:
        # 所有非空值都相同时，统一记为 3 分，避免除零并保持中性
        out = pd.Series(np.nan, index=series.index)
        out.loc[valid.index] = 3.0
        return out

    ranks = valid.rank(method='min', ascending=True)
    total_ranks = ranks.max()
    scores = 1 + (ranks - 1) / (total_ranks - 1) * 4
    out = pd.Series(np.nan, index=series.index)
    out.loc[valid.index] = np.round(scores, 5)
    return out



def _safe_filename(text: str) -> str:
    keep = []
    for ch in str(text):
        if ch.isalnum() or ch in ('-', '_'):
            keep.append(ch)
        else:
            keep.append('_')
    return ''.join(keep)


# =========================
# Excel 输入层
# =========================
def load_radar_source_excel(source_excel_path: str = RADAR_SOURCE_EXCEL) -> pd.DataFrame:
    """读取 2024test.xlsx 这类原始 radar 输入表。"""
    if not os.path.exists(source_excel_path):
        raise FileNotFoundError(f"未找到 radar 原始输入文件：{source_excel_path}")

    df = pd.read_excel(source_excel_path)

    required_columns = ['经销商代码', '省份', '销售FED级别', '终端检核平均分']
    required_columns += NON_NORMALIZED_COLUMNS
    # 五力计算实际依赖的月度业务列
    for month in MONTH_LABELS:
        required_columns += [
            f'{month}客流量', f'{month}潜客量', f'{month}线索量',
            f'{month}成交率', f'{month}战败率', f'{month}销量',
            f'{month}成交响应时间', f'{month}战败响应时间', f'{month}试驾数',
            f'{month}政策', f'{month}GSEV',
        ]
    _ensure_required_columns(df, required_columns, f"radar 原始输入文件 {source_excel_path}")
    return df



def load_scores_excel(scores_excel_path: str = RADAR_SCORES_EXCEL) -> pd.DataFrame:
    """读取已经计算好的五力结果 Excel。"""
    if not os.path.exists(scores_excel_path):
        raise FileNotFoundError(f"未找到 radar 结果文件：{scores_excel_path}")

    df = pd.read_excel(scores_excel_path)
    required_columns = ['经销商代码'] + [f'{m}{force}' for m in MONTH_LABELS for force in FORCE_LABELS]
    _ensure_required_columns(df, required_columns, f"radar 结果文件 {scores_excel_path}")
    return df


# =========================
# 数据库输入层
# =========================
DB_FIELD_TO_EXCEL_MONTHLY = {
    'customer_flow': '客流量',
    'potential_customers': '潜客量',
    'leads': '线索量',
    'success_rate': '成交率',
    'defeat_rate': '战败率',
    'sales': '销量',
    'success_response_time': '成交响应时间',
    'defeat_response_time': '战败响应时间',
    'test_drives': '试驾数',
    'policy': '政策',
    'gsev': 'GSEV',
    'evaluation_score': '评价分',
}

DB_FIELD_TO_EXCEL_BASE = {
    'dealer_code': '经销商代码',
    'province': '省份',
    'fed_level': '销售FED级别',
    'terminal_check_avg': '终端检核平均分',
}

FORCE_DB_FIELDS = {
    '传播获客力': 'spread_force',
    '体验力': 'experience_force',
    '转化力': 'conversion_force',
    '服务力': 'service_force',
    '经营力': 'operation_force',
}


def load_radar_source_from_db(year: int = 2024) -> pd.DataFrame:
    from models import RadarSource2024
    
    app, db = _ensure_db_app()
    
    with app.app_context():
        records = RadarSource2024.query.all()
        
        if not records:
            raise ValueError(f"数据库 radar_source_2024 表中没有数据")
        
        data = []
        for r in records:
            row = {
                '经销商代码': str(r.dealer_code),
                '省份': r.province,
                '销售FED级别': r.fed_level,
                '终端检核平均分': float(r.terminal_check_avg) if r.terminal_check_avg else np.nan,
            }
            
            for month in range(1, 11):
                m_label = f'{month}月'
                for db_field, cn_name in DB_FIELD_TO_EXCEL_MONTHLY.items():
                    db_col = f'{db_field}_m{month:02d}'
                    value = getattr(r, db_col, None)
                    row[f'{m_label}{cn_name}'] = float(value) if value is not None else np.nan
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        required_columns = ['经销商代码', '省份', '销售FED级别', '终端检核平均分']
        required_columns += NON_NORMALIZED_COLUMNS
        for month in MONTH_LABELS:
            required_columns += [
                f'{month}客流量', f'{month}潜客量', f'{month}线索量',
                f'{month}成交率', f'{month}战败率', f'{month}销量',
                f'{month}成交响应时间', f'{month}战败响应时间', f'{month}试驾数',
                f'{month}政策', f'{month}GSEV',
            ]
        _ensure_required_columns(df, required_columns, "数据库 radar_source_2024")
        
        return df


def load_scores_from_db(year: int = 2024) -> pd.DataFrame:
    from models import MonthlyRadarScores
    
    app, db = _ensure_db_app()
    
    with app.app_context():
        records = MonthlyRadarScores.query.filter_by(stat_year=year).all()
        
        if not records:
            raise FileNotFoundError(f"数据库 monthly_radar_scores 表中没有 {year} 年的数据")
        
        dealer_months = {}
        for r in records:
            key = str(r.dealer_code)
            if key not in dealer_months:
                dealer_months[key] = {}
            dealer_months[key][r.stat_month] = r
        
        data = []
        for dealer_code, month_records in dealer_months.items():
            row = {'经销商代码': dealer_code}
            
            for month in range(1, 11):
                m_label = f'{month}月'
                r = month_records.get(month)
                if r:
                    for force_cn, force_db in FORCE_DB_FIELDS.items():
                        value = getattr(r, force_db, None)
                        row[f'{m_label}{force_cn}'] = float(value) if value is not None else np.nan
                else:
                    for force_cn in FORCE_LABELS:
                        row[f'{m_label}{force_cn}'] = np.nan
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        required_columns = ['经销商代码'] + [f'{m}{force}' for m in MONTH_LABELS for force in FORCE_LABELS]
        _ensure_required_columns(df, required_columns, f"数据库 monthly_radar_scores {year}年")
        
        return df


def save_scores_to_db(scores_df: pd.DataFrame, year: int = 2024, calc_version: str = 'v1.0') -> int:
    from models import db as models_db, MonthlyRadarScores
    
    app, db = _ensure_db_app()
    
    with app.app_context():
        saved_count = 0
        
        for _, row in scores_df.iterrows():
            dealer_code = str(row['经销商代码'])
            
            for month in range(1, 11):
                m_label = f'{month}月'
                
                existing = MonthlyRadarScores.query.filter_by(
                    dealer_code=dealer_code,
                    stat_year=year,
                    stat_month=month
                ).first()
                
                if existing:
                    for force_cn, force_db in FORCE_DB_FIELDS.items():
                        col_name = f'{m_label}{force_cn}'
                        if col_name in row:
                            value = row[col_name]
                            if pd.notna(value):
                                setattr(existing, force_db, float(value))
                            else:
                                setattr(existing, force_db, None)
                    existing.calc_version = calc_version
                    existing.source_tag = 'radar_source_2024'
                else:
                    record = MonthlyRadarScores(
                        dealer_code=dealer_code,
                        stat_year=year,
                        stat_month=month,
                        calc_version=calc_version,
                        source_tag='radar_source_2024',
                    )
                    
                    for force_cn, force_db in FORCE_DB_FIELDS.items():
                        col_name = f'{m_label}{force_cn}'
                        if col_name in row:
                            value = row[col_name]
                            if pd.notna(value):
                                setattr(record, force_db, float(value))
                    
                    models_db.session.add(record)
                
                saved_count += 1
        
        models_db.session.commit()
        
        return saved_count


# =========================
# 五力计算层
# =========================
def compute_quantified_scores(source_df: pd.DataFrame) -> pd.DataFrame:
    """从原始 radar 输入表计算五力结果。"""
    df = source_df.copy()

    # 保留标识列
    quantified_scores = pd.DataFrame()
    quantified_scores['经销商代码'] = df['经销商代码'].astype(str)
    quantified_scores['省份'] = df['省份']
    quantified_scores['销售FED级别'] = df['销售FED级别']

    # 评价分直接保留
    for col in NON_NORMALIZED_COLUMNS:
        quantified_scores[col] = _safe_numeric(df[col])

    # 终端检核平均分按原脚本缩放为 /20
    quantified_scores['终端检核平均分'] = _safe_numeric(df['终端检核平均分']).apply(
        lambda x: x / 20 if pd.notna(x) else x
    )

    # 需要量化的列：除 ID_COLUMNS 外全部列
    columns_to_quantify = [col for col in df.columns if col not in ID_COLUMNS]

    scores_df = pd.DataFrame(index=df.index)
    for column in columns_to_quantify:
        if column in NON_NORMALIZED_COLUMNS:
            scores_df[f'{column}评分'] = _safe_numeric(df[column])
        elif column == '终端检核平均分':
            # 这个字段单独保存在 quantified_scores 中，不生成 “评分” 列
            continue
        else:
            scores_df[f'{column}评分'] = _rank_to_score(df[column])

    quantified_scores = pd.concat([quantified_scores, scores_df], axis=1)

    # 月度五力计算
    monthly_forces = pd.DataFrame(index=df.index)

    for m in MONTH_LABELS:
        for force_name, weight_dict in FORCES_WEIGHTS.items():
            if force_name == '经营力':
                monthly_forces[f'{m}{force_name}'] = 3.5
                continue

            def calculate_monthly_weighted_score(row: pd.Series) -> float:
                valid_weights: Dict[str, float] = {}

                for dim, weight in weight_dict.items():
                    if dim == '终端检核平均分':
                        if '终端检核平均分' in row and pd.notna(row['终端检核平均分']):
                            valid_weights[dim] = weight
                    else:
                        score_column_name = f'{m}{dim}评分'
                        if score_column_name in row and pd.notna(row[score_column_name]):
                            valid_weights[dim] = weight

                if not valid_weights:
                    return np.nan

                total_weight = sum(valid_weights.values())
                weighted_sum = 0.0
                for dim, weight in valid_weights.items():
                    if dim == '终端检核平均分':
                        weighted_sum += row['终端检核平均分'] * weight
                    else:
                        weighted_sum += row[f'{m}{dim}评分'] * weight

                return round(weighted_sum / total_weight, 2)

            monthly_forces[f'{m}{force_name}'] = quantified_scores.apply(calculate_monthly_weighted_score, axis=1)

    quantified_scores = pd.concat([quantified_scores, monthly_forces], axis=1)
    return quantified_scores



def export_scores_excel(scores_df: pd.DataFrame, scores_excel_path: str = RADAR_SCORES_EXCEL) -> str:
    os.makedirs(os.path.dirname(scores_excel_path) or '.', exist_ok=True)
    scores_df.to_excel(scores_excel_path, index=False)
    return scores_excel_path



def get_scores_dataframe(
    source_excel_path: str = RADAR_SOURCE_EXCEL,
    scores_excel_path: str = RADAR_SCORES_EXCEL,
    prefer_scores_excel: bool = True,
    refresh: bool = False,
    persist_scores_excel: bool = True,
    use_db: bool = True,
    year: int = 2024,
    persist_to_db: bool = True,
    calc_version: str = 'v1.0',
) -> pd.DataFrame:
    """
    统一取数入口：
    - use_db=False（默认）：使用 Excel 版本
      1. 优先读取 quantified_scores_with_monthly_forces_v2.xlsx
      2. 若不存在/校验失败，则从 2024test.xlsx 重新计算
      3. 可选择把新结果重新导出为 quantified_scores_with_monthly_forces_v2.xlsx
    
    - use_db=True：使用数据库版本
      1. 优先读取 monthly_radar_scores 表
      2. 若不存在，则从 radar_source_2024 表读取并计算
      3. 可选择把新结果写入 monthly_radar_scores 表
    """
    if use_db:
        return get_scores_dataframe_from_db(
            year=year,
            prefer_db=True,
            refresh=refresh,
            persist_to_db=persist_to_db,
            calc_version=calc_version,
        )
    
    if prefer_scores_excel and not refresh:
        try:
            return load_scores_excel(scores_excel_path)
        except Exception:
            pass

    source_df = load_radar_source_excel(source_excel_path)
    scores_df = compute_quantified_scores(source_df)
    if persist_scores_excel:
        export_scores_excel(scores_df, scores_excel_path)
    return scores_df


def get_scores_dataframe_from_db(
    year: int = 2024,
    prefer_db: bool = True,
    refresh: bool = False,
    persist_to_db: bool = True,
    calc_version: str = 'v1.0',
) -> pd.DataFrame:
    """
    数据库版本的统一取数入口：
    1. 优先读取 monthly_radar_scores 表
    2. 若不存在/校验失败，则从 radar_source_2024 表读取并计算
    3. 可选择把新结果写入 monthly_radar_scores 表
    """
    if prefer_db and not refresh:
        try:
            return load_scores_from_db(year)
        except Exception:
            pass
    
    source_df = load_radar_source_from_db(year)
    scores_df = compute_quantified_scores(source_df)
    
    if persist_to_db:
        save_scores_to_db(scores_df, year=year, calc_version=calc_version)
    
    return scores_df


# =========================
# 查询 / 输出层
# =========================
def get_force_columns_for_month(month: Union[str, int]) -> Dict[str, str]:
    m_label = month_label(month)
    return {force: f'{m_label}{force}' for force in FORCE_LABELS}



def get_single_dealer_force_scores(
    dealer_code: str,
    month: Union[str, int],
    scores_df: pd.DataFrame,
) -> Dict[str, Union[float, str]]:
    force_columns = get_force_columns_for_month(month)
    row = scores_df[scores_df['经销商代码'].astype(str) == str(dealer_code)]
    if row.empty:
        return {force: '数据不存在' for force in FORCE_LABELS}

    result: Dict[str, Union[float, str]] = {}
    for force, col in force_columns.items():
        value = row.iloc[0].get(col, np.nan)
        result[force] = round(float(value), 2) if pd.notna(value) else '数据不存在'
    return result



def plot_dealers_radar(
    dealer_codes: Union[str, Sequence[str]],
    month: Union[str, int],
    year: Optional[Union[str, int]] = None,
    source_excel_path: str = RADAR_SOURCE_EXCEL,
    scores_excel_path: str = RADAR_SCORES_EXCEL,
    prefer_scores_excel: bool = True,
    refresh: bool = False,
    persist_scores_excel: bool = True,
    static_dir: str = RADAR_STATIC_DIR,
    use_db: bool = True,
    db_year: int = 2024,
    persist_to_db: bool = True,
    calc_version: str = 'v1.0',
) -> str:
    """
    绘制单个或多个经销商指定月份的雷达图。
    为兼容旧接口，保留 year 参数，但当前列名只按 "1月传播获客力" 这种格式存储，不实际使用 year。
    
    参数：
    - use_db: 是否使用数据库版本（默认 True 使用数据库）
    - db_year: 数据库版本使用的年份（默认 2024）
    - persist_to_db: 是否将计算结果写入数据库（仅 use_db=True 时有效）
    - calc_version: 计算版本号
    """
    _ = year
    if isinstance(dealer_codes, str):
        dealer_codes = [dealer_codes]
    dealer_codes = [str(code).strip() for code in dealer_codes if str(code).strip()]
    if not dealer_codes:
        raise ValueError("dealer_codes 不能为空")

    m_label = month_label(month)
    force_columns = get_force_columns_for_month(month)
    scores_df = get_scores_dataframe(
        source_excel_path=source_excel_path,
        scores_excel_path=scores_excel_path,
        prefer_scores_excel=prefer_scores_excel,
        refresh=refresh,
        persist_scores_excel=persist_scores_excel,
        use_db=use_db,
        year=db_year,
        persist_to_db=persist_to_db,
        calc_version=calc_version,
    )
    scores_df = scores_df.copy()
    scores_df['经销商代码'] = scores_df['经销商代码'].astype(str)

    valid_dealers = []
    invalid_dealers = []
    for code in dealer_codes:
        if (scores_df['经销商代码'] == code).any():
            valid_dealers.append(code)
        else:
            invalid_dealers.append(code)

    if not valid_dealers:
        raise ValueError(f"没有有效的经销商代码。无效代码：{invalid_dealers}")

    data_length = len(FORCE_LABELS)
    angles = np.linspace(0, 2 * np.pi, data_length, endpoint=False).tolist()
    angles_closed = np.concatenate((angles, [angles[0]]))

    fig = plt.figure(figsize=(6 * min(len(valid_dealers), 2), 6 * ((len(valid_dealers) + 1) // 2)), dpi=150)
    cols = min(len(valid_dealers), 2)
    rows = (len(valid_dealers) + cols - 1) // cols

    for idx, dealer_code in enumerate(valid_dealers, start=1):
        ax = plt.subplot(rows, cols, idx, polar=True)
        dealer_row = scores_df[scores_df['经销商代码'] == dealer_code].iloc[0]

        values = []
        for force in FORCE_LABELS:
            col = force_columns[force]
            value = dealer_row.get(col, np.nan)
            values.append(float(value) if pd.notna(value) else 0.0)

        score_closed = np.concatenate((values, [values[0]]))

        # 背景网格
        for j in np.arange(0, 5.1, 0.5):
            ax.plot(angles_closed, [j] * len(angles_closed), '-', lw=0.5, color='gray')
        for j in range(data_length):
            ax.plot([angles[j], angles[j]], [0, 5], '-', lw=1, color='gray')

        # 数据区域
        ax.fill(angles_closed, score_closed, color='lightblue', alpha=0.6)
        ax.plot(angles_closed, score_closed, color='blue', lw=2)

        ax.spines['polar'].set_visible(False)
        ax.grid(False)

        for a, b in zip(angles_closed, score_closed):
            ax.text(a, b + 0.1, f'{b:.2f}', ha='center', va='center', fontsize=10, color='b')

        ax.set_thetagrids(np.array(angles) * 180 / np.pi, FORCE_LABELS)
        ax.set_theta_zero_location('N')
        ax.set_rlim(0, 5)
        ax.set_rlabel_position(0)
        ax.set_title(f"经销商 {dealer_code} 的 {m_label} 五力比较")

    plt.tight_layout()

    os.makedirs(static_dir, exist_ok=True)
    filename = f"radar_{m_label}_{_safe_filename('_'.join(valid_dealers[:5]))}"
    if len(valid_dealers) > 5:
        filename += f"_and_{len(valid_dealers) - 5}_more"
    img_path = os.path.join(static_dir, f"{filename}.png")

    image_stream = BytesIO()
    plt.savefig(image_stream, format='png', bbox_inches='tight')
    image_stream.seek(0)
    plt.close(fig)

    with open(img_path, 'wb') as f:
        f.write(image_stream.getvalue())

    return img_path



def dealers_score(
    dealer_codes: Union[str, Sequence[str]],
    month: Union[str, int],
    year: Optional[Union[str, int]] = None,
    source_excel_path: str = RADAR_SOURCE_EXCEL,
    scores_excel_path: str = RADAR_SCORES_EXCEL,
    prefer_scores_excel: bool = True,
    refresh: bool = False,
    persist_scores_excel: bool = True,
    use_db: bool = True,
    db_year: int = 2024,
    persist_to_db: bool = True,
    calc_version: str = 'v1.0',
) -> Dict[str, Dict[str, Union[float, str]]]:
    """
    返回前端表格展示用的五力分数与综合得分。
    为兼容旧接口，保留 year 参数，但当前实现不使用 year 拼列名。
    
    参数：
    - use_db: 是否使用数据库版本（默认 True 使用数据库）
    - db_year: 数据库版本使用的年份（默认 2024）
    - persist_to_db: 是否将计算结果写入数据库（仅 use_db=True 时有效）
    - calc_version: 计算版本号
    """
    _ = year
    if isinstance(dealer_codes, str):
        dealer_codes = [dealer_codes]
    dealer_codes = [str(code).strip() for code in dealer_codes if str(code).strip()]
    if not dealer_codes:
        raise ValueError("dealer_codes 不能为空")

    force_columns = get_force_columns_for_month(month)
    scores_df = get_scores_dataframe(
        source_excel_path=source_excel_path,
        scores_excel_path=scores_excel_path,
        prefer_scores_excel=prefer_scores_excel,
        refresh=refresh,
        persist_scores_excel=persist_scores_excel,
        use_db=use_db,
        year=db_year,
        persist_to_db=persist_to_db,
        calc_version=calc_version,
    ).copy()
    scores_df['经销商代码'] = scores_df['经销商代码'].astype(str)

    result: Dict[str, Dict[str, Union[float, str]]] = {}
    for dealer_code in dealer_codes:
        row = scores_df[scores_df['经销商代码'] == dealer_code]
        if row.empty:
            result[dealer_code] = {col: '数据不存在' for col in force_columns.values()}
            result[dealer_code]['综合得分'] = '数据不存在'
            continue

        row_data = row.iloc[0]
        dealer_result: Dict[str, Union[float, str]] = {}
        total_score = 0.0
        has_numeric = False

        for force, col_name in force_columns.items():
            raw_score = row_data.get(col_name, np.nan)
            if pd.notna(raw_score):
                raw_score = float(raw_score)
                dealer_result[col_name] = round(raw_score * 20 * DISPLAY_SCORE_WEIGHTS[force], 2)
                total_score += dealer_result[col_name]
                has_numeric = True
            else:
                dealer_result[col_name] = '数据不存在'

        dealer_result['综合得分'] = round(total_score, 2) if has_numeric else '数据不存在'
        result[dealer_code] = dealer_result

    return result



def refresh_scores_excel(
    source_excel_path: str = RADAR_SOURCE_EXCEL,
    scores_excel_path: str = RADAR_SCORES_EXCEL,
) -> str:
    """强制从原始 radar Excel 重算，并覆盖写出结果 Excel。"""
    source_df = load_radar_source_excel(source_excel_path)
    scores_df = compute_quantified_scores(source_df)
    return export_scores_excel(scores_df, scores_excel_path)



def main() -> None:
    print("当前 radar 仅支持 2024 年 1-10 月。")
    while True:
        dealer_codes_input = input("请输入要查询的经销商代码（多个代码用逗号分隔，输入 q 退出）: ").strip()
        if dealer_codes_input.lower() == 'q':
            break
        month_input = input("请输入要查询的月份（1-10）: ").strip()
        if month_input not in SUPPORTED_MONTHS:
            print("请输入有效月份（1-10）。")
            continue
        dealer_codes = [code.strip() for code in dealer_codes_input.split(',') if code.strip()]
        if not dealer_codes:
            print("请输入有效的经销商代码。")
            continue

        try:
            img_path = plot_dealers_radar(dealer_codes, month_input)
            score_info = dealers_score(dealer_codes, month_input)
            print(f"雷达图已生成：{img_path}")
            print(score_info)
        except Exception as e:
            print(f"发生错误：{e}")


if __name__ == "__main__":
    main()
