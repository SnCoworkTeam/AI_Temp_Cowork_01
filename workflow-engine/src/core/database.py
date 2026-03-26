"""
数据库连接初始化
工作流引擎的数据库连接管理
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from sqlalchemy import text

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
    init_session_factory
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
            _ensure_workflow_connection_columns(engine)
            logger.info("Database connection initialized successfully")
            return True
        else:
            logger.error("Database connection test failed")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        return False


def _ensure_workflow_connection_columns(engine) -> None:
    """确保工作流连接表包含label/style字段，避免旧库导致500"""
    try:
        with engine.begin() as conn:
            table_exists = conn.execute(
                text("SELECT to_regclass('public.workflow_connections')")
            ).scalar()
            if not table_exists:
                return
            conn.execute(
                text(
                    "ALTER TABLE public.workflow_connections "
                    "ADD COLUMN IF NOT EXISTS label VARCHAR(200)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE public.workflow_connections "
                    "ADD COLUMN IF NOT EXISTS style JSONB"
                )
            )
    except Exception as exc:
        logger.warning(
            f"Failed to ensure workflow_connections schema: {exc}",
            exc_info=True
        )


def close_database():
    """关闭数据库连接"""
    global _db_manager
    if _db_manager:
        _db_manager.dispose()
        _db_manager = None
        logger.info("Database connection closed")


# 获取数据库引擎
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








