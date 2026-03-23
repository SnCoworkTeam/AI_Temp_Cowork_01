"""
测试Neo4j API是否正确返回关系数据
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.neo4j_client import Neo4jClient

async def test_api():
    """测试API逻辑"""
    client = Neo4jClient()
    
    try:
        await client.connect()
        
        # 模拟API的查询逻辑
        limit = 100
        
        # 第一步：查询关系
        rel_query = f"""
        MATCH (a)-[r]->(b)
        RETURN id(a) AS source, id(b) AS target, type(r) AS type, r AS rel
        LIMIT {limit * 2}
        """
        
        rel_results = await client.execute_query(rel_query)
        
        # 收集所有涉及到的节点ID
        all_node_ids = set()
        links = []
        seen_links = set()
        
        for record in rel_results:
            source_id = record.get("source")
            target_id = record.get("target")
            rel_type = record.get("type", "")
            
            if source_id is not None and target_id is not None:
                all_node_ids.add(source_id)
                all_node_ids.add(target_id)
                
                source_id_str = str(source_id)
                target_id_str = str(target_id)
                link_key = f"{source_id_str}-{target_id_str}-{rel_type}"
                
                if link_key not in seen_links:
                    seen_links.add(link_key)
                    
                    rel_data = record.get("rel", {})
                    if hasattr(rel_data, 'items'):
                        rel_properties = dict(rel_data)
                    elif isinstance(rel_data, dict):
                        rel_properties = rel_data
                    else:
                        rel_properties = {}
                    
                    links.append({
                        "id": link_key,
                        "source": source_id_str,
                        "target": target_id_str,
                        "type": rel_type,
                        "properties": rel_properties
                    })
        
        # 第二步：根据节点ID查询节点数据
        node_ids_list = list(all_node_ids)[:limit]
        
        nodes = []
        node_id_map = {}
        
        if len(node_ids_list) > 0:
            node_query = """
            MATCH (n)
            WHERE id(n) IN $node_ids
            RETURN id(n) AS node_id, labels(n) AS labels, n
            """
            
            node_results = await client.execute_query(node_query, {"node_ids": node_ids_list})
            
            for record in node_results:
                node_id = record.get("node_id")
                if node_id is None:
                    continue
                
                node_id_str = str(node_id)
                node_data = record.get("n", {})
                labels = record.get("labels", [])
                
                if hasattr(node_data, 'items'):
                    properties = dict(node_data)
                elif isinstance(node_data, dict):
                    properties = node_data
                else:
                    properties = {}
                
                node_info = {
                    "id": node_id_str,
                    "label": properties.get("label") or properties.get("name") or node_id_str,
                    "type": labels[0] if labels else "Entity",
                    "properties": properties
                }
                
                nodes.append(node_info)
                node_id_map[node_id] = node_info
        
        # 过滤关系
        filtered_links = []
        for link in links:
            source_id = int(link["source"]) if link["source"].isdigit() else None
            target_id = int(link["target"]) if link["target"].isdigit() else None
            
            if source_id in node_id_map and target_id in node_id_map:
                filtered_links.append(link)
        
        result = {
            "nodes": nodes,
            "links": filtered_links
        }
        
        print("=" * 60)
        print("Neo4j API测试结果")
        print("=" * 60)
        print(f"\n节点数量: {len(result.get('nodes', []))}")
        print(f"关系数量: {len(result.get('links', []))}")
        
        if len(result.get('nodes', [])) > 0:
            print("\n前5个节点:")
            for i, node in enumerate(result['nodes'][:5], 1):
                print(f"  {i}. ID: {node['id']}, 标签: {node.get('type', 'N/A')}, 名称: {node.get('label', 'N/A')}")
        
        if len(result.get('links', [])) > 0:
            print("\n前10个关系:")
            for i, link in enumerate(result['links'][:10], 1):
                print(f"  {i}. {link['source']} --[{link.get('type', 'N/A')}]--> {link['target']}")
        else:
            print("\n⚠️ 没有找到关系！")
        
        # 验证关系是否匹配节点
        if result.get('links'):
            node_ids = {node['id'] for node in result.get('nodes', [])}
            links = result.get('links', [])
            
            matched = 0
            unmatched = 0
            
            for link in links:
                source = link.get('source')
                target = link.get('target')
                
                if source in node_ids and target in node_ids:
                    matched += 1
                else:
                    unmatched += 1
                    if unmatched <= 5:
                        print(f"  ⚠️ 不匹配的关系: {source} -> {target} (节点不在列表中)")
            
            print(f"\n关系匹配情况:")
            print(f"  匹配: {matched}")
            print(f"  不匹配: {unmatched}")
            
            if matched > 0:
                print("✅ 关系数据正确，节点之间有连线！")
            else:
                print("❌ 关系数据有问题，节点之间没有连线")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())

