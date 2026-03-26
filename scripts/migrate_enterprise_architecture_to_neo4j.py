"""
企业架构数据迁移脚本
将PostgreSQL中的企业架构数据迁移到Neo4j
"""
import asyncio
import sys
from pathlib import Path
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import get_db
from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, BusinessProcess, BusinessCapability,
    BusinessService, ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow, TechnologyType, TechnologyInstance
)
import sys
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from services.enterprise_architecture_sync_service import (
    EnterpriseArchitectureSyncService
)
from database.src.core.neo4j_client import get_neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_all_data():
    """迁移所有企业架构数据到Neo4j"""
    print("=" * 60)
    print("企业架构数据迁移到Neo4j")
    print("=" * 60)
    
    # 初始化数据库连接
    db = next(get_db())
    
    # 初始化Neo4j客户端
    neo4j_client = get_neo4j_client()
    if not await neo4j_client.connect():
        print("[ERROR] 无法连接到Neo4j，请检查配置")
        return
    
    # 创建同步服务
    sync_service = EnterpriseArchitectureSyncService(db, neo4j_client)
    
    try:
        # 迁移所有数据
        results = await sync_service.sync_all_enterprise_architecture()
        
        print("\n" + "=" * 60)
        print("迁移结果统计")
        print("=" * 60)
        
        for category, stats in results.items():
            if category != "summary":
                print(f"\n{category}:")
                print(f"  成功: {stats['success']}")
                print(f"  失败: {stats['failed']}")
        
        print(f"\n总计:")
        print(f"  成功: {results['summary']['total_success']}")
        print(f"  失败: {results['summary']['total_failed']}")
        
        print("\n[OK] 数据迁移完成！")
        
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()
        await neo4j_client.disconnect()


if __name__ == "__main__":
    asyncio.run(migrate_all_data())

