"""
数据库依赖注入
FastAPI依赖注入的数据库会话管理
"""
from typing import Generator
from sqlalchemy.orm import Session

# 导入database模块的会话工厂
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（FastAPI依赖）
    包含完整的事务管理和错误处理

    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
        # 注意：不在这里commit，由调用方决定是否commit
        # 如果调用方已经commit，这里不会有问题
        # 如果调用方没有commit，FastAPI结束时也会清理
    except Exception as e:
        # 发生异常时回滚事务
        try:
            session.rollback()
        except Exception as rollback_error:
            # 如果回滚也失败，记录错误并强制关闭
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to rollback transaction: {rollback_error}", exc_info=True)
            try:
                session.close()
            except Exception:
                pass
        raise e
    finally:
        # 确保会话被关闭
        try:
            session.close()
        except Exception as close_error:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to close session: {close_error}", exc_info=True)









