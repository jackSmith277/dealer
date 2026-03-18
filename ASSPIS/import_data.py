"""
ASSPIS 数据导入脚本
将Excel数据导入到MySQL数据库

使用方法：
    python import_data.py --table all          # 导入所有表
    python import_data.py --table metrics      # 只导入monthly_metrics_11d
    python import_data.py --table radar        # 只导入radar_source_2024
"""

import os
import re
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from models import db, MonthlyMetrics11d, RadarSource2024, MonthlyRadarScores

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/dealer_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

db.init_app(app)

BASE_DIR = Path(__file__).resolve().parent

FILE_24_11D = os.getenv("ASSPIS_FILE_24", str(BASE_DIR / "24年11维度数据.xlsx"))
FILE_22_23 = os.getenv("ASSPIS_FILE_2223", str(BASE_DIR / "22-23数据.xlsx"))
FILE_2024TEST = os.getenv("ASSPIS_FILE_2024TEST", str(BASE_DIR / "2024test.xlsx"))


def unify_column_names(df):
    """统一列名格式，去掉所有空白"""
    def _norm(x):
        return re.sub(r'[\s\u3000]+', '', str(x)).strip()
    df.columns = [_norm(c) for c in df.columns]
    if '经销商代码' in df.columns:
        df['经销商代码'] = df['经销商代码'].astype(str).str.strip()
    return df


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


def safe_numeric(value):
    """安全转换为数值，保留空值"""
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def import_monthly_metrics_11d():
    """
    导入monthly_metrics_11d表
    数据源：24年13维度数据.xlsx 和 22-23数据.xlsx
    """
    print("\n" + "="*60)
    print("开始导入 monthly_metrics_11d 表")
    print("="*60)

    all_records = []
    
    field_mapping = {
        '销量': 'sales',
        '潜客量': 'potential_customers',
        '试驾数': 'test_drives',
        '线索量': 'leads',
        '客流量': 'customer_flow',
        '战败率': 'defeat_rate',
        '成交率': 'success_rate',
        '成交响应时间': 'success_response_time',
        '战败响应时间': 'defeat_response_time',
        '政策': 'policy',
        'GSEV': 'gsev',
    }
    
    cn_field_mapping = {v: k for k, v in field_mapping.items()}

    files_to_process = [
        (FILE_24_11D, [2024]),
        (FILE_22_23, [2022, 2023]),
    ]

    for file_path, default_years in files_to_process:
        if not os.path.exists(file_path):
            print(f"警告：文件不存在 - {file_path}")
            continue

        print(f"\n处理文件: {file_path}")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"  发现 {len(sheet_names)} 个工作表")
        except Exception as e:
            print(f"  错误：无法读取文件 - {e}")
            continue

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df = unify_column_names(df)
                
                if '经销商代码' not in df.columns:
                    continue

                matched_field = None
                for cn_key, db_field in field_mapping.items():
                    if cn_key in sheet_name:
                        matched_field = db_field
                        break
                
                if not matched_field:
                    continue

                print(f"  处理工作表: {sheet_name} -> {matched_field}")

                months_found = set()
                years_found = set()
                
                for col in df.columns:
                    month = parse_month_from_col(col)
                    year = parse_year_from_col(col)
                    if month:
                        months_found.add(month)
                    if year:
                        years_found.add(year)

                if not years_found:
                    years_found = set(default_years)
                
                months_found = sorted(months_found) if months_found else list(range(1, 13))
                years_found = sorted(years_found)

                print(f"    年份: {years_found}")
                print(f"    月份: {months_found}")

                for _, row in df.iterrows():
                    dealer_code = str(row.get('经销商代码', '')).strip()
                    if not dealer_code or dealer_code == 'nan':
                        continue

                    for col in df.columns:
                        col_clean = re.sub(r'[\s\u3000]+', '', str(col))
                        
                        year = parse_year_from_col(col_clean)
                        month = parse_month_from_col(col_clean)
                        
                        if not year or not month:
                            continue
                        
                        cn_field = cn_field_mapping.get(matched_field, '')
                        if cn_field not in col_clean:
                            continue
                        
                        value = row.get(col)
                        if value is None or pd.isna(value):
                            continue
                        
                        value = safe_numeric(value)
                        if value is None:
                            continue

                        record_key = (dealer_code, year, month)
                        existing_record = None
                        for r in all_records:
                            if (r['dealer_code'], r['stat_year'], r['stat_month']) == record_key:
                                existing_record = r
                                break
                        
                        if existing_record:
                            existing_record[matched_field] = value
                        else:
                            new_record = {
                                'dealer_code': dealer_code,
                                'stat_year': year,
                                'stat_month': month,
                                matched_field: value,
                            }
                            all_records.append(new_record)

            except Exception as e:
                print(f"  处理工作表 {sheet_name} 时出错: {e}")
                continue

    print(f"\n共收集 {len(all_records)} 条记录")
    
    with app.app_context():
        print("清空现有数据...")
        MonthlyMetrics11d.query.delete()
        db.session.commit()

        print("开始批量插入...")
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i+batch_size]
            for record in batch:
                db_record = MonthlyMetrics11d(**record)
                db.session.add(db_record)
            
            try:
                db.session.commit()
                total_inserted += len(batch)
                print(f"  已插入 {total_inserted}/{len(all_records)} 条记录")
            except Exception as e:
                db.session.rollback()
                print(f"  批次插入失败: {e}")

    print(f"monthly_metrics_11d 表导入完成，共 {total_inserted} 条记录")
    return total_inserted


def import_radar_source_2024():
    """
    导入radar_source_2024表
    数据源：2024test.xlsx
    """
    print("\n" + "="*60)
    print("开始导入 radar_source_2024 表")
    print("="*60)

    if not os.path.exists(FILE_2024TEST):
        print(f"错误：文件不存在 - {FILE_2024TEST}")
        return 0

    print(f"处理文件: {FILE_2024TEST}")
    
    try:
        df = pd.read_excel(FILE_2024TEST)
        df = unify_column_names(df)
        print(f"  共 {len(df)} 行数据")
        print(f"  列名: {list(df.columns)[:20]}...")
    except Exception as e:
        print(f"  错误：无法读取文件 - {e}")
        return 0

    month_fields = [
        'customer_flow', 'potential_customers', 'leads', 'success_rate',
        'defeat_rate', 'sales', 'success_response_time', 'defeat_response_time',
        'test_drives', 'policy', 'gsev', 'evaluation_score'
    ]

    cn_to_field = {
        '客流量': 'customer_flow',
        '潜客量': 'potential_customers',
        '线索量': 'leads',
        '成交率': 'success_rate',
        '战败率': 'defeat_rate',
        '销量': 'sales',
        '成交响应时间': 'success_response_time',
        '战败响应时间': 'defeat_response_time',
        '试驾数': 'test_drives',
        '政策': 'policy',
        'GSEV': 'gsev',
        '评价分': 'evaluation_score',
    }

    records = []
    
    for _, row in df.iterrows():
        dealer_code = str(row.get('经销商代码', '')).strip()
        if not dealer_code or dealer_code == 'nan':
            continue

        record = {
            'dealer_code': dealer_code,
            'province': safe_numeric(row.get('省份')) if isinstance(row.get('省份'), (int, float)) else str(row.get('省份', '')).strip() if row.get('省份') else None,
            'fed_level': str(row.get('销售FED级别', '')).strip() if row.get('销售FED级别') else None,
            'terminal_check_avg': safe_numeric(row.get('终端检核平均分')),
        }

        for col in df.columns:
            month = parse_month_from_col(col)
            if not month or month > 10:
                continue

            for cn_name, field_name in cn_to_field.items():
                if cn_name in col:
                    col_value = safe_numeric(row.get(col))
                    if col_value is not None:
                        db_field_name = f'{field_name}_m{month:02d}'
                        record[db_field_name] = col_value
                    break

        records.append(record)

    print(f"共收集 {len(records)} 条记录")

    with app.app_context():
        print("清空现有数据...")
        RadarSource2024.query.delete()
        db.session.commit()

        print("开始批量插入...")
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            for record in batch:
                db_record = RadarSource2024(**record)
                db.session.add(db_record)
            
            try:
                db.session.commit()
                total_inserted += len(batch)
                print(f"  已插入 {total_inserted}/{len(records)} 条记录")
            except Exception as e:
                db.session.rollback()
                print(f"  批次插入失败: {e}")

    print(f"radar_source_2024 表导入完成，共 {total_inserted} 条记录")
    return total_inserted


def create_tables():
    """创建数据库表"""
    print("\n创建数据库表...")
    with app.app_context():
        db.create_all()
        print("数据库表创建完成")


def main():
    parser = argparse.ArgumentParser(description='ASSPIS数据导入工具')
    parser.add_argument('--table', type=str, default='all',
                        choices=['all', 'metrics', 'radar', 'create'],
                        help='要导入的表: all(全部), metrics(monthly_metrics_11d), radar(radar_source_2024), create(仅创建表)')
    
    args = parser.parse_args()

    print("="*60)
    print("ASSPIS 数据导入工具")
    print("="*60)
    print(f"数据库: mysql+pymysql://root:***@localhost:3306/dealer_management")
    print(f"操作: {args.table}")

    if args.table in ['all', 'create']:
        create_tables()

    if args.table in ['all', 'metrics']:
        import_monthly_metrics_11d()

    if args.table in ['all', 'radar']:
        import_radar_source_2024()

    print("\n" + "="*60)
    print("数据导入完成")
    print("="*60)


if __name__ == '__main__':
    main()
