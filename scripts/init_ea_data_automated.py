#!/usr/bin/env python3
"""
EA数据初始化自动化脚本
自动初始化企业架构数据到PostgreSQL、Qdrant和Neo4j
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "database" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "metadata-service" / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_ea_data():
    """初始化EA数据"""
    try:
        # 检查环境变量
        required_env_vars = [
            "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"缺少必需的环境变量: {', '.join(missing_vars)}")
            logger.info("请设置以下环境变量:")
            for var in missing_vars:
                logger.info(f"  export {var}=<value>")
            return False
        
        logger.info("开始初始化EA数据...")
        
        # 1. 初始化数据库连接
        logger.info("步骤1: 初始化数据库连接...")
        try:
            from database.src.core.database import get_database_manager
            from database.src.core.session import init_session_factory
            
            db_manager = get_database_manager()
            if not db_manager.test_connection():
                logger.error("数据库连接失败")
                return False
            
            init_session_factory()
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
        
        # 2. 初始化EA数据到PostgreSQL
        logger.info("步骤2: 初始化EA数据到PostgreSQL...")
        try:
            from metadata_service.src.scripts.ea_data_initializer import EADataInitializer
            
            initializer = EADataInitializer()
            await initializer.initialize_all()
            logger.info("✅ PostgreSQL数据初始化完成")
        except Exception as e:
            logger.error(f"PostgreSQL数据初始化失败: {e}")
            return False
        
        # 3. 向量化EA实体
        logger.info("步骤3: 向量化EA实体...")
        try:
            from metadata_service.src.services.ea_vectorization_service import EAVectorizationService
            from database.src.core.session import get_db
            
            db = next(get_db())
            vector_service = EAVectorizationService(db)
            
            # 批量向量化
            await vector_service.batch_vectorize_all()
            logger.info("✅ EA实体向量化完成")
            db.close()
        except Exception as e:
            logger.error(f"EA实体向量化失败: {e}")
            return False
        
        # 4. 初始化Neo4j图谱
        logger.info("步骤4: 初始化Neo4j图谱...")
        try:
            from metadata_service.src.services.ea_knowledge_graph import EAKnowledgeGraph
            
            graph_service = EAKnowledgeGraph()
            await graph_service.initialize_from_database()
            logger.info("✅ Neo4j图谱初始化完成")
        except Exception as e:
            logger.warning(f"Neo4j图谱初始化失败（可能Neo4j未运行）: {e}")
            logger.info("⚠️  继续执行，Neo4j功能将不可用")
        
        logger.info("=" * 60)
        logger.info("✅ EA数据初始化完成！")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"EA数据初始化过程出错: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(init_ea_data())
    sys.exit(0 if success else 1)

