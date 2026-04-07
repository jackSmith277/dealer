import sys
sys.path.append('d:\\dealer\\dealer\\backend')

from app import app, db

def migrate_database():
    with app.app_context():
        try:
            print('开始迁移数据库...')
            
            db.session.execute(db.text('''
                ALTER TABLE prediction_history 
                DROP COLUMN month_for_radar,
                DROP COLUMN propagation_force,
                DROP COLUMN experience_force,
                DROP COLUMN conversion_force,
                DROP COLUMN service_force,
                DROP COLUMN operation_force,
                DROP COLUMN comprehensive_score
            '''))
            db.session.commit()
            print('数据库迁移完成!')
            
        except Exception as e:
            print(f'迁移失败: {str(e)}')
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_database()
