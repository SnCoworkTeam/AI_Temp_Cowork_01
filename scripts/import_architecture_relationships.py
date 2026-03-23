#!/usr/bin/env python3
"""
从PostgreSQL导入企业架构关系到Neo4j
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
    print(f"[ERROR] 缺少依赖: {e}")
    print("请安装: pip install neo4j asyncpg")
    sys.exit(1)

# 从环境变量读取配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://43.143.90.179:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Neo4j@2024')

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'ai_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ai_password')
DB_NAME = os.getenv('DB_NAME', 'ai_platform')

async def import_architecture_relationships():
    """导入企业架构关系"""
    print("=" * 80)
    print("导入企业架构关系到Neo4j")
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
        print("[OK] PostgreSQL连接成功")
    except Exception as e:
        print(f"[ERROR] PostgreSQL连接失败: {e}")
        return
    
    # 连接Neo4j
    print("[2] 连接Neo4j...")
    try:
        neo4j_driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        await neo4j_driver.verify_connectivity()
        print("[OK] Neo4j连接成功")
    except Exception as e:
        print(f"[ERROR] Neo4j连接失败: {e}")
        await pg_conn.close()
        return
    
    # 检查架构关系表
    print("\n[3] 检查架构关系数据...")
    try:
        count = await pg_conn.fetchval("SELECT COUNT(*) FROM architecture_relationships")
        print(f"[OK] 找到 {count} 个架构关系")
        
        if count == 0:
            print("[WARN] 没有架构关系数据，退出")
            await pg_conn.close()
            await neo4j_driver.close()
            return
    except Exception as e:
        print(f"[ERROR] 检查架构关系失败: {e}")
        await pg_conn.close()
        await neo4j_driver.close()
        return
    
    # 获取架构关系数据
    print("\n[4] 读取架构关系数据...")
    try:
        relationships = await pg_conn.fetch("""
            SELECT 
                id,
                source_type,
                source_id,
                target_type,
                target_id,
                relationship_type,
                properties,
                created_at
            FROM architecture_relationships
        """)
        print(f"[OK] 读取到 {len(relationships)} 个关系")
    except Exception as e:
        print(f"[ERROR] 读取架构关系失败: {e}")
        import traceback
        traceback.print_exc()
        await pg_conn.close()
        await neo4j_driver.close()
        return
    
    # 导入关系
    print("\n[5] 导入架构关系到Neo4j...")
    imported = 0
    failed = 0
    
    async with neo4j_driver.session() as session:
        for i, rel in enumerate(relationships, 1):
            try:
                source_type = rel['source_type']
                source_id = str(rel['source_id'])
                target_type = rel['target_type']
                target_id = str(rel['target_id'])
                rel_type = rel['relationship_type'] or 'RELATES_TO'
                
                # 处理properties JSONB字段
                props = {}
                if rel['properties']:
                    if isinstance(rel['properties'], dict):
                        props = rel['properties']
                    elif isinstance(rel['properties'], str):
                        import json
                        try:
                            props = json.loads(rel['properties'])
                        except:
                            props = {}
                
                # 添加元数据
                props['uuid'] = str(rel['id'])
                if rel['created_at']:
                    props['created_at'] = rel['created_at'].isoformat()
                
                # 转换节点类型（PostgreSQL使用小写，Neo4j使用PascalCase）
                type_mapping = {
                    'application_system': 'ApplicationSystem',
                    'business_process': 'BusinessProcess',
                    'data_entity': 'DataEntity',
                    'technology_component': 'TechnologyComponent',
                    'business_capability': 'BusinessCapability',
                    'application_service': 'ApplicationService'
                }
                neo4j_source_type = type_mapping.get(source_type.lower(), source_type)
                neo4j_target_type = type_mapping.get(target_type.lower(), target_type)
                
                # 创建关系
                # 通过UUID查找源节点和目标节点
                query = f"""
                MATCH (source:{neo4j_source_type} {{uuid: $source_id}})
                MATCH (target:{neo4j_target_type} {{uuid: $target_id}})
                CREATE (source)-[r:{rel_type}]->(target)
                SET r = $props
                RETURN r
                """
                
                result = await session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    props=props
                )
                record = await result.single()
                
                if record:
                    imported += 1
                else:
                    failed += 1
                    if failed <= 10:  # 只打印前10个错误
                        print(f"[WARN] 关系创建失败: {source_type}({source_id}) -> {target_type}({target_id})")
                
                if i % 50 == 0:
                    print(f"  已处理 {i}/{len(relationships)} 个关系 (成功: {imported}, 失败: {failed})", end='\r')
                    
            except Exception as e:
                failed += 1
                if failed <= 10:
                    print(f"\n[WARN] 处理关系失败: {e}")
    
    print(f"\n[OK] 关系导入完成: 成功 {imported} 个, 失败 {failed} 个")
    
    # 验证
    print("\n[6] 验证导入结果...")
    try:
        async with neo4j_driver.session() as session:
            # 检查ApplicationSystem和BusinessProcess之间的关系
            result = await session.run("""
                MATCH (a:ApplicationSystem)-[r]->(b:BusinessProcess)
                RETURN count(r) AS count
            """)
            count = (await result.single())['count']
            print(f"[OK] ApplicationSystem -> BusinessProcess 关系: {count} 个")
            
            # 检查所有架构关系
            result = await session.run("""
                MATCH ()-[r]->()
                WHERE r.uuid IS NOT NULL
                RETURN count(r) AS count
            """)
            total = (await result.single())['count']
            print(f"[OK] 总架构关系数: {total} 个")
    except Exception as e:
        print(f"[WARN] 验证失败: {e}")
    
    # 清理
    await pg_conn.close()
    await neo4j_driver.close()
    
    print("\n" + "=" * 80)
    print("导入完成！")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(import_architecture_relationships())

