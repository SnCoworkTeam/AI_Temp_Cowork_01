#!/usr/bin/env python3
"""
简化的Neo4j数据导入脚本
直接在服务器上运行，使用环境变量配置
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from neo4j import AsyncGraphDatabase
    import asyncpg
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请安装: pip install neo4j asyncpg")
    sys.exit(1)

# 从环境变量读取配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://43.143.90.179:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Neo4j@2024')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'ai_platform')

async def import_data():
    """导入数据"""
    print("=" * 80)
    print("Neo4j数据导入")
    print("=" * 80)
    print(f"Neo4j: {NEO4J_URI}")
    print(f"PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("")
    
    # 连接PostgreSQL
    print("[1] 连接PostgreSQL...")
    try:
        pg_conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("✅ PostgreSQL连接成功")
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return
    
    # 连接Neo4j
    print("[2] 连接Neo4j...")
    try:
        neo4j_driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        await neo4j_driver.verify_connectivity()
        print("✅ Neo4j连接成功")
    except Exception as e:
        print(f"❌ Neo4j连接失败: {e}")
        await pg_conn.close()
        return
    
    # 导入知识图谱节点
    print("\n[3] 导入知识图谱节点...")
    try:
        nodes = await pg_conn.fetch("""
            SELECT id, label, node_type, properties, document_id, created_at, updated_at
            FROM knowledge_graph_nodes
        """)
        print(f"找到 {len(nodes)} 个节点")
        
        node_mapping = {}
        async with neo4j_driver.session() as session:
            for i, node in enumerate(nodes, 1):
                labels = [node['node_type']] if node['node_type'] else ['Entity']
                # 处理properties JSONB字段
                props_dict = {}
                if node['properties']:
                    if isinstance(node['properties'], dict):
                        props_dict = node['properties']
                    elif isinstance(node['properties'], str):
                        import json
                        try:
                            props_dict = json.loads(node['properties'])
                        except:
                            props_dict = {}
                
                properties = {
                    'uuid': str(node['id']),
                    'label': node['label'],
                    **props_dict
                }
                if node['document_id']:
                    properties['document_id'] = str(node['document_id'])
                
                result = await session.run(
                    f"CREATE (n:{':'.join(labels)}) SET n = $props RETURN id(n) AS node_id",
                    props=properties
                )
                record = await result.single()
                node_mapping[str(node['id'])] = record['node_id']
                
                if i % 100 == 0:
                    print(f"  已导入 {i}/{len(nodes)} 个节点")
        
        print(f"✅ 节点导入完成: {len(node_mapping)} 个")
    except Exception as e:
        print(f"❌ 节点导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 导入知识图谱边
    print("\n[4] 导入知识图谱边...")
    try:
        edges = await pg_conn.fetch("""
            SELECT id, source_node_id, target_node_id, relationship_type, weight, metadata
            FROM knowledge_graph_edges
        """)
        print(f"找到 {len(edges)} 个边")
        
        imported = 0
        async with neo4j_driver.session() as session:
            for i, edge in enumerate(edges, 1):
                source_id = node_mapping.get(str(edge['source_node_id']))
                target_id = node_mapping.get(str(edge['target_node_id']))
                
                if not source_id or not target_id:
                    continue
                
                # 处理metadata JSONB字段
                metadata_dict = {}
                if edge['metadata']:
                    if isinstance(edge['metadata'], dict):
                        metadata_dict = edge['metadata']
                    elif isinstance(edge['metadata'], str):
                        import json
                        try:
                            metadata_dict = json.loads(edge['metadata'])
                        except:
                            metadata_dict = {}
                
                properties = {
                    'uuid': str(edge['id']),
                    'weight': edge['weight'] or 1.0,
                    **metadata_dict
                }
                
                await session.run(
                    f"""
                    MATCH (a) WHERE id(a) = $source_id
                    MATCH (b) WHERE id(b) = $target_id
                    CREATE (a)-[r:{edge['relationship_type']}]->(b)
                    SET r = $props
                    """,
                    source_id=source_id,
                    target_id=target_id,
                    props=properties
                )
                imported += 1
                
                if i % 100 == 0:
                    print(f"  已导入 {i}/{len(edges)} 个边")
        
        print(f"✅ 边导入完成: {imported} 个")
    except Exception as e:
        print(f"❌ 边导入失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 创建索引
    print("\n[5] 创建索引...")
    try:
        async with neo4j_driver.session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.uuid)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.label)",
            ]
            for index_query in indexes:
                await session.run(index_query)
        print("✅ 索引创建完成")
    except Exception as e:
        print(f"⚠️  索引创建失败: {e}")
    
    # 验证
    print("\n[6] 验证导入结果...")
    try:
        async with neo4j_driver.session() as session:
            node_result = await session.run("MATCH (n) RETURN count(n) AS count")
            node_count = (await node_result.single())['count']
            
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = (await rel_result.single())['count']
            
            print(f"✅ Neo4j中: 节点={node_count}, 关系={rel_count}")
    except Exception as e:
        print(f"⚠️  验证失败: {e}")
    
    # 清理
    await pg_conn.close()
    await neo4j_driver.close()
    
    print("\n" + "=" * 80)
    print("导入完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(import_data())

