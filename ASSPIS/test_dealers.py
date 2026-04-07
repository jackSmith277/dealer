import requests

print("获取经销商列表...")
r = requests.get('/dealers')
if r.status_code == 200:
    data = r.json()
    dealers = data.get('dealers', [])
    print(f"共有 {len(dealers)} 个经销商")
    print(f"\n前10个: {dealers[:10]}")
