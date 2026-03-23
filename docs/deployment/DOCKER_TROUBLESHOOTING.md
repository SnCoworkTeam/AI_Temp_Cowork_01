# Docker 服务连接问题排查指南

## 问题：All connection attempts failed

这个错误表示 agent-service 无法连接到其他后端服务（mcp-gateway、knowledge-base 等）。

## 排查步骤

### 1. 检查所有服务是否正在运行

```bash
docker-compose ps
```

确保所有服务状态为 `Up` 或 `Up (healthy)`。

### 2. 检查服务健康状态

```bash
# 检查 agent-service
docker exec enterprise-ai-agent-service curl -f http://localhost:8010/api/v1/health

# 检查 mcp-gateway
docker exec enterprise-ai-mcp-gateway curl -f http://localhost:8001/api/health

# 检查 knowledge-base
docker exec enterprise-ai-knowledge-base curl -f http://localhost:8004/health
```

### 3. 测试服务之间的网络连接

```bash
# 从 agent-service 容器内测试连接 mcp-gateway
docker exec enterprise-ai-agent-service ping -c 2 mcp-gateway

# 从 agent-service 容器内测试连接 knowledge-base
docker exec enterprise-ai-agent-service ping -c 2 knowledge-base

# 测试 HTTP 连接
docker exec enterprise-ai-agent-service curl -f http://mcp-gateway:8001/api/health
docker exec enterprise-ai-agent-service curl -f http://knowledge-base:8004/health
```

### 4. 检查环境变量配置

```bash
# 检查 agent-service 的环境变量
docker exec enterprise-ai-agent-service env | grep -E '(MCP_GATEWAY|KNOWLEDGE_BASE)'

# 应该看到：
# MCP_GATEWAY_URL=http://mcp-gateway:8001
# KNOWLEDGE_BASE_URL=http://knowledge-base:8004
```

### 5. 查看服务日志

```bash
# 查看 agent-service 日志
docker-compose logs agent-service | tail -50

# 查看 mcp-gateway 日志
docker-compose logs mcp-gateway | tail -50

# 查看 knowledge-base 日志
docker-compose logs knowledge-base | tail -50
```

### 6. 检查 Docker 网络

```bash
# 检查网络是否存在
docker network ls | grep enterprise-ai

# 检查网络中的容器
docker network inspect enterprise-ai-platform_enterprise-ai-network | grep -A 10 "Containers"
```

### 7. 重启服务

如果服务配置已更新，需要重启：

```bash
# 重启所有服务
docker-compose down
docker-compose up -d

# 或者只重启 agent-service
docker-compose restart agent-service
```

## 常见问题和解决方案

### 问题 1: 服务启动顺序问题

**症状**: agent-service 在 mcp-gateway 或 knowledge-base 启动之前就启动了。

**解决方案**: 已更新 `docker-compose.yml`，让 agent-service 依赖于这些服务的健康检查。

### 问题 2: 服务健康检查失败

**症状**: 服务虽然运行，但健康检查失败。

**解决方案**: 
- 检查服务的健康检查端点是否正常
- 增加健康检查的 `start_period` 时间
- 检查服务日志中的错误

### 问题 3: Docker 网络问题

**症状**: 容器之间无法互相访问。

**解决方案**:
- 确保所有服务都在同一个 Docker 网络中
- 检查网络配置：`docker network inspect enterprise-ai-platform_enterprise-ai-network`

### 问题 4: 服务 URL 配置错误

**症状**: 环境变量中的 URL 不正确。

**解决方案**:
- 检查 `docker-compose.yml` 中的环境变量配置
- 确保使用 Docker 服务名（如 `mcp-gateway`）而不是 `localhost`

## 快速诊断脚本

运行诊断脚本（Windows PowerShell）：

```powershell
.\web-ui\scripts\check-docker-services.ps1
```

或（Linux/Mac）：

```bash
chmod +x web-ui/scripts/check-docker-services.sh
./web-ui/scripts/check-docker-services.sh
```









