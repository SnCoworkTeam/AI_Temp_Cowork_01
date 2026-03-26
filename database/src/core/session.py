"""
数据库会话管理
提供会话上下文管理器
"""
import logging
from typing import Generator, Optional
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from .database import get_engine

logger = logging.getLogger(__name__)

# 创建会话工厂
SessionLocal = sessionmaker(
    bind=None,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def init_session_factory():
    """初始化会话工厂（绑定引擎）"""
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    logger.info("Session factory initialized")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（上下文管理器）
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（FastAPI依赖）
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()









