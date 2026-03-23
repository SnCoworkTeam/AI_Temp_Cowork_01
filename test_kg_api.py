"""
测试知识图谱API返回的数据
"""
import requests

API_URL = "http://43.143.139.197:8080/api/knowledge-graph/graph"

print("=" * 60)
print("测试知识图谱API")
print("=" * 60)

# 测试不同的limit值
for limit in [100, 500, 1000]:
    try:
        response = requests.get(f"{API_URL}?limit={limit}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        print(f"\nlimit={limit}:")
        print(f"  节点数: {len(nodes)}")
        print(f"  边数: {len(links)}")
        
        if len(nodes) > 0:
            print(f"  节点示例: {nodes[0].get('name', 'N/A')} ({nodes[0].get('type', 'N/A')})")
        
        if len(links) > 0:
            print(f"  边示例: {links[0].get('source', 'N/A')} -> {links[0].get('target', 'N/A')} ({links[0].get('type', 'N/A')})")
        
    except Exception as e:
        print(f"\nlimit={limit}: 错误 - {e}")

print("\n" + "=" * 60)



