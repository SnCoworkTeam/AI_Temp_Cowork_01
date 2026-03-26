"""
测试知识图谱数据
"""
import requests
import json

API_URL = "http://43.143.139.197:8080/api/knowledge-graph/graph?limit=20"

try:
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    nodes = data.get("nodes", [])
    links = data.get("links", [])
    
    print("=" * 60)
    print("知识图谱数据检查")
    print("=" * 60)
    print(f"\n节点数量: {len(nodes)}")
    print(f"边数量: {len(links)}")
    
    if nodes:
        print(f"\n节点ID示例（前3个）:")
        for i, node in enumerate(nodes[:3]):
            print(f"  {i+1}. ID: {node.get('id')} (type: {type(node.get('id')).__name__})")
            print(f"     名称: {node.get('name')}")
            print(f"     类型: {node.get('type')} ({node.get('type_cn')})")
    
    if links:
        print(f"\n边示例（前3个）:")
        for i, link in enumerate(links[:3]):
            print(f"  {i+1}. Source: {link.get('source')} (type: {type(link.get('source')).__name__})")
            print(f"     Target: {link.get('target')} (type: {type(link.get('target')).__name__})")
            print(f"     关系: {link.get('type')}")
    
    # 检查ID匹配
    node_ids = {str(node["id"]) for node in nodes}
    print(f"\n节点ID集合大小: {len(node_ids)}")
    print(f"节点ID示例: {list(node_ids)[:3]}")
    
    if links:
        invalid_links = []
        for link in links:
            source = str(link.get("source", ""))
            target = str(link.get("target", ""))
            if source not in node_ids:
                invalid_links.append(("source", source, link))
            if target not in node_ids:
                invalid_links.append(("target", target, link))
        
        if invalid_links:
            print(f"\n⚠️  发现 {len(invalid_links)} 个无效的边:")
            for issue_type, missing_id, link in invalid_links[:5]:
                print(f"  - {issue_type} ID {missing_id} 不在节点列表中")
                print(f"    边: {link.get('source')} -> {link.get('target')}")
        else:
            print(f"\n✅ 所有边的source和target都在节点列表中")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()



