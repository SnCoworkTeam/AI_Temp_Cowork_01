# 数据库服务 Docker 配置

## 概述

本配置提供了企业AI平台的数据库服务Docker编排，包括：
- PostgreSQL 15 数据库
- Redis 7 缓存服务
- Redis Commander Web管理界面

## 文件结构

```
.
├── docker-compose.db.yml          # 数据库服务编排文件
├── .env.database.example          # 环境变量配置示例
└── database/
    └── init-scripts/               # 数据库初始化脚本
        ├── 01-init-schema.sql     # 基础表结构初始化
        ├── 02-seed-data.sql       # 种子数据
        ├── 03-create-indexes.sql # 索引创建
        └── README.md              # 初始化脚本说明
```

## 快速开始

### 1. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.database.example .env.database
```

编辑 `.env.database` 文件，修改数据库密码等配置。

### 2. 启动数据库服务

```bash
# 启动所有数据库服务
docker-compose -f docker-compose.db.yml --env-file .env.database up -d

# 或者只启动PostgreSQL
docker-compose -f docker-compose.db.yml --env-file .env.database up -d postgres

# 查看日志
docker-compose -f docker-compose.db.yml logs -f postgres
```

### 3. 验证服务

```bash
# 检查PostgreSQL连接
docker exec -it enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT version();"

# 检查Redis连接
docker exec -it enterprise-ai-redis redis-cli ping

# 访问Redis Commander
# 打开浏览器访问 http://localhost:8081
```

## 服务说明

### PostgreSQL

- **容器名**: `enterprise-ai-postgres`
- **端口**: `5432`
- **数据库**: `ai_platform`（可通过环境变量配置）
- **用户**: `ai_user`（可通过环境变量配置）
- **数据卷**: `postgres_data`（持久化存储）

**特性**：
- 自动执行初始化脚本（`database/init-scripts/`）
- 健康检查配置
- 优化的PostgreSQL参数
- 数据持久化

### Redis

- **容器名**: `enterprise-ai-redis`
- **端口**: `6379`
- **数据卷**: `redis_data`（持久化存储）

**特性**：
- 使用Redis配置文件
- 健康检查配置
- 数据持久化
- AOF持久化（在redis.conf中配置）

### Redis Commander

- **容器名**: `enterprise-ai-redis-commander`
- **端口**: `8081`
- **Web界面**: http://localhost:8081

**特性**：
- Redis可视化管理界面
- 支持查看、编辑、删除键值
- 支持执行Redis命令

## 使用场景

### 开发环境

```bash
# 启动数据库服务
docker-compose -f docker-compose.db.yml --env-file .env.database up -d

# 启动应用服务（使用主docker-compose.yml）
docker-compose up -d
```

### 生产环境

1. **修改默认密码**：编辑 `.env.database`，使用强密码
2. **启用SSL/TLS**：配置数据库SSL连接
3. **配置备份**：设置定期备份策略
4. **监控**：配置数据库监控和告警
5. **资源限制**：在docker-compose中设置资源限制

### 数据库迁移

```bash
# 进入数据库容器
docker exec -it enterprise-ai-postgres bash

# 运行Alembic迁移
cd /app
alembic upgrade head
```

## 数据持久化

所有数据存储在Docker卷中：

- `postgres_data`: PostgreSQL数据目录
- `redis_data`: Redis数据目录

查看卷：

```bash
docker volume ls | grep enterprise-ai
```

备份数据：

```bash
# 备份PostgreSQL
docker exec enterprise-ai-postgres pg_dump -U ai_user ai_platform > backup.sql

# 备份Redis
docker exec enterprise-ai-redis redis-cli SAVE
docker cp enterprise-ai-redis:/data/dump.rdb ./redis-backup.rdb
```

恢复数据：

```bash
# 恢复PostgreSQL
docker exec -i enterprise-ai-postgres psql -U ai_user ai_platform < backup.sql

# 恢复Redis
docker cp redis-backup.rdb enterprise-ai-redis:/data/dump.rdb
docker restart enterprise-ai-redis
```

## 环境变量

主要环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_NAME` | `ai_platform` | 数据库名称 |
| `DB_USER` | `ai_user` | 数据库用户 |
| `DB_PASSWORD` | `ai_password` | 数据库密码（请修改） |
| `DB_PORT` | `5432` | PostgreSQL端口 |
| `REDIS_PORT` | `6379` | Redis端口 |
| `REDIS_COMMANDER_PORT` | `8081` | Redis Commander端口 |
| `REDIS_COMMANDER_USER` | `admin` | Redis Commander用户名 |
| `REDIS_COMMANDER_PASSWORD` | `admin` | Redis Commander密码（请修改） |

完整列表请参考 `.env.database.example`。

## 健康检查

所有服务都配置了健康检查：

```bash
# 检查服务状态
docker-compose -f docker-compose.db.yml ps

# 查看健康检查日志
docker inspect enterprise-ai-postgres | grep -A 10 Health
```

## 故障排除

### PostgreSQL连接失败

1. 检查容器是否运行：`docker ps | grep postgres`
2. 查看日志：`docker logs enterprise-ai-postgres`
3. 检查端口是否被占用：`netstat -an | grep 5432`
4. 验证环境变量：`docker exec enterprise-ai-postgres env | grep POSTGRES`

### Redis连接失败

1. 检查容器是否运行：`docker ps | grep redis`
2. 查看日志：`docker logs enterprise-ai-redis`
3. 测试连接：`docker exec enterprise-ai-redis redis-cli ping`

### 初始化脚本未执行

1. 检查脚本文件是否存在：`ls database/init-scripts/`
2. 查看容器日志：`docker logs enterprise-ai-postgres | grep init`
3. 手动执行：`docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < database/init-scripts/01-init-schema.sql`

### 数据丢失

1. 检查数据卷：`docker volume inspect postgres_data`
2. 查看卷数据：`docker run --rm -v postgres_data:/data alpine ls -la /data`
3. 从备份恢复（如果有）

## 安全建议

1. **修改默认密码**：生产环境必须修改所有默认密码
2. **网络隔离**：使用Docker网络隔离数据库服务
3. **访问控制**：限制数据库访问IP
4. **SSL/TLS**：生产环境启用SSL连接
5. **定期备份**：设置自动备份策略
6. **监控告警**：配置数据库监控和告警
7. **日志审计**：启用数据库审计日志

## 相关文档

- [PostgreSQL文档](https://www.postgresql.org/docs/)
- [Redis文档](https://redis.io/documentation)
- [Redis Commander文档](https://github.com/joeferner/redis-commander)
- [Docker Compose文档](https://docs.docker.com/compose/)

## 常见命令

```bash
# 启动服务
docker-compose -f docker-compose.db.yml --env-file .env.database up -d

# 停止服务
docker-compose -f docker-compose.db.yml stop

# 停止并删除容器
docker-compose -f docker-compose.db.yml down

# 停止并删除容器和数据卷（危险！）
docker-compose -f docker-compose.db.yml down -v

# 查看日志
docker-compose -f docker-compose.db.yml logs -f

# 重启服务
docker-compose -f docker-compose.db.yml restart

# 进入PostgreSQL容器
docker exec -it enterprise-ai-postgres bash

# 进入Redis容器
docker exec -it enterprise-ai-redis sh

# 连接PostgreSQL
docker exec -it enterprise-ai-postgres psql -U ai_user -d ai_platform

# 连接Redis
docker exec -it enterprise-ai-redis redis-cli
```









