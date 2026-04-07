import requests
import json

print("测试 /forecast/quantiles API...")

params = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": [1, 2, 3],
    "quantiles": [0.1, 0.5, 0.9],
    "scenarios": [
        {"name": "baseline"},
        {"name": "leads+10%", "dimension": "leads", "change_percentage": 10}
    ]
}

r = requests.post('http://localhost:5001/forecast/quantiles', json=params)
print(f"POST /forecast/quantiles: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print("\n响应结构:")
    print(f"  dealer_code: {data.get('dealer_code')}")
    print(f"  base_year: {data.get('base_year')}")
    print(f"  base_month: {data.get('base_month')}")
    print(f"  scenarios keys: {list(data.get('scenarios', {}).keys())}")
    
    for scenario_name, scenario_data in data.get('scenarios', {}).items():
        print(f"\n  Scenario: {scenario_name}")
        print(f"    horizons: {scenario_data.get('horizons_requested')}")
        print(f"    months: {scenario_data.get('months')}")
        print(f"    point (first 3): {scenario_data.get('point', [])[:3]}")
        print(f"    quantiles keys: {list(scenario_data.get('quantiles', {}).keys())}")
else:
    print(f"Error: {r.text[:500]}")
