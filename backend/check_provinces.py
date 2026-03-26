from app import app, db
from sqlalchemy import text

with app.app_context():
    result = db.session.execute(text("SELECT DISTINCT province FROM v_dealer_info WHERE province IS NOT NULL AND province != ''"))
    provinces = [r[0] for r in result]
    print("Provinces:", provinces)
