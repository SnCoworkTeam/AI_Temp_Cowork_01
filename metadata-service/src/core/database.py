"""
数据库连接初始化
元数据服务的数据库连接管理
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径，以便导入database模块
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.database import (
    DatabaseManager,
    get_database_manager,
    get_engine
)
from database.src.core.session import (
    SessionLocal,
    init_session_factory,
    get_session as get_db_session
)
from database.src.core.redis_client import (
    get_redis_client,
    get_async_redis_client
)

logger = logging.getLogger(__name__)

# 全局数据库管理器
_db_manager: Optional[DatabaseManager] = None


def init_database() -> bool:
    """
    初始化数据库连接
    
    Returns:
        是否初始化成功
    """
    global _db_manager
    try:
        # 获取数据库管理器
        _db_manager = get_database_manager()
        
        # 创建引擎
        engine = _db_manager.create_engine()
        
        # 初始化会话工厂
        init_session_factory()
        
        # 测试连接
        if _db_manager.test_connection():
            logger.info("Database connection initialized successfully")
            return True
        else:
            logger.error("Database connection test failed")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        return False


def close_database():
    """关闭数据库连接"""
    global _db_manager
    if _db_manager:
        _db_manager.dispose()
        _db_manager = None
        logger.info("Database connection closed")


# 获取数据库会话
def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 获取数据库引擎（用于Alembic迁移等）
def get_database_engine():
    """获取数据库引擎"""
    return get_engine()


# 获取Redis客户端
def get_redis():
    """获取同步Redis客户端"""
    return get_redis_client()


def get_async_redis():
    """获取异步Redis客户端"""
    return get_async_redis_client()

