"""
数据库连接管理
"""
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from database.src.core.database import get_database_settings
from database.src.models.base import Base
import os

# 获取数据库配置
settings = get_database_settings()
database_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# 创建引擎
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

