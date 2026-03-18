"""
详细验证各年份数据
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, MonthlyMetrics11d
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/dealer_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("各年份记录数统计:")
    
    result = db.session.query(
        MonthlyMetrics11d.stat_year,
        func.count(MonthlyMetrics11d.id)
    ).group_by(MonthlyMetrics11d.stat_year).order_by(MonthlyMetrics11d.stat_year).all()
    
    for year, count in result:
        print(f"  {year}年: {count}条记录")
    
    print("\n各年份示例数据:")
    for year in [2022, 2023, 2024]:
        sample = MonthlyMetrics11d.query.filter_by(stat_year=year).first()
        if sample:
            print(f"  {year}年示例: dealer_code={sample.dealer_code}, month={sample.stat_month}, sales={sample.sales}")
