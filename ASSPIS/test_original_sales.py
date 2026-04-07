import requests

print("获取原始销量数据...")
r = requests.get('/sales/original?dealer_code=9210006&months=10')
if r.status_code == 200:
    data = r.json()
    print(f"9210006 原始销量: {data}")
    
r2 = requests.get('/sales/original?dealer_code=B440045&months=10')
if r2.status_code == 200:
    data2 = r2.json()
    print(f"\nB440045 原始销量: {data2}")
