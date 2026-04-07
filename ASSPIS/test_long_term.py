import requests
import json

print("测试长期预测 (h=1-12)...")

params = {
    "dealer_code": "9210006",
    "base_year": 2024,
    "base_month": 10,
    "horizons": list(range(1, 13)),
    "quantiles": [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
    "calib_alpha": 0.2,
    "scenarios": [{"name": "baseline"}]
}

r = requests.post('/forecast/quantiles', json=params)
if r.status_code == 200:
    data = r.json()
    for name, scenario in data.get('scenarios', {}).items():
        print(f"Scenario: {name}")
        print(f"  horizons_requested: {scenario.get('horizons_requested')}")
        print(f"  horizons_supported: {scenario.get('horizons_supported')}")
        print(f"  unsupported_horizons: {scenario.get('unsupported_horizons')}")
        print(f"  years: {scenario.get('years')}")
        print(f"  months: {scenario.get('months')}")
        print(f"  point: {scenario.get('point')}")
else:
    print(f"Error: {r.status_code} - {r.text}")
