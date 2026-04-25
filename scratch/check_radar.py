from unified_app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        res = db.session.execute(text("SELECT stat_month, count(*) FROM monthly_radar_scores WHERE stat_year=2024 GROUP BY stat_month")).fetchall()
        print("Radar scores months:", res)
        
        res2 = db.session.execute(text("SELECT fed_level, count(*) FROM v_dealer_info GROUP BY fed_level")).fetchall()
        print("Fed levels:", res2)
    except Exception as e:
        print("Error:", e)
