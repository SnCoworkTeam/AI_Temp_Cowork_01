# 数据库架构和迁移系统

## 概述

本模块提供了企业AI平台的完整数据库架构，包括：
- PostgreSQL 主数据库（业务数据存储）
- Redis 缓存和会话存储
- SQLAlchemy 2.0 ORM 数据模型
- Alembic 数据库迁移系统
- Repository 模式数据访问层

## 目录结构

```
database/
├── src/
│   ├── core/              # 数据库核心模块
│   │   ├── database.py    # 数据库连接管理
│   │   ├── session.py     # 会话管理
│   │   └── redis_client.py # Redis客户端
│   ├── models/            # SQLAlchemy数据模型
│   │   ├── base.py        # 基础模型类
│   │   ├── user_models.py      # 用户、角色、权限
│   │   ├── workflow_models.py   # 工作流定义和执行
│   │   ├── knowledge_models.py  # 知识库文档和知识图谱
│   │   ├── mcp_models.py        # MCP工具配置和执行
│   │   └── system_models.py     # 系统配置和审计日志
│   ├── repositories/      # 数据访问层（Repository模式）
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── workflow_repository.py
│   │   ├── knowledge_repository.py
│   │   ├── mcp_repository.py
│   │   └── system_repository.py
│   └── migrations/         # Alembic迁移脚本
│       ├── env.py         # 迁移环境配置
│       ├── script.py.mako # 迁移脚本模板
│       └── versions/      # 迁移版本
├── alembic.ini            # Alembic配置文件
├── requirements.txt       # Python依赖
└── README.md             # 本文档
```

## 数据模型

### 用户和权限
- **User**: 用户账户
- **Role**: 角色
- **Permission**: 权限
- **UserSession**: 用户会话

### 工作流
- **WorkflowDefinition**: 工作流定义
- **WorkflowNode**: 工作流节点
- **WorkflowConnection**: 工作流连接
- **WorkflowExecution**: 工作流执行历史

### 知识库
- **Document**: 文档
- **DocumentChunk**: 文档块
- **KnowledgeGraphNode**: 知识图谱节点
- **KnowledgeGraphEdge**: 知识图谱边

### MCP工具
- **MCPTool**: MCP工具配置
- **MCPToolExecution**: 工具执行记录

### 系统
- **SystemConfig**: 系统配置
- **AuditLog**: 审计日志

## 环境变量配置

在 `.env` 文件中配置以下变量：

```env
# PostgreSQL配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform
DB_ECHO=false

# 连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
```

## 使用数据库连接

### 基本用法

```python
from database.src.core.database import get_database_manager, get_engine
from database.src.core.session import get_session, get_db

# 获取数据库引擎
engine = get_engine()

# 使用上下文管理器获取会话
with get_session() as session:
    # 使用session进行数据库操作
    pass

# 在FastAPI中使用（作为依赖）
from fastapi import Depends
from database.src.core.session import get_db

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    # 使用db进行数据库操作
    pass
```

## 使用Repository

### 基本用法

```python
from database.src.core.session import get_session
from database.src.repositories.user_repository import UserRepository

# 使用Repository
with get_session() as session:
    user_repo = UserRepository(session)
    
    # 创建用户
    user = user_repo.create(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    
    # 查询用户
    user = user_repo.get_by_username("testuser")
    
    # 更新用户
    user_repo.update(user.id, full_name="Updated Name")
    
    # 删除用户
    user_repo.delete(user.id)
```

### Repository列表

- `UserRepository`: 用户管理
- `RoleRepository`: 角色管理
- `PermissionRepository`: 权限管理
- `WorkflowDefinitionRepository`: 工作流定义管理
- `WorkflowExecutionRepository`: 工作流执行历史
- `DocumentRepository`: 文档管理
- `MCPToolRepository`: MCP工具管理
- `SystemConfigRepository`: 系统配置管理
- `AuditLogRepository`: 审计日志管理

## 数据库迁移

### 初始化迁移

首次运行迁移：

```bash
cd database
alembic upgrade head
```

### 创建新迁移

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "描述信息"

# 手动创建迁移脚本
alembic revision -m "描述信息"
```

### 运行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision>

# 降级到指定版本
alembic downgrade <revision>

# 降级一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 迁移脚本位置

迁移脚本位于 `database/src/migrations/versions/` 目录。

## 使用Redis

### 同步Redis客户端

```python
from database.src.core.redis_client import get_redis_client

redis_client = get_redis_client()

# 设置值
redis_client.set("key", "value", ex=3600)  # 1小时过期

# 获取值
value = redis_client.get("key")

# 删除键
redis_client.delete("key")

# 检查存在
exists = redis_client.exists("key")
```

### 异步Redis客户端

```python
from database.src.core.redis_client import get_async_redis_client

async def example():
    redis_client = get_async_redis_client()
    
    # 设置值
    await redis_client.set("key", "value", ex=3600)
    
    # 获取值
    value = await redis_client.get("key")
    
    # 删除键
    await redis_client.delete("key")
```

## 最佳实践

1. **使用Repository模式**: 所有数据库操作应通过Repository进行，避免直接使用SQLAlchemy Session。

2. **事务管理**: 使用 `get_session()` 上下文管理器自动管理事务，确保异常时回滚。

3. **连接池配置**: 根据实际负载调整连接池大小（`DB_POOL_SIZE`、`DB_MAX_OVERFLOW`）。

4. **迁移管理**: 
   - 始终在开发环境测试迁移
   - 为每个迁移添加 `downgrade` 函数
   - 在生产环境执行前备份数据库

5. **索引优化**: 为常用查询字段添加索引，提高查询性能。

6. **审计日志**: 使用 `AuditLogRepository.create_log()` 记录重要操作。

## 常见问题

### Q: 如何添加新的数据模型？

1. 在 `src/models/` 中创建新的模型文件
2. 在 `src/models/__init__.py` 中导出新模型
3. 创建对应的Repository（如果需要）
4. 生成新的迁移脚本：`alembic revision --autogenerate -m "添加新模型"`

### Q: 如何在迁移中处理数据？

```python
def upgrade() -> None:
    # 创建表
    op.create_table(...)
    
    # 插入初始数据
    op.execute("INSERT INTO table_name (column1, column2) VALUES ('value1', 'value2')")
```

### Q: 如何回滚迁移？

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>

# 回滚所有迁移
alembic downgrade base
```

## 依赖项

主要依赖项：
- `sqlalchemy==2.0.23`: ORM框架
- `alembic==1.12.1`: 数据库迁移工具
- `psycopg2-binary==2.9.9`: PostgreSQL驱动
- `redis==5.0.1`: Redis客户端
- `pydantic-settings==2.1.0`: 配置管理

## 许可证

本项目遵循项目根目录的许可证声明。









