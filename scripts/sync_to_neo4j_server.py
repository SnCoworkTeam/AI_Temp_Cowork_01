"""
同步企业架构数据到Neo4j服务器
使用远程Neo4j服务器地址
"""
import asyncio
import sys
import os
from pathlib import Path

# 设置Windows控制台编码
if sys.platform == "win32":
    os.system("chcp 65001")

# 添加项目根目录到路径
# 在Docker容器中：
# - /app 是metadata-service的工作目录
# - /database 是数据库模块的挂载目录
# - /app/src 是metadata-service的源代码目录
if os.path.exists("/app"):
    # 容器内：/database已经在sys.path中，只需要添加/app/src
    sys.path.insert(0, "/app/src")
else:
    # 本地开发环境
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from database.src.core.session import get_db, init_session_factory
from database.src.core.neo4j_client import Neo4jClient, Neo4jSettings
from services.enterprise_architecture_sync_service import (
    EnterpriseArchitectureSyncService
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_to_neo4j():
    """同步所有企业架构数据到Neo4j"""
    print("=" * 60)
    print("同步企业架构数据到Neo4j服务器")
    print("=" * 60)
    
    # 配置Neo4j服务器地址（远程服务器）
    neo4j_settings = Neo4jSettings(
        NEO4J_URI="bolt://43.143.90.179:7687",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="Neo4j@2024",
        NEO4J_DATABASE="neo4j"
    )
    
    # 初始化数据库连接
    init_session_factory()
    db = next(get_db())
    
    # 初始化Neo4j客户端
    neo4j_client = Neo4jClient(neo4j_settings)
    print(f"正在连接到Neo4j服务器: {neo4j_settings.NEO4J_URI}")
    
    if not await neo4j_client.connect():
        print("❌ 无法连接到Neo4j服务器，请检查配置")
        return
    
    print("✅ Neo4j连接成功")
    
    # 创建同步服务
    sync_service = EnterpriseArchitectureSyncService(db, neo4j_client)
    
    try:
        print("\n开始同步数据...")
        print("-" * 60)
        
        # 同步所有数据
        results = await sync_service.sync_all_enterprise_architecture()
        
        # 打印同步结果
        if results:
            print("\n同步结果统计:")
            for category, stats in results.items():
                if isinstance(stats, dict) and 'success' in stats:
                    print(f"  {category}: 成功 {stats.get('success', 0)}, 失败 {stats.get('failed', 0)}")
                else:
                    print(f"  {category}: {stats}")
        
        print("\n" + "=" * 60)
        print("✅ 数据同步完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"同步过程中出错: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()
        await neo4j_client.disconnect()
        print("已断开Neo4j连接")


if __name__ == "__main__":
    asyncio.run(sync_to_neo4j())

