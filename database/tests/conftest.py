"""
Database 测试配置
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects import sqlite

# 导入Base模型（路径已在上方设置）
from database.src.models.base import Base

# 将JSONB映射到JSON（SQLite兼容）
sqlite.JSONB = sqlite.JSON


@pytest.fixture(scope="function")
def db_session():
    """数据库会话fixture"""
    from sqlalchemy import MetaData
    from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
    from sqlalchemy import JSON
    
    # 使用内存数据库进行测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 注册JSONB到JSON的适配器
    @event.listens_for(engine, "connect", insert=True)
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """为SQLite设置JSON支持"""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # 在创建表之前，将所有PostgreSQL特定类型替换为SQLite兼容类型
    from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY
    from sqlalchemy import String
    
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PGJSONB):
                column.type = JSON()
            elif isinstance(column.type, PGARRAY):
                # ARRAY类型在SQLite中可以用JSON或Text替代
                # 这里使用JSON来保持数据结构的完整性
                column.type = JSON()
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def test_engine():
    """测试数据库引擎"""
    from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
    from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY
    from sqlalchemy import JSON
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 在创建表之前，将所有PostgreSQL特定类型替换为SQLite兼容类型
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PGJSONB):
                column.type = JSON()
            elif isinstance(column.type, PGARRAY):
                column.type = JSON()
    
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

