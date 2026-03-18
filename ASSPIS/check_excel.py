import pandas as pd
import re

def parse_month_from_col(col_name):
    """从列名中解析月份"""
    col_name = re.sub(r'[\s\u3000]+', '', str(col_name))
    patterns = [
        r'(?:^|\.)(\d{1,2})月',
        r'(\d{1,2})月',
        r'm(\d{1,2})$',
        r'_(\d{1,2})$',
    ]
    for pattern in patterns:
        m = re.search(pattern, col_name)
        if m:
            month = int(m.group(1))
            if 1 <= month <= 12:
                return month
    return None

def parse_year_from_col(col_name):
    """从列名中解析年份"""
    col_name = re.sub(r'[\s\u3000]+', '', str(col_name))
    m = re.search(r'((?:19|20)\d{2})', col_name)
    if m:
        return int(m.group(1))
    return None

print("检查 24年11维度数据.xlsx")
df = pd.read_excel('24年11维度数据.xlsx', sheet_name='2024各月销量', nrows=3)
print('Columns:', list(df.columns))
print()

for col in df.columns:
    col_clean = re.sub(r'[\s\u3000]+', '', str(col))
    year = parse_year_from_col(col_clean)
    month = parse_month_from_col(col_clean)
    field = 'sales'
    field_match = field.replace('_', '') in col_clean.replace('_', '')
    print(f"  {col} -> clean: {col_clean}, year: {year}, month: {month}, field_match: {field_match}")
