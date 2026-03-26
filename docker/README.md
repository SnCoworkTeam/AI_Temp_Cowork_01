# Docker 开发环境配置

## 概述

本项目提供了完整的Docker开发和生产环境配置，支持热重载、调试和多阶段构建优化。

## 快速开始

### 开发环境

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 编辑 .env 文件，填入必要的配置

# 3. 启动所有服务（开发模式，支持热重载）
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

### 生产环境

```bash
# 1. 复制并配置生产环境变量
cp .env.example .env.prod

# 2. 启动生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

## 服务说明

### 1. Redis (端口: 6379)
- 缓存服务
- 数据持久化到 `redis_data` volume
- 配置文件: `docker/redis/redis.conf`

### 2. MCP Gateway (端口: 8001)
- FastAPI服务
- 开发模式: 支持热重载，代码修改自动重启
- 生产模式: 多worker模式（4个worker）

### 3. Workflow Engine (端口: 8002)
- LangGraph工作流引擎
- 开发模式: 支持热重载，代码修改自动重启
- 生产模式: 多worker模式（4个worker）

### 4. Web UI (端口: 3000)
- Next.js前端应用
- 开发模式: 支持热重载，支持文件监听
- 生产模式: 优化构建，使用standalone模式

## 开发特性

### 热重载
- Python服务使用 `uvicorn --reload` 自动检测代码变更
- Next.js使用开发模式，支持快速刷新

### 调试支持
开发环境的Dockerfile包含：
- `ipython` - 交互式Python shell
- `ipdb` - Python调试器
- `vim` - 文本编辑器
- `git` - 版本控制

### Volume挂载
开发环境使用volume挂载源代码，实现：
- 代码修改立即生效
- 无需重建镜像
- 保持开发环境一致性

## 环境变量

### 必需变量
- `OPENAI_API_KEY` - OpenAI API密钥（Workflow Engine需要）
- `LANGCHAIN_API_KEY` - LangChain API密钥（可选）

### 可选变量
参考 `.env.example` 文件

## 网络配置

所有服务在 `enterprise-ai-network` 网络中，可以通过服务名相互访问：
- `mcp-gateway:8001`
- `workflow-engine:8002`
- `redis:6379`

## 健康检查

所有服务都配置了健康检查：
- MCP Gateway: `http://localhost:8001/api/health`
- Workflow Engine: `http://localhost:8002/api/health`
- Web UI: `http://localhost:3000/api/health`
- Redis: `redis-cli ping`

## 常见问题

### 1. 端口冲突
如果端口被占用，修改 `.env` 文件中的端口配置：
```bash
MCP_GATEWAY_PORT=8001
WORKFLOW_ENGINE_PORT=8002
WEB_UI_PORT=3000
REDIS_PORT=6379
```

### 2. 热重载不工作
- 确保使用 `docker-compose.yml`（开发配置）
- 检查volume挂载是否正确
- 查看服务日志：`docker-compose logs -f [service-name]`

### 3. 构建失败
- 清理旧的镜像和容器：
  ```bash
  docker-compose down -v
  docker system prune -a
  ```
- 重新构建：
  ```bash
  docker-compose build --no-cache
  ```

### 4. 权限问题
- 开发环境使用root用户（便于调试）
- 生产环境使用非root用户（安全）

## 性能优化

### 开发环境
- 使用volume挂载，避免复制文件
- 启用热重载，快速迭代

### 生产环境
- 多阶段构建，减小镜像大小
- 使用Alpine Linux基础镜像
- 多worker进程，提高并发性能
- 非root用户运行，提高安全性

## 监控和调试

### 查看服务状态
```bash
docker-compose ps
```

### 查看服务日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f mcp-gateway
docker-compose logs -f workflow-engine
docker-compose logs -f web-ui
```

### 进入容器调试
```bash
# 进入MCP Gateway容器
docker-compose exec mcp-gateway bash

# 进入Workflow Engine容器
docker-compose exec workflow-engine bash

# 进入Web UI容器
docker-compose exec web-ui sh
```

### 查看资源使用
```bash
docker stats
```

## 数据持久化

- Redis数据: `redis_data` volume
- 开发环境node_modules: 使用named volume避免覆盖

## 清理

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器和volume
docker-compose down -v

# 清理所有未使用的资源
docker system prune -a
```









