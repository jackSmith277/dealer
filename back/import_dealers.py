import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_config import get_database_uri

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', get_database_uri())
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def import_dealers():
    with app.app_context():
        try:
            result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            dealers_data = result.fetchall()
            
            print(f"找到 {len(dealers_data)} 条经销商数据")
            
            added_count = 0
            for row in dealers_data:
                dealer_code = row[0] or ''
                province = row[1] or ''
                city = row[2] or ''
                fed_level = row[3] or ''
                
                if not dealer_code:
                    continue
                
                existing_user = db.session.execute(db.text("SELECT id FROM users WHERE username = :username"), {'username': dealer_code}).fetchone()
                if existing_user:
                    print(f"用户 {dealer_code} 已存在，跳过")
                    continue
                
                db.session.execute(db.text("""
                    INSERT INTO users (username, password_hash, role, status, created_at, updated_at)
                    VALUES (:username, :password, 'dealer', 1, NOW(), NOW())
                """), {'username': dealer_code, 'password': '123456'})
                
                user_result = db.session.execute(db.text("SELECT LAST_INSERT_ID()")).fetchone()
                user_id = user_result[0]
                
                region = f"{province}{city}" if province and city else (province or city or '')
                
                db.session.execute(db.text("""
                    INSERT INTO dealers (user_id, dealer_name, level, region, contact_name, contact_phone, address, created_at, updated_at)
                    VALUES (:user_id, :dealer_name, :level, :region, '', '', '', NOW(), NOW())
                """), {
                    'user_id': user_id,
                    'dealer_name': dealer_code,
                    'level': fed_level or '',
                    'region': region
                })
                
                added_count += 1
                print(f"已添加: {dealer_code}")
            
            db.session.commit()
            print(f"\n导入完成! 共添加 {added_count} 条经销商数据")
            
        except Exception as e:
            db.session.rollback()
            print(f"导入失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import_dealers()
