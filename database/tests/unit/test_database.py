"""
数据库连接测试
"""
import pytest
import sys
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.database import DatabaseManager, get_database_settings


@pytest.mark.unit
class TestDatabaseManager:
    """数据库管理器测试"""
    
    def test_database_settings(self):
        """测试数据库配置"""
        # 创建独立的配置实例，避免环境变量干扰
        from database.src.core.database import DatabaseSettings
        settings = DatabaseSettings()
        assert settings is not None
        assert settings.DB_HOST is not None
        assert settings.DB_PORT > 0
    
    def test_database_manager_initialization(self):
        """测试数据库管理器初始化"""
        # 创建独立的配置实例
        from database.src.core.database import DatabaseSettings
        test_settings = DatabaseSettings()
        manager = DatabaseManager(settings=test_settings)
        assert manager is not None
        assert manager.settings is not None
    
    def test_connection_pool_config(self):
        """测试连接池配置"""
        # 创建独立的配置实例
        from database.src.core.database import DatabaseSettings
        settings = DatabaseSettings()
        assert settings.DB_POOL_SIZE > 0
        assert settings.DB_MAX_OVERFLOW >= 0


@pytest.mark.unit
class TestDatabaseConnection:
    """数据库连接测试"""
    
    def test_in_memory_connection(self, db_session):
        """测试内存数据库连接"""
        # 使用db_session fixture，它已经配置了JSONB兼容性
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    def test_create_tables(self, db_session):
        """测试创建表"""
        # 使用db_session fixture，它已经配置了JSONB兼容性
        # 检查表是否存在（SQLite特定）
        result = db_session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ))
        tables = [row[0] for row in result]
        assert len(tables) > 0

