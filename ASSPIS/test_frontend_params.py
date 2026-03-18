import requests
import json

print("测试前端默认经销商 B440045...")

params = {
    "dealer_code": "B440045",
    "dimension": "customer_flow",
    "change_percentage": 40,
    "base_year": 2024,
    "base_month": 10,
    "month_for_radar": 10
}

r = requests.post('http://localhost:5001/sales/predict', json=params)
print(f"POST /sales/predict: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"\n预测结果:")
    print(f"  dealer_code: {data.get('dealer_code')}")
    print(f"  target_year: {data.get('target_year')}")
    print(f"  target_month: {data.get('target_month')}")
    
    if data.get('point_result'):
        pr = data['point_result']
        print(f"\n  point_result:")
        print(f"    baseline: {pr.get('baseline')}")
        print(f"    scenario: {pr.get('scenario')}")
        print(f"    delta: {pr.get('delta')}")
        print(f"    delta_pct: {pr.get('delta_pct')}")
    
    if data.get('original_sales'):
        print(f"\n  original_sales: {data.get('original_sales')}")
        
    if data.get('message'):
        print(f"\n  message: {data.get('message')}")
else:
    print(f"Error: {r.text[:500]}")
