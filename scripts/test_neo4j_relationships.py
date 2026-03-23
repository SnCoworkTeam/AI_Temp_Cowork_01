"""
测试Neo4j关系查询
验证节点和关系是否正确返回
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.neo4j_client import Neo4jClient

async def test_relationships():
    """测试关系查询"""
    client = Neo4jClient()
    
    try:
        await client.connect()
        print("✅ Neo4j连接成功")
        
        # 测试1: 查询节点和ID
        print("\n测试1: 查询节点和ID...")
        node_query = "MATCH (n) RETURN id(n) AS node_id, labels(n) AS labels, n.label AS label LIMIT 10"
        node_results = await client.execute_query(node_query)
        print(f"找到 {len(node_results)} 个节点")
        
        node_ids = []
        for record in node_results:
            node_id = record.get("node_id")
            label = record.get("label", "N/A")
            labels = record.get("labels", [])
            node_ids.append(node_id)
            print(f"  节点ID: {node_id}, 标签: {labels}, 名称: {label}")
        
        if len(node_ids) == 0:
            print("❌ 没有找到节点")
            return
        
        # 测试2: 查询这些节点之间的关系
        print(f"\n测试2: 查询节点 {node_ids[:5]} 之间的关系...")
        node_ids_param = node_ids[:5]  # 只测试前5个节点
        
        rel_query = """
        MATCH (a)-[r]->(b)
        WHERE id(a) IN $node_ids AND id(b) IN $node_ids
        RETURN id(a) AS source, id(b) AS target, type(r) AS type
        LIMIT 20
        """
        
        rel_results = await client.execute_query(rel_query, {"node_ids": node_ids_param})
        print(f"找到 {len(rel_results)} 个关系")
        
        for record in rel_results:
            source = record.get("source")
            target = record.get("target")
            rel_type = record.get("type", "N/A")
            print(f"  关系: {source} --[{rel_type}]--> {target}")
        
        if len(rel_results) > 0:
            print("✅ 关系查询成功，关系数据存在")
        else:
            print("⚠️ 这些节点之间没有关系，尝试查询所有关系...")
            
            # 测试3: 查询所有关系
            print("\n测试3: 查询所有关系...")
            all_rel_query = """
            MATCH (a)-[r]->(b)
            RETURN id(a) AS source, id(b) AS target, type(r) AS type
            LIMIT 10
            """
            all_rel_results = await client.execute_query(all_rel_query)
            print(f"找到 {len(all_rel_results)} 个关系（前10个）")
            
            for record in all_rel_results:
                source = record.get("source")
                target = record.get("target")
                rel_type = record.get("type", "N/A")
                print(f"  关系: {source} --[{rel_type}]--> {target}")
        
        # 测试4: 统计关系数量
        print("\n测试4: 统计关系数量...")
        count_query = "MATCH ()-[r]->() RETURN count(r) AS total, type(r) AS type, count(*) AS count ORDER BY count DESC LIMIT 10"
        count_results = await client.execute_query(count_query)
        
        for record in count_results:
            rel_type = record.get("type", "N/A")
            count = record.get("count", 0)
            print(f"  关系类型 {rel_type}: {count} 个")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_relationships())



