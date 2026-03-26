# 数据库初始化脚本

## 概述

本目录包含PostgreSQL数据库的初始化脚本，这些脚本在数据库容器首次启动时自动执行。

## 脚本执行顺序

PostgreSQL容器会自动按文件名顺序执行 `/docker-entrypoint-initdb.d` 目录下的 `.sql`、`.sh` 和 `.sql.gz` 文件。

当前脚本执行顺序：
1. `01-init-schema.sql` - 创建扩展、枚举类型和函数
2. `02-seed-data.sql` - 插入种子数据（默认角色、权限、用户等）
3. `03-create-indexes.sql` - 创建性能优化索引

## 脚本说明

### 01-init-schema.sql

**功能**：
- 启用PostgreSQL扩展（uuid-ossp, pg_trgm, pg_stat_statements）
- 创建枚举类型（如果不存在）
- 创建触发器函数（自动更新时间戳等）
- 设置数据库默认权限

**注意事项**：
- 此脚本主要处理扩展和类型，实际表结构由Alembic迁移管理
- 如果枚举类型已存在，会跳过创建（使用DO块处理）

### 02-seed-data.sql

**功能**：
- 插入默认权限（用户管理、角色管理、工作流管理等）
- 插入默认角色（admin, user, developer, viewer）
- 为角色分配权限
- 创建默认管理员用户（用户名：admin，密码：admin123）
- 插入系统配置

**重要提示**：
- 默认管理员密码为 `admin123`，**请在生产环境中立即修改**
- 密码哈希使用bcrypt，示例：`$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYq5L5v5F5e`
- 如果用户已存在，不会覆盖（使用ON CONFLICT处理）

### 03-create-indexes.sql

**功能**：
- 创建复合索引以优化查询性能
- 创建全文搜索索引（GIN索引）
- 创建部分索引（WHERE条件）
- 更新表统计信息

**注意事项**：
- 主要索引已在Alembic迁移中创建
- 此脚本补充额外的性能优化索引
- 索引创建前会检查表是否存在

## 使用方法

### 自动执行

当使用 `docker-compose.db.yml` 启动数据库容器时，这些脚本会自动执行：

```bash
docker-compose -f docker-compose.db.yml --env-file .env.database up -d postgres
```

### 手动执行

如果需要手动执行脚本：

```bash
# 连接到PostgreSQL容器
docker exec -it enterprise-ai-postgres psql -U ai_user -d ai_platform

# 在psql中执行脚本
\i /docker-entrypoint-initdb.d/01-init-schema.sql
\i /docker-entrypoint-initdb.d/02-seed-data.sql
\i /docker-entrypoint-initdb.d/03-create-indexes.sql
```

### 重新初始化

如果需要重新初始化数据库：

```bash
# 停止并删除数据库容器和数据卷
docker-compose -f docker-compose.db.yml down -v

# 重新启动（会重新执行初始化脚本）
docker-compose -f docker-compose.db.yml up -d postgres
```

## 默认数据

### 默认角色

| 角色代码 | 角色名称 | 说明 |
|---------|---------|------|
| admin | 超级管理员 | 拥有所有权限 |
| user | 普通用户 | 基本查看和执行权限 |
| developer | 开发者 | 可以管理工作流和工具 |
| viewer | 查看者 | 只读权限 |

### 默认管理员用户

- **用户名**: `admin`
- **邮箱**: `admin@example.com`
- **密码**: `admin123`（请在生产环境中修改）
- **角色**: `admin`

### 默认权限

权限遵循 `资源:操作` 的命名规范：
- `user:read`, `user:create`, `user:update`, `user:delete`
- `role:read`, `role:create`, `role:update`, `role:delete`
- `workflow:read`, `workflow:create`, `workflow:update`, `workflow:delete`, `workflow:execute`
- `knowledge:read`, `knowledge:create`, `knowledge:update`, `knowledge:delete`
- `tool:read`, `tool:create`, `tool:update`, `tool:delete`, `tool:execute`
- `system:read`, `system:update`, `system:monitor`

## 自定义初始化

如果需要添加自定义初始化逻辑：

1. 创建新的SQL脚本文件（按数字顺序命名，如 `04-custom-init.sql`）
2. 将文件放在 `database/init-scripts/` 目录
3. 脚本会在容器启动时自动执行

## 故障排除

### 脚本执行失败

如果脚本执行失败，检查：
1. SQL语法是否正确
2. 表是否已创建（由Alembic迁移管理）
3. 权限是否足够
4. 查看PostgreSQL容器日志：`docker logs enterprise-ai-postgres`

### 数据未插入

如果种子数据未插入：
1. 检查表是否存在（可能需要先运行Alembic迁移）
2. 检查ON CONFLICT处理是否正确
3. 手动执行脚本查看错误信息

### 索引创建失败

如果索引创建失败：
1. 检查表是否存在
2. 检查索引是否已存在（使用IF NOT EXISTS）
3. 检查扩展是否已启用（如pg_trgm）

## 生产环境建议

1. **修改默认密码**：立即修改默认管理员密码
2. **安全配置**：启用SSL/TLS连接
3. **备份策略**：定期备份数据库
4. **监控**：启用数据库性能监控
5. **权限控制**：限制数据库用户权限
6. **审计日志**：启用审计日志功能

## 相关文档

- [PostgreSQL初始化脚本文档](https://www.postgresql.org/docs/current/app-initdb.html)
- [Alembic迁移文档](../README.md)
- [数据库架构文档](../README.md)









