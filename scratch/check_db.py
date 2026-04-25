from unified_app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Check v_dealer_info
        res = db.session.execute(text("SELECT * FROM v_dealer_info LIMIT 1"))
        print("v_dealer_info columns:", res.keys())
        
        # Check if fed_level exists in MonthlyMetrics11d
        res2 = db.session.execute(text("SELECT * FROM monthly_metrics_11d LIMIT 1"))
        print("monthly_metrics_11d columns:", res2.keys())
        
        # Check MonthlyRadarScores
        res3 = db.session.execute(text("SELECT * FROM monthly_radar_scores LIMIT 1"))
        print("monthly_radar_scores columns:", res3.keys())
    except Exception as e:
        print("Error:", e)
