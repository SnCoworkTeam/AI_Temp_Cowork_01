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
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()









