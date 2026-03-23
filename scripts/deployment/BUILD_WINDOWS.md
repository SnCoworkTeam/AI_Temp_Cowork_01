# Windows Docker构建指南

## 前置要求

1. **启动Docker Desktop**
   - 在Windows开始菜单中搜索"Docker Desktop"并启动
   - 等待Docker Desktop完全启动（系统托盘图标变为绿色）
   - 启动后，Docker Desktop需要几分钟时间来初始化

## 构建步骤

### 方法1: 使用docker-compose（推荐）

```powershell
# 1. 确保Docker Desktop已启动
docker info

# 2. 拉取基础镜像
docker pull redis:7-alpine
docker pull python:3.11-slim
docker pull node:20-alpine

# 3. 构建所有服务镜像
docker-compose build

# 4. 验证镜像
docker images
```

### 方法2: 分步构建

```powershell
# 拉取Redis镜像
docker pull redis:7-alpine

# 构建MCP Gateway
docker-compose build mcp-gateway

# 构建Workflow Engine
docker-compose build workflow-engine

# 构建Web UI
docker-compose build web-ui

# 构建Auth Service
docker-compose build auth-service

# 构建Knowledge Base
docker-compose build knowledge-base
```

## 验证构建

```powershell
# 查看所有镜像
docker images

# 查看特定服务镜像
docker images | findstr enterprise-ai
```

## 启动服务

```powershell
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 常见问题

### Docker Desktop未运行
**错误信息:**
```
error during connect: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

**解决方案:**
1. 打开Docker Desktop应用程序
2. 等待Docker完全启动（系统托盘图标变为绿色）
3. 重新运行命令

### 镜像拉取失败
**可能原因:**
- 网络连接问题
- 需要配置Docker镜像加速器（国内用户）

**解决方案:**
1. 检查网络连接
2. 配置Docker镜像加速器（在Docker Desktop设置中）
   - 推荐镜像源：阿里云、腾讯云、网易云等

### 构建失败
**可能原因:**
- Dockerfile语法错误
- 依赖安装失败
- 磁盘空间不足

**解决方案:**
```powershell
# 查看详细错误信息
docker-compose build --no-cache

# 查看特定服务的构建日志
docker-compose build mcp-gateway --progress=plain
```

