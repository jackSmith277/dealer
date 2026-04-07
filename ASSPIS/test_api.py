import requests

print("测试 ASSPIS API...")

r = requests.get('http://localhost:5001/sales/original', params={'dealer_code': '9210006', 'months': 3})
print(f"GET /sales/original: {r.status_code}")
print(r.text[:500] if r.text else "No content")

print("\n测试 /sales/predict...")
r2 = requests.post('http://localhost:5001/sales/predict', json={
    'dealer_code': '9210006',
    'dimension': 'leads',
    'change_percentage': 10,
    'month': 11,
    'month_for_radar': 10
})
print(f"POST /sales/predict: {r2.status_code}")
print(r2.text[:500] if r2.text else "No content")
