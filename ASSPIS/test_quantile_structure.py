import requests
import json

print("测试不同预测长度的返回结构...")

# 短期预测 (1-3月)
params_short = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": [1, 2, 3],
    "quantiles": [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
    "scenarios": [
        {"name": "baseline"},
        {"name": "leads+10%", "dimension": "leads", "change_percentage": 10}
    ]
}

print("\n=== 短期预测 (h=1,2,3) ===")
r = requests.post('http://localhost:5001/forecast/quantiles', json=params_short)
if r.status_code == 200:
    data = r.json()
    print(f"scenarios keys: {list(data.get('scenarios', {}).keys())}")
    for name, scenario in data.get('scenarios', {}).items():
        print(f"\n  Scenario: {name}")
        print(f"    horizons: {scenario.get('horizons_requested')}")
        print(f"    months: {scenario.get('months')}")
        print(f"    point: {scenario.get('point')}")
        print(f"    quantiles keys: {list(scenario.get('quantiles', {}).keys())}")
        if scenario.get('calibrated_interval_80'):
            print(f"    calibrated_interval_80.lower: {scenario['calibrated_interval_80'].get('lower')}")
            print(f"    calibrated_interval_80.upper: {scenario['calibrated_interval_80'].get('upper')}")
        if scenario.get('calibrated_interval_90'):
            print(f"    calibrated_interval_90: {scenario['calibrated_interval_90']}")

# 中期预测 (1-6月)
params_mid = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": [1, 2, 3, 4, 5, 6],
    "quantiles": [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
    "scenarios": [{"name": "baseline"}]
}

print("\n\n=== 中期预测 (h=1-6) ===")
r2 = requests.post('http://localhost:5001/forecast/quantiles', json=params_mid)
if r2.status_code == 200:
    data2 = r2.json()
    for name, scenario in data2.get('scenarios', {}).items():
        print(f"  Scenario: {name}")
        print(f"    horizons: {scenario.get('horizons_requested')}")
        print(f"    months: {scenario.get('months')}")
        print(f"    point: {scenario.get('point')}")
        print(f"    quantiles keys: {list(scenario.get('quantiles', {}).keys())}")
        if scenario.get('calibrated_interval_80'):
            print(f"    calibrated_interval_80 exists")
        if scenario.get('calibrated_interval_90'):
            print(f"    calibrated_interval_90 exists")
