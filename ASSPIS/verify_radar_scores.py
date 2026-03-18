"""验证 monthly_radar_scores 表数据"""
from models import db, MonthlyRadarScores
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/dealer_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print('monthly_radar_scores 记录数:', MonthlyRadarScores.query.count())
    r = MonthlyRadarScores.query.first()
    if r:
        print(f'示例: {r.dealer_code}, {r.stat_year}, {r.stat_month}')
        print(f'  传播获客力={r.spread_force}, 体验力={r.experience_force}')
        print(f'  转化力={r.conversion_force}, 服务力={r.service_force}, 经营力={r.operation_force}')
    else:
        print('无数据')
