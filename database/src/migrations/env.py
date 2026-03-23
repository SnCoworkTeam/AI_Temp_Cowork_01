"""
Alembic迁移环境配置
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入基础模型
from database.src.models.base import Base
from database.src.models.user_models import User, Role, Permission, UserSession
from database.src.models.workflow_models import WorkflowDefinition, WorkflowExecution, WorkflowNode, WorkflowConnection
from database.src.models.knowledge_models import Document, DocumentChunk, KnowledgeGraphNode, KnowledgeGraphEdge
from database.src.models.mcp_models import MCPTool, MCPToolExecution
from database.src.models.system_models import SystemConfig, AuditLog
from database.src.models.token_blacklist import TokenBlacklist
from database.src.models.entity_mapping import EntityMapping
from database.src.models.agent_definition import AgentDefinition

# 导入metadata-service的模型（用于迁移）
try:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from metadata_service.src.models.workflow_version import WorkflowVersion, WorkflowVersionTag
except ImportError:
    # 如果metadata-service不可用，迁移脚本仍可运行
    pass

# 导入数据库配置
from database.src.core.database import get_database_settings

# this is the Alembic Config object
config = context.config

# 从环境变量或配置文件获取数据库URL
settings = get_database_settings()
database_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# 设置数据库URL
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入所有模型以确保它们被注册
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()








