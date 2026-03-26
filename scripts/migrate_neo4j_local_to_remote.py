#!/usr/bin/env python3
"""
将本地Docker中的Neo4j数据迁移到远程Neo4j服务器
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

async def migrate_data():
    """迁移数据"""
    print("=" * 80)
    print("Neo4j数据迁移：本地 -> 远程")
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
    
    # 检查本地数据
    print("\n[3] 检查本地数据...")
    try:
        async with local_driver.session() as session:
            node_result = await session.run("MATCH (n) RETURN count(n) AS count")
            node_count = (await node_result.single())['count']
            
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = (await rel_result.single())['count']
            
            print(f"[OK] 本地: 节点={node_count}, 关系={rel_count}")
    except Exception as e:
        print(f"[ERROR] 检查本地数据失败: {e}")
        await local_driver.close()
        await remote_driver.close()
        return
    
    # 清空远程数据库（可选）
    print("\n[4] 清空远程数据库...")
    try:
        async with remote_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        print("[OK] 远程数据库已清空")
    except Exception as e:
        print(f"[WARN] 清空远程数据库失败: {e}")
    
    # 导出并导入节点
    print("\n[5] 迁移节点...")
    try:
        batch_size = 100
        offset = 0
        total_imported = 0
        
        async with local_driver.session() as local_session:
            while True:
                # 获取一批节点
                result = await local_session.run("""
                    MATCH (n)
                    RETURN n, labels(n) AS labels, id(n) AS internal_id
                    SKIP $offset LIMIT $limit
                """, offset=offset, limit=batch_size)
                
                nodes = await result.values()
                if not nodes:
                    break
                
                # 导入到远程
                async with remote_driver.session() as remote_session:
                    for node_data in nodes:
                        node, labels, internal_id = node_data
                        label_str = ':'.join(labels) if labels else 'Entity'
                        
                        # 提取属性
                        props = dict(node)
                        props['_local_id'] = internal_id  # 临时存储本地ID
                        
                        await remote_session.run(
                            f"CREATE (n:{label_str}) SET n = $props",
                            props=props
                        )
                
                total_imported += len(nodes)
                offset += batch_size
                print(f"  已迁移 {total_imported}/{node_count} 个节点", end='\r')
        
        print(f"\n[OK] 节点迁移完成: {total_imported} 个")
    except Exception as e:
        print(f"\n[ERROR] 节点迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 迁移关系（需要先建立ID映射）
    print("\n[6] 建立ID映射...")
    try:
        id_mapping = {}
        async with local_driver.session() as local_session:
            async with remote_driver.session() as remote_session:
                # 获取所有节点的UUID或唯一标识
                result = await local_session.run("""
                    MATCH (n)
                    RETURN id(n) AS local_id, n.uuid AS uuid, n.label AS label
                    LIMIT 10000
                """)
                
                async for record in result:
                    local_id = record['local_id']
                    uuid = record['uuid']
                    label = record['label']
                    
                    if uuid:
                        # 通过UUID查找远程节点
                        remote_result = await remote_session.run(
                            "MATCH (n {uuid: $uuid}) RETURN id(n) AS remote_id",
                            uuid=uuid
                        )
                        remote_record = await remote_result.single()
                        if remote_record:
                            id_mapping[local_id] = remote_record['remote_id']
        
        print(f"[OK] ID映射建立完成: {len(id_mapping)} 个")
    except Exception as e:
        print(f"[ERROR] ID映射建立失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 迁移关系
    print("\n[7] 迁移关系...")
    try:
        batch_size = 100
        offset = 0
        total_imported = 0
        
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
                            await remote_session.run("""
                                MATCH (a) WHERE id(a) = $source_id
                                MATCH (b) WHERE id(b) = $target_id
                                CREATE (a)-[r:$rel_type]->(b)
                                SET r = $props
                            """, source_id=remote_source_id, target_id=remote_target_id,
                                rel_type=rel_type, props=props or {})
                            total_imported += 1
                
                offset += batch_size
                print(f"  已迁移 {total_imported} 个关系", end='\r')
        
        print(f"\n[OK] 关系迁移完成: {total_imported} 个")
    except Exception as e:
        print(f"\n[ERROR] 关系迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理临时属性
    print("\n[8] 清理临时属性...")
    try:
        async with remote_driver.session() as session:
            await session.run("MATCH (n) REMOVE n._local_id")
        print("[OK] 清理完成")
    except Exception as e:
        print(f"[WARN] 清理失败: {e}")
    
    # 验证
    print("\n[9] 验证迁移结果...")
    try:
        async with remote_driver.session() as session:
            node_result = await session.run("MATCH (n) RETURN count(n) AS count")
            remote_node_count = (await node_result.single())['count']
            
            rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            remote_rel_count = (await rel_result.single())['count']
            
            print(f"[OK] 远程: 节点={remote_node_count}, 关系={remote_rel_count}")
            
            if remote_node_count == node_count:
                print("[OK] 节点数量匹配！")
            else:
                print(f"[WARN] 节点数量不匹配: 本地={node_count}, 远程={remote_node_count}")
    except Exception as e:
        print(f"[WARN] 验证失败: {e}")
    
    # 清理
    await local_driver.close()
    await remote_driver.close()
    
    print("\n" + "=" * 80)
    print("迁移完成！")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(migrate_data())

