"""
验证数据导入结果
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_config import get_database_uri

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, MonthlyMetrics11d, RadarSource2024, MonthlyRadarScores

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', get_database_uri())
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("="*60)
    print("数据导入验证")
    print("="*60)
    
    print("\n1. monthly_metrics_11d 表统计:")
    total = MonthlyMetrics11d.query.count()
    print(f"   总记录数: {total}")
    
    years = db.session.query(MonthlyMetrics11d.stat_year).distinct().all()
    print(f"   年份分布: {[y[0] for y in years]}")
    
    dealers = db.session.query(MonthlyMetrics11d.dealer_code).distinct().count()
    print(f"   经销商数量: {dealers}")
    
    sample = MonthlyMetrics11d.query.first()
    if sample:
        print(f"   示例记录: dealer_code={sample.dealer_code}, year={sample.stat_year}, month={sample.stat_month}")
        print(f"             sales={sample.sales}, potential_customers={sample.potential_customers}")
    
    print("\n2. radar_source_2024 表统计:")
    total_radar = RadarSource2024.query.count()
    print(f"   总记录数: {total_radar}")
    
    sample_radar = RadarSource2024.query.first()
    if sample_radar:
        print(f"   示例记录: dealer_code={sample_radar.dealer_code}, province={sample_radar.province}")
        print(f"             sales_m01={sample_radar.sales_m01}, customer_flow_m01={sample_radar.customer_flow_m01}")
    
    print("\n" + "="*60)
    print("验证完成")
    print("="*60)
