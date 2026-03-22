import requests

user_id = "default_user"
url = f"http://localhost:8000/api/v4/knowledge-graph/{user_id}/export"

r = requests.get(url)
d = r.json()

info = d.get("data", {}).get("information", [])
rels = d.get("data", {}).get("relationships", [])

print(f"API返回节点数: {len(info)}")
print(f"API返回关系数: {len(rels)}")

if info:
    print("\n前5个节点:")
    for n in info[:5]:
        print(f"  - {n.get('name')} ({n.get('category', n.get('type'))})")
