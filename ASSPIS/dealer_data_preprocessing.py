import pandas as pd
import re
import os

USE_EXCEL = False

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'dealer_management')
}

def get_db_connection():
    import pymysql
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4'
    )


# ==============================================================================
# DealerData 类定义
# ==============================================================================
class DealerData:
    """
    经销商数据类，存储各维度月度数据
    修改：使用 (year, month) 元组作为 key，避免不同年份同一月份数据覆盖
    """

    def __init__(self, dealer_code):
        self.dealer_code = dealer_code
        self.sales = {}
        self.potential_customers = {}
        self.test_drives = {}
        self.leads = {}
        self.customer_flow = {}
        self.defeat_rate = {}
        self.success_rate = {}
        self.success_response_time = {}
        self.defeat_response_time = {}
        self.policy = {}
        self.gsev = {}

        # Phase2.5: dealer 分层画像（训练集分层纳入/加权使用）
        self.profile = {}
        self.tier = "unknown"

    def add_monthly_data(self, year, month, sales=None, potential_customers=None,
                         test_drives=None, leads=None, customer_flow=None,
                         defeat_rate=None, success_rate=None,
                         success_response_time=None, defeat_response_time=None,
                         policy=None, gsev=None):
        """
        添加月度数据，使用 (year, month) 元组作为 key
        """
        key = (year, month)
        if sales is not None:
            self.sales[key] = sales
        if potential_customers is not None:
            self.potential_customers[key] = potential_customers
        if test_drives is not None:
            self.test_drives[key] = test_drives
        if leads is not None:
            self.leads[key] = leads
        if customer_flow is not None:
            self.customer_flow[key] = customer_flow
        if defeat_rate is not None:
            self.defeat_rate[key] = defeat_rate
        if success_rate is not None:
            self.success_rate[key] = success_rate
        if success_response_time is not None:
            self.success_response_time[key] = success_response_time
        if defeat_response_time is not None:
            self.defeat_response_time[key] = defeat_response_time
        if policy is not None:
            self.policy[key] = policy
        if gsev is not None:
            self.gsev[key] = gsev


# ==============================================================================
# 辅助函数定义（必须在调用前定义）
# ==============================================================================
def unify_column_names(df):
    """
    统一列名格式：
    - 去掉所有空白（含全角空格），避免 '2024.1 月潜客量' vs '2024.1月潜客量' 匹配失败
    """
    def _norm(x):
        return re.sub(r'[\s\u3000]+', '', str(x)).strip()

    df.columns = [_norm(c) for c in df.columns]

    if '经销商代码' in df.columns:
        df['经销商代码'] = df['经销商代码'].astype(str).str.strip()

    return df


def infer_months_from_columns(df):
    months = set()
    for c in df.columns:
        c = re.sub(r"[\s\u3000]+", "", str(c))
        m = re.search(r"(?:^|\.)(\d{1,2})月", c)  # 2024.1月 / 1月
        if m:
            mm = int(m.group(1))
            if 1 <= mm <= 12:
                months.add(mm)
    return sorted(months) if months else list(range(1, 13))


def infer_year_from_columns(df):
    years = set()
    for c in df.columns:
        c = re.sub(r"[\s\u3000]+", "", str(c))
        m = re.search(r"((?:19|20)\d{2})\.(\d{1,2})", c)  # 2022.1
        if m:
            years.add(int(m.group(1)))
    return sorted(years) if years else [2024]


def process_data(data, dealers, data_type, col_prefix, year_list=None):
    """
    处理单个数据表，填充到 dealers 字典
    支持 (year, month) key
    """
    if year_list is None:
        year_list = infer_year_from_columns(data)

    months = infer_months_from_columns(data)

    for _, row in data.iterrows():
        dealer_code = str(row.get('经销商代码', '')).strip()
        if not dealer_code:
            continue

        if dealer_code not in dealers:
            dealers[dealer_code] = DealerData(dealer_code)

        for year in year_list:
            for month in months:
                # 尝试更多列名变体（含/不含“月”）
                col_names_to_try = [
                    f'{year}.{month}月{col_prefix}',
                    f'{year}.{month}{col_prefix}',       # 无“月”
                    f'{month}月{col_prefix}',
                    f'{month}{col_prefix}',              # 无“月”
                    f'{year}年{month}月{col_prefix}',
                    f'{year}年{month}{col_prefix}',      # 无“月”
                ]

                value = None
                for col_name in col_names_to_try:
                    if col_name in data.columns:
                        value = row.get(col_name, None)
                        break
                COUNT_TYPES = {"sales", "potential_customers", "test_drives", "leads", "customer_flow"}
                if value is None or pd.isna(value):
                    if data_type in COUNT_TYPES:
                        value = 0.0
                    else:
                        continue
                dealers[dealer_code].add_monthly_data(year=year, month=month, **{data_type: value})
# ==============================================================================
# Phase2.5：经销商分层（用于训练集分层纳入 / sample_weight）
# - 不改变 load_and_process_data() 的返回结构，仅在 DealerData 上增加 tier/profile 字段
# - tier 规则基于“销量时间跨度 + 非零月份占比 + 规模”，可通过 env 调参
# ==============================================================================

def _dealer_profile_from_sales(sales_map: dict) -> dict:
    tuples = []
    if isinstance(sales_map, dict):
        for k, v in sales_map.items():
            if not (isinstance(k, tuple) and len(k) == 2):
                continue
            if v is None:
                continue
            y, m = int(k[0]), int(k[1])
            tuples.append((y, m, float(v)))

    if not tuples:
        return {
            "months_total": 0,
            "months_nonzero": 0,
            "nonzero_ratio": 0.0,
            "sales_sum": 0.0,
            "sales_mean_nonzero": 0.0,
            "first_ym": None,
            "last_ym": None,
        }

    tuples.sort(key=lambda x: (x[0], x[1]))
    months_total = len(tuples)
    nonzero_vals = [v for _, _, v in tuples if v > 0]
    months_nonzero = len(nonzero_vals)
    sales_sum = float(sum(max(v, 0.0) for _, _, v in tuples))
    sales_mean_nonzero = float(sum(nonzero_vals) / months_nonzero) if months_nonzero else 0.0
    nonzero_ratio = float(months_nonzero / months_total) if months_total else 0.0

    first_ym = (tuples[0][0], tuples[0][1])
    last_ym = (tuples[-1][0], tuples[-1][1])

    return {
        "months_total": int(months_total),
        "months_nonzero": int(months_nonzero),
        "nonzero_ratio": float(nonzero_ratio),
        "sales_sum": float(sales_sum),
        "sales_mean_nonzero": float(sales_mean_nonzero),
        "first_ym": first_ym,
        "last_ym": last_ym,
    }


def annotate_dealer_tiers(dealers: dict) -> None:
    # 默认阈值：你可以用 env 细调
    core_min_months = int(os.getenv("TIER_CORE_MIN_MONTHS", "24"))
    regular_min_months = int(os.getenv("TIER_REGULAR_MIN_MONTHS", "12"))
    core_min_mean = float(os.getenv("TIER_CORE_MIN_MEAN_SALES", "35"))
    regular_min_mean = float(os.getenv("TIER_REGULAR_MIN_MEAN_SALES", "15"))
    min_nonzero_ratio = float(os.getenv("TIER_MIN_NONZERO_RATIO", "0.60"))

    for _, dealer in dealers.items():
        sales_map = getattr(dealer, "sales", {}) or {}
        profile = _dealer_profile_from_sales(sales_map)
        dealer.profile = profile

        months_total = int(profile.get("months_total", 0))
        mean_nonzero = float(profile.get("sales_mean_nonzero", 0.0))
        nonzero_ratio = float(profile.get("nonzero_ratio", 0.0))

        tier = "tail"
        if (months_total >= core_min_months) and (mean_nonzero >= core_min_mean) and (nonzero_ratio >= min_nonzero_ratio):
            tier = "core"
        elif (months_total >= regular_min_months) and (mean_nonzero >= regular_min_mean) and (nonzero_ratio >= (min_nonzero_ratio * 0.8)):
            tier = "regular"

        dealer.tier = tier



def load_and_process_data(file_paths, selected_year=None, selected_month=None):
    """
    加载并处理多个 Excel 文件的数据
    - 只使用“关键字包含”匹配真实 sheet 名（支持 2024各月xxx / 2022-2023各月xxx）
    - 移除旧的“精确 sheet 名读取”循环（会导致 Worksheet not found 噪声报错）
    """
    import unicodedata

    dealers = {}
    all_dealer_codes = set()

    # 关键字配置（不是精确 sheet 名）
    sheet_configs = [
        ('各月销量', 'sales', '销量'),
        ('各月潜客量', 'potential_customers', '潜客量'),
        ('各月试驾数', 'test_drives', '试驾数'),
        ('各月线索量', 'leads', '线索量'),
        ('各月客流量', 'customer_flow', '客流量'),
        ('各月战败率', 'defeat_rate', '战败率'),
        ('各月成交率', 'success_rate', '成交率'),
        ('各月成交响应时间', 'success_response_time', '成交响应时间'),
        ('各月战败响应时间', 'defeat_response_time', '战败响应时间'),
        ('政策', 'policy', '政策'),     # 支持 2024政策
        ('GSEV', 'gsev', 'GSEV'),       # 你已统一修正为 GSEV
    ]

    def _norm(s: str) -> str:
        # 统一全/半角、去空白（含全角空格）、小写
        s = unicodedata.normalize("NFKC", str(s))
        s = re.sub(r'[\s\u3000]+', '', s)
        return s.lower()

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"警告：文件不存在 {file_path}")
            continue

        print(f"正在加载文件：{file_path}")

        try:
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names

            for sheet_key, data_type, col_prefix in sheet_configs:
                key_n = _norm(sheet_key)

                # 找出所有“包含关键字”的 sheet
                matched = [raw for raw in sheet_names if key_n in _norm(raw)]

                if not matched:
                    print(f"读取 sheet (关键字 '{sheet_key}') 失败：未找到。当前 sheets: {sheet_names}")
                    continue

                for real_sheet_name in matched:
                    try:
                        data = pd.read_excel(xl, sheet_name=real_sheet_name)
                        data = unify_column_names(data)

                        if '经销商代码' in data.columns:
                            codes = data['经销商代码'].dropna().astype(str).str.strip().tolist()
                            all_dealer_codes.update(codes)

                        process_data(data, dealers, data_type, col_prefix)

                    except Exception as e:
                        print(f"读取 sheet '{real_sheet_name}' 失败：{e}")
                        continue

        except Exception as e:
            print(f"读取文件 {file_path} 失败：{e}")
            continue

    # Phase2.5: 标注经销商 tier/profile（用于主流程分层纳入/加权）
    try:
        annotate_dealer_tiers(dealers)
    except Exception as _e:
        print(f"经销商分层标注失败（将跳过）：{_e}")

    dealer_codes = sorted(list(all_dealer_codes))
    print(f"加载完成，共 {len(dealers)} 个经销商，{len(dealer_codes)} 个唯一代码")
    return dealers, dealer_codes


def filter_dealers_by_month(dealers, year, month):
    """
    根据年份和月份过滤经销商数据（可选功能，用于特定查询）
    返回只包含指定年月数据的经销商字典
    """
    filtered_dealers = {}
    key = (year, month)

    for code, dealer in dealers.items():
        # 检查该经销商在指定年月是否有数据
        has_data = False
        for attr in ['sales', 'potential_customers', 'test_drives', 'leads',
                     'customer_flow', 'defeat_rate', 'success_rate']:
            if key in getattr(dealer, attr, {}):
                has_data = True
                break

        if has_data:
            filtered_dealers[code] = dealer

    return filtered_dealers


def get_dealer_monthly_data(dealer_data, attr_name, year, month):
    """
    获取经销商指定年月的特定属性数据
    """
    key = (year, month)
    return getattr(dealer_data, attr_name, {}).get(key, None)


def get_all_available_months(dealer_data):
    """
    获取经销商所有有数据的月份（返回 (year, month) 元组列表）
    """
    months_set = set()
    for attr in ['sales', 'potential_customers', 'test_drives', 'leads',
                 'customer_flow', 'defeat_rate', 'success_rate',
                 'success_response_time', 'defeat_response_time', 'policy', 'gsev']:
        data_dict = getattr(dealer_data, attr, {})
        for key in data_dict.keys():
            if isinstance(key, tuple) and len(key) == 2:
                months_set.add(key)

    return sorted(list(months_set))


def get_available_years(dealers):
    """
    获取所有经销商数据中涉及的年份列表
    """
    years_set = set()
    for dealer in dealers.values():
        for attr in ['sales', 'potential_customers', 'test_drives', 'leads',
                     'customer_flow', 'defeat_rate', 'success_rate']:
            data_dict = getattr(dealer, attr, {})
            for key in data_dict.keys():
                if isinstance(key, tuple) and len(key) == 2:
                    years_set.add(key[0])

    return sorted(list(years_set))


def get_available_months_for_year(dealers, year):
    """
    获取指定年份下所有经销商有数据的月份列表
    """
    months_set = set()
    for dealer in dealers.values():
        for attr in ['sales', 'potential_customers', 'test_drives', 'leads',
                     'customer_flow', 'defeat_rate', 'success_rate']:
            data_dict = getattr(dealer, attr, {})
            for key in data_dict.keys():
                if isinstance(key, tuple) and len(key) == 2 and key[0] == year:
                    months_set.add(key[1])

    return sorted(list(months_set))


def load_and_process_data_from_db():
    """
    从数据库 monthly_metrics_11d 表加载经销商数据
    返回与 load_and_process_data 相同格式的 (dealers, dealer_codes)
    """
    dealers = {}
    all_dealer_codes = set()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
            SELECT dealer_code, stat_year, stat_month,
                   sales, potential_customers, test_drives, leads, customer_flow,
                   defeat_rate, success_rate, success_response_time, defeat_response_time,
                   policy, gsev
            FROM monthly_metrics_11d
            ORDER BY dealer_code, stat_year, stat_month
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        for row in rows:
            dealer_code = str(row['dealer_code']).strip()
            year = int(row['stat_year'])
            month = int(row['stat_month'])
            
            if dealer_code not in dealers:
                dealers[dealer_code] = DealerData(dealer_code)
            
            dealer = dealers[dealer_code]
            all_dealer_codes.add(dealer_code)
            
            if row['sales'] is not None:
                dealer.sales[(year, month)] = float(row['sales'])
            if row['potential_customers'] is not None:
                dealer.potential_customers[(year, month)] = float(row['potential_customers'])
            if row['test_drives'] is not None:
                dealer.test_drives[(year, month)] = float(row['test_drives'])
            if row['leads'] is not None:
                dealer.leads[(year, month)] = float(row['leads'])
            if row['customer_flow'] is not None:
                dealer.customer_flow[(year, month)] = float(row['customer_flow'])
            if row['defeat_rate'] is not None:
                dealer.defeat_rate[(year, month)] = float(row['defeat_rate'])
            if row['success_rate'] is not None:
                dealer.success_rate[(year, month)] = float(row['success_rate'])
            if row['success_response_time'] is not None:
                dealer.success_response_time[(year, month)] = float(row['success_response_time'])
            if row['defeat_response_time'] is not None:
                dealer.defeat_response_time[(year, month)] = float(row['defeat_response_time'])
            if row['policy'] is not None:
                dealer.policy[(year, month)] = float(row['policy'])
            if row['gsev'] is not None:
                dealer.gsev[(year, month)] = float(row['gsev'])
        
        cursor.close()
        conn.close()
        
        try:
            annotate_dealer_tiers(dealers)
        except Exception as _e:
            print(f"经销商分层标注失败（将跳过）：{_e}")
        
        dealer_codes = sorted(list(all_dealer_codes))
        print(f"[DB] 从数据库加载完成，共 {len(dealers)} 个经销商，{len(dealer_codes)} 个唯一代码")
        return dealers, dealer_codes
        
    except Exception as e:
        print(f"[DB] 从数据库加载失败: {e}")
        import traceback
        traceback.print_exc()
        return {}, []


def load_dealers_data(file_paths=None, use_excel=None):
    """
    统一入口：根据 USE_EXCEL 开关选择数据来源
    """
    global USE_EXCEL
    if use_excel is not None:
        USE_EXCEL = use_excel
    
    if USE_EXCEL:
        print("[数据源] 使用 Excel 文件")
        if file_paths is None:
            file_paths = [
                "data/24年11维度数据.xlsx",
                "data/22-23数据.xlsx"
            ]
        return load_and_process_data(file_paths)
    else:
        print("[数据源] 使用数据库")
        return load_and_process_data_from_db()


import pymysql.cursors