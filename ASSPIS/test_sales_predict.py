import requests
import json

print("测试 /sales/predict API...")

params = {
    "dealer_code": "9210006",
    "dimension": "leads",
    "change_percentage": 10,
    "base_year": 2024,
    "base_month": 10,
    "month_for_radar": 10
}

r = requests.post('http://localhost:5001/sales/predict', json=params)
print(f"POST /sales/predict: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print("\n完整响应结构:")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    
    print("\n\n关键字段:")
    print(f"  status: {data.get('status')}")
    print(f"  mode: {data.get('mode')}")
    print(f"  dealer_code: {data.get('dealer_code')}")
    print(f"  dimension: {data.get('dimension')}")
    print(f"  change_percentage: {data.get('change_percentage')}")
    print(f"  base_year: {data.get('base_year')}")
    print(f"  base_month: {data.get('base_month')}")
    print(f"  target_year: {data.get('target_year')}")
    print(f"  target_month: {data.get('target_month')}")
    
    if data.get('sales_prediction'):
        print(f"\n  sales_prediction (first item):")
        first = data['sales_prediction'][0] if data['sales_prediction'] else None
        if first:
            for k, v in first.items():
                print(f"    {k}: {v}")
    
    if data.get('sales_changes'):
        print(f"\n  sales_changes (first item):")
        first = data['sales_changes'][0] if data['sales_changes'] else None
        if first:
            for k, v in first.items():
                print(f"    {k}: {v}")
else:
    print(f"Error: {r.text[:500]}")
