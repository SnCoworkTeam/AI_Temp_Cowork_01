#!/usr/bin/env python3
"""
仅迁移Neo4j关系（节点已迁移完成）
"""
import asyncio
import os
from neo4j import AsyncGraphDatabase

# 本地Neo4j配置
LOCAL_NEO4J_URI = os.getenv('LOCAL_NEO4J_URI', 'bolt://localhost:7687')
LOCAL_NEO4J_USER = os.getenv('LOCAL_NEO4J_USER', 'neo4j')
LOCAL_NEO4J_PASSWORD = os.getenv('LOCAL_NEO4J_PASSWORD', 'neo4j_password')

# 远程Neo4j配置
REMOTE_NEO4J_URI = os.getenv('REMOTE_NEO4J_URI', 'bolt://43.143.90.179:7687')
REMOTE_NEO4J_USER = os.getenv('REMOTE_NEO4J_USER', 'neo4j')
REMOTE_NEO4J_PASSWORD = os.getenv('REMOTE_NEO4J_PASSWORD', 'Neo4j@2024')

async def migrate_relationships():
    """迁移关系"""
    print("=" * 80)
    print("Neo4j关系迁移：本地 -> 远程")
    print("=" * 80)
    print(f"本地: {LOCAL_NEO4J_URI}")
    print(f"远程: {REMOTE_NEO4J_URI}")
    print("")
    
    # 连接本地Neo4j
    print("[1] 连接本地Neo4j...")
    try:
        local_driver = AsyncGraphDatabase.driver(
            LOCAL_NEO4J_URI,
            auth=(LOCAL_NEO4J_USER, LOCAL_NEO4J_PASSWORD)
        )
        await local_driver.verify_connectivity()
        print("[OK] 本地Neo4j连接成功")
    except Exception as e:
        print(f"[ERROR] 本地Neo4j连接失败: {e}")
        return
    
    # 连接远程Neo4j
    print("[2] 连接远程Neo4j...")
    try:
        remote_driver = AsyncGraphDatabase.driver(
            REMOTE_NEO4J_URI,
            auth=(REMOTE_NEO4J_USER, REMOTE_NEO4J_PASSWORD)
        )
        await remote_driver.verify_connectivity()
        print("[OK] 远程Neo4j连接成功")
    except Exception as e:
        print(f"[ERROR] 远程Neo4j连接失败: {e}")
        await local_driver.close()
        return
    
    # 检查数据
    print("\n[3] 检查数据...")
    try:
        async with local_driver.session() as session:
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            local_rel_count = (await rel_result.single())['count']
            print(f"[OK] 本地关系数量: {local_rel_count}")
        
        async with remote_driver.session() as session:
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            remote_rel_count = (await rel_result.single())['count']
            print(f"[OK] 远程关系数量: {remote_rel_count}")
    except Exception as e:
        print(f"[ERROR] 检查数据失败: {e}")
        await local_driver.close()
        await remote_driver.close()
        return
    
    # 建立ID映射（通过UUID）- 使用批量查询
    print("\n[4] 建立ID映射...")
    id_mapping = {}
    try:
        batch_size = 500
        offset = 0
        
        while True:
            async with local_driver.session() as local_session:
                # 批量获取本地节点的ID和UUID
                result = await local_session.run("""
                    MATCH (n)
                    RETURN id(n) AS local_id, n.uuid AS uuid
                    SKIP $offset LIMIT $limit
                """, offset=offset, limit=batch_size)
                
                nodes = await result.values()
                if not nodes:
                    break
                
                # 批量查询远程节点
                async with remote_driver.session() as remote_session:
                    for local_id, uuid in nodes:
                        if uuid:
                            try:
                                # 通过UUID查找远程节点
                                remote_result = await remote_session.run(
                                    "MATCH (n {uuid: $uuid}) RETURN id(n) AS remote_id",
                                    uuid=uuid
                                )
                                remote_record = await remote_result.single()
                                if remote_record:
                                    id_mapping[local_id] = remote_record['remote_id']
                            except Exception as e:
                                pass  # 忽略单个节点查询失败
            
            offset += batch_size
            print(f"  已处理 {min(offset, 3651)}/3651 个节点，映射 {len(id_mapping)} 个", end='\r')
        
        print(f"\n[OK] ID映射建立完成: {len(id_mapping)} 个")
    except Exception as e:
        print(f"[ERROR] ID映射建立失败: {e}")
        import traceback
        traceback.print_exc()
        await local_driver.close()
        await remote_driver.close()
        return
    
    # 迁移关系
    print("\n[5] 迁移关系...")
    try:
        batch_size = 100
        offset = 0
        total_imported = 0
        failed = 0
        
        async with local_driver.session() as local_session:
            while True:
                result = await local_session.run("""
                    MATCH (a)-[r]->(b)
                    RETURN id(a) AS source_id, id(b) AS target_id, 
                           type(r) AS rel_type, properties(r) AS props
                    SKIP $offset LIMIT $limit
                """, offset=offset, limit=batch_size)
                
                rels = await result.values()
                if not rels:
                    break
                
                async with remote_driver.session() as remote_session:
                    for rel_data in rels:
                        source_id, target_id, rel_type, props = rel_data
                        
                        # 查找远程节点ID
                        remote_source_id = id_mapping.get(source_id)
                        remote_target_id = id_mapping.get(target_id)
                        
                        if remote_source_id and remote_target_id:
                            try:
                                # 转义关系类型（如果有特殊字符）
                                rel_type_escaped = rel_type.replace(':', '_')
                                
                                await remote_session.run(f"""
                                    MATCH (a) WHERE id(a) = $source_id
                                    MATCH (b) WHERE id(b) = $target_id
                                    CREATE (a)-[r:{rel_type}]->(b)
                                    SET r = $props
                                """, source_id=remote_source_id, target_id=remote_target_id,
                                    props=props or {})
                                total_imported += 1
                            except Exception as e:
                                failed += 1
                                if failed <= 5:  # 只打印前5个错误
                                    print(f"\n[WARN] 关系迁移失败: {e}")
                        else:
                            failed += 1
                            if not remote_source_id:
                                print(f"\n[WARN] 源节点ID {source_id} 未找到映射")
                            if not remote_target_id:
                                print(f"\n[WARN] 目标节点ID {target_id} 未找到映射")
                
                offset += batch_size
                print(f"  已迁移 {total_imported}/{local_rel_count} 个关系 (失败: {failed})", end='\r')
        
        print(f"\n[OK] 关系迁移完成: {total_imported} 个 (失败: {failed})")
    except Exception as e:
        print(f"\n[ERROR] 关系迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 验证
    print("\n[6] 验证迁移结果...")
    try:
        async with remote_driver.session() as session:
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            remote_rel_count = (await rel_result.single())['count']
            
            print(f"[OK] 远程关系数量: {remote_rel_count}")
            
            if remote_rel_count == local_rel_count:
                print("[OK] 关系数量匹配！")
            else:
                print(f"[WARN] 关系数量不匹配: 本地={local_rel_count}, 远程={remote_rel_count}")
    except Exception as e:
        print(f"[WARN] 验证失败: {e}")
    
    # 清理
    await local_driver.close()
    await remote_driver.close()
    
    print("\n" + "=" * 80)
    print("迁移完成！")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(migrate_relationships())

