# 502 Bad Gateway 错误排查指南

## 问题描述

访问知识库管理页面时出现 `502 (Bad Gateway)` 错误，通常发生在：
- `GET http://localhost:3000/api/knowledge-bases`
- `POST http://localhost:3000/api/knowledge-bases`

## 错误原因

502 Bad Gateway 错误表示 Next.js API 路由（localhost:3000）无法连接到后端服务。可能的原因：

1. **API Gateway 未运行**（如果使用 API Gateway）
2. **知识库服务未运行**
3. **服务端口配置错误**
4. **网络连接问题**
5. **API Gateway 路由配置错误**

## 排查步骤

### 1. 检查服务运行状态

#### 检查 API Gateway（如果使用）
```bash
# 检查 API Gateway 是否运行
curl http://localhost:8080/health

# 或访问浏览器
http://localhost:8080/health
```

#### 检查知识库服务
```bash
# 检查知识库服务是否运行
curl http://localhost:8004/api/health

# 或访问浏览器
http://localhost:8004/api/health
```

### 2. 检查环境变量配置

在 `web-ui` 目录下检查环境变量：

```bash
# 查看 .env.local 或 .env 文件
cat web-ui/.env.local
```

确保以下环境变量正确配置：

```env
# 如果使用 API Gateway
API_GATEWAY_URL=http://localhost:8080
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8080

# 如果直接使用知识库服务
KNOWLEDGE_BASE_URL=http://localhost:8004
NEXT_PUBLIC_KNOWLEDGE_BASE_URL=http://localhost:8004
```

### 3. 检查 API 路由配置

检查 `web-ui/src/app/api/knowledge-bases/route.ts` 中的 URL 构建逻辑：

```typescript
// 如果配置了 API_GATEWAY_URL，使用：
// http://localhost:8080/api/knowledge/knowledge-bases

// 否则使用：
// http://localhost:8004/api/knowledge-bases
```

### 4. 直接测试后端 API

#### 测试 API Gateway 路由（如果使用）
```bash
# 测试知识库列表
curl http://localhost:8080/api/knowledge/knowledge-bases?page=1&page_size=20

# 测试创建知识库
curl -X POST http://localhost:8080/api/knowledge/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name":"测试知识库","description":"测试"}'
```

#### 直接测试知识库服务
```bash
# 测试知识库列表
curl http://localhost:8004/api/knowledge-bases?page=1&page_size=20

# 测试创建知识库
curl -X POST http://localhost:8004/api/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name":"测试知识库","description":"测试"}'
```

### 5. 检查 Docker 容器状态（如果使用 Docker）

```bash
# 查看所有容器状态
docker ps -a

# 查看 API Gateway 容器日志
docker logs api-gateway

# 查看知识库服务容器日志
docker logs knowledge-base

# 检查容器网络连接
docker network ls
docker network inspect <network_name>
```

### 6. 检查防火墙和端口

```bash
# Windows: 检查端口是否被占用
netstat -ano | findstr :8080
netstat -ano | findstr :8004

# Linux/Mac: 检查端口是否被占用
lsof -i :8080
lsof -i :8004
```

## 解决方案

### 方案 1: 启动缺失的服务

#### 启动 API Gateway
```bash
# 如果使用 Docker Compose
docker-compose up -d api-gateway

# 如果直接运行
cd api-gateway
npm start
# 或
python main.py
```

#### 启动知识库服务
```bash
# 如果使用 Docker Compose
docker-compose up -d knowledge-base

# 如果直接运行
cd knowledge-base
python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

### 方案 2: 修改环境变量配置

如果 API Gateway 未运行，可以配置直接使用知识库服务：

在 `web-ui/.env.local` 中：
```env
# 注释掉或删除 API Gateway 配置
# API_GATEWAY_URL=http://localhost:8080
# NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8080

# 使用知识库服务直接连接
KNOWLEDGE_BASE_URL=http://localhost:8004
NEXT_PUBLIC_KNOWLEDGE_BASE_URL=http://localhost:8004
```

然后重启 Next.js 开发服务器：
```bash
cd web-ui
npm run dev
```

### 方案 3: 检查 API Gateway 路由配置

如果使用 API Gateway，确保路由配置正确：

检查 API Gateway 的配置文件（通常是 `api-gateway/config/routes.json` 或类似文件）：

```json
{
  "routes": [
    {
      "path": "/api/knowledge/*",
      "target": "http://knowledge-base:8004/api",
      "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]
    }
  ]
}
```

### 方案 4: 检查服务发现配置

如果使用服务发现，确保：
1. 知识库服务已注册到服务发现中心
2. API Gateway 可以正确发现知识库服务

## 调试技巧

### 1. 查看 Next.js 服务器日志

在运行 Next.js 开发服务器时，查看控制台输出：

```bash
cd web-ui
npm run dev
```

应该能看到类似这样的日志：
```
[Knowledge Bases API] Request URL: http://localhost:8080/api/knowledge/knowledge-bases?page=1&page_size=20
[Knowledge Bases API] API Gateway URL: http://localhost:8080
[Knowledge Bases API] Knowledge Base URL: http://localhost:8004
```

### 2. 查看浏览器网络请求

在浏览器开发者工具中：
1. 打开 Network 标签
2. 查看失败的请求
3. 检查请求 URL 和响应状态
4. 查看响应内容（如果有）

### 3. 使用 Postman 或 curl 测试

直接测试后端 API，确认服务是否正常工作：

```bash
# 测试健康检查
curl http://localhost:8004/api/health

# 测试知识库列表
curl http://localhost:8004/api/knowledge-bases
```

## 常见问题

### Q1: 为什么会出现 502 错误？

A: 502 错误表示网关（Next.js API 路由）无法从上游服务器（API Gateway 或知识库服务）获取有效响应。通常是因为：
- 上游服务未运行
- 网络连接问题
- 服务配置错误

### Q2: 如何判断是 API Gateway 还是知识库服务的问题？

A: 
1. 先测试知识库服务：`curl http://localhost:8004/api/health`
2. 如果知识库服务正常，再测试 API Gateway：`curl http://localhost:8080/api/knowledge/knowledge-bases`
3. 根据测试结果判断问题所在

### Q3: 环境变量不生效怎么办？

A:
1. 确保环境变量文件在正确的位置（`web-ui/.env.local`）
2. 重启 Next.js 开发服务器
3. 检查环境变量名称是否正确（区分 `API_GATEWAY_URL` 和 `NEXT_PUBLIC_API_GATEWAY_URL`）
4. 在服务器端代码中使用 `process.env.API_GATEWAY_URL`（不带 `NEXT_PUBLIC_`）
5. 在客户端代码中使用 `process.env.NEXT_PUBLIC_API_GATEWAY_URL`（带 `NEXT_PUBLIC_`）

### Q4: Docker 容器无法连接怎么办？

A:
1. 确保容器在同一网络中：`docker network ls`
2. 检查容器名称是否正确
3. 使用容器名称而不是 localhost（在 Docker 网络内）
4. 检查端口映射是否正确：`docker ps` 查看端口映射

## 改进后的错误处理

我已经改进了 `web-ui/src/app/api/knowledge-bases/route.ts` 的错误处理：

1. **添加了超时控制**（10秒）
2. **详细的错误日志**（包括 URL、状态码、错误信息）
3. **更好的错误消息**（区分超时、网络错误、服务器错误）
4. **调试信息**（在响应中包含调试信息，便于排查）

现在错误响应会包含更多信息，帮助快速定位问题。

## 下一步

如果问题仍然存在，请：

1. 检查服务运行状态
2. 查看服务日志
3. 测试后端 API 是否正常工作
4. 检查环境变量配置
5. 查看改进后的错误响应中的调试信息


