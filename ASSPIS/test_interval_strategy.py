import requests
import json

print("测试不同区间策略的返回结构...")

# 80% 区间策略
params_80 = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": [1, 2, 3],
    "quantiles": [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
    "calib_alpha": 0.2,
    "scenarios": [{"name": "baseline"}]
}

print("\n=== 80% 区间策略 (calib_alpha=0.2) ===")
r = requests.post('http://localhost:5001/forecast/quantiles', json=params_80)
if r.status_code == 200:
    data = r.json()
    for name, scenario in data.get('scenarios', {}).items():
        print(f"  Scenario: {name}")
        print(f"    months: {scenario.get('months')}")
        print(f"    point: {scenario.get('point')}")
        print(f"    meta.cqr_alpha: {scenario.get('meta', {}).get('cqr_alpha')}")
        print(f"    meta.interval_name: {scenario.get('meta', {}).get('interval_name')}")
        if scenario.get('calibrated_interval_80'):
            print(f"    calibrated_interval_80.lower: {scenario['calibrated_interval_80'].get('lower')}")
            print(f"    calibrated_interval_80.upper: {scenario['calibrated_interval_80'].get('upper')}")
else:
    print(f"  Error: {r.status_code} - {r.text}")

# 90% 区间策略
params_90 = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": [1, 2, 3],
    "quantiles": [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
    "calib_alpha": 0.1,
    "scenarios": [{"name": "baseline"}]
}

print("\n\n=== 90% 区间策略 (calib_alpha=0.1) ===")
r2 = requests.post('http://localhost:5001/forecast/quantiles', json=params_90)
if r2.status_code == 200:
    data2 = r2.json()
    for name, scenario in data2.get('scenarios', {}).items():
        print(f"  Scenario: {name}")
        print(f"    months: {scenario.get('months')}")
        print(f"    point: {scenario.get('point')}")
        print(f"    meta.cqr_alpha: {scenario.get('meta', {}).get('cqr_alpha')}")
        print(f"    meta.interval_name: {scenario.get('meta', {}).get('interval_name')}")
        if scenario.get('calibrated_interval_90'):
            print(f"    calibrated_interval_90.lower: {scenario['calibrated_interval_90'].get('lower')}")
            print(f"    calibrated_interval_90.upper: {scenario['calibrated_interval_90'].get('upper')}")
else:
    print(f"  Error: {r2.status_code} - {r2.text}")
