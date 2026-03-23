"""
数据库连接管理
PostgreSQL连接池配置和会话管理
"""
import logging
from typing import Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.url import URL
try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for environments without pydantic-settings
    from pydantic import BaseModel  # type: ignore
    import os

    class BaseSettings(BaseModel):  # type: ignore
        """简化版 BaseSettings：从环境变量注入同名字段值"""

        def __init__(self, **values):
            env_values = {}
            fields = getattr(self.__class__, "model_fields", None) or getattr(self.__class__, "__fields__", {})
            for name in fields.keys():
                if name in os.environ and name not in values:
                    env_values[name] = os.environ[name]
            super().__init__(**{**env_values, **values})

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = True
            extra = "ignore"

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    # PostgreSQL配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "ai_user"
    DB_PASSWORD: str = "ai_password"
    DB_NAME: str = "ai_platform"
    DB_ECHO: bool = False
    
    # 连接池配置
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # 1小时
    
    # 连接配置
    DB_CONNECT_ARGS: dict = {
        "connect_timeout": 10,
        "application_name": "enterprise_ai_platform"
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


_settings = None


def get_database_settings() -> DatabaseSettings:
    """获取数据库配置（单例）"""
    global _settings
    if _settings is None:
        _settings = DatabaseSettings()
    return _settings


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, settings: Optional[DatabaseSettings] = None):
        """
        初始化数据库管理器
        
        Args:
            settings: 数据库配置，如果为None则从环境变量加载
        """
        self.settings = settings or get_database_settings()
        self._engine: Optional[Engine] = None
    
    def create_engine(self) -> Engine:
        """
        创建数据库引擎
        
        Returns:
            SQLAlchemy引擎实例
        """
        if self._engine is not None:
            return self._engine
        
        # 构建数据库URL
        database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD,
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME
        )
        
        # 创建引擎
        self._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.settings.DB_POOL_SIZE,
            max_overflow=self.settings.DB_MAX_OVERFLOW,
            pool_timeout=self.settings.DB_POOL_TIMEOUT,
            pool_recycle=self.settings.DB_POOL_RECYCLE,
            echo=self.settings.DB_ECHO,
            connect_args=self.settings.DB_CONNECT_ARGS,
            future=True  # 使用SQLAlchemy 2.0风格
        )
        
        logger.info(
            f"Database engine created: {self.settings.DB_HOST}:{self.settings.DB_PORT}/{self.settings.DB_NAME}"
        )
        
        return self._engine
    
    def get_engine(self) -> Engine:
        """获取数据库引擎（如果不存在则创建）"""
        if self._engine is None:
            return self.create_engine()
        return self._engine
    
    def dispose(self):
        """释放数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("Database engine disposed")
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            连接是否成功
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例（单例）"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_engine() -> Engine:
    """获取数据库引擎"""
    return get_database_manager().get_engine()






