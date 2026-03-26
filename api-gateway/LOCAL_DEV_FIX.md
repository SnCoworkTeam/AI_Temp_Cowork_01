# API Gateway 本地开发配置修复

## 问题描述

在本地开发环境中，API Gateway 尝试使用 Docker 服务名（如 `auth-service:8003`）连接后端服务，但这些服务名在本地开发环境中无法解析，导致 `ERR_EMPTY_RESPONSE` 错误。

## 解决方案

### 方法 1: 设置环境变量（推荐）

在 `.env` 文件中添加以下配置：

```bash
# 本地开发模式：使用 localhost 而非 Docker 服务名
LOCAL_DEV=true
# 或者
USE_LOCALHOST=true
```

### 方法 2: 直接设置环境变量

如果使用命令行启动 API Gateway：

**Windows (PowerShell):**
```powershell
$env:LOCAL_DEV="true"
# 然后启动 API Gateway
```

**Linux/Mac:**
```bash
export LOCAL_DEV=true
# 然后启动 API Gateway
```

## 验证修复

1. **确保服务正在运行：**
   - API Gateway: `http://localhost:8080/health`
   - Auth Service: `http://localhost:8003/health`

2. **测试登录接口：**
   ```bash
   curl -X POST http://localhost:8080/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123456"}'
   ```

3. **检查 API Gateway 日志：**
   应该看到类似以下日志：
   ```
   Service auth-service not found in registry, using fallback: http://localhost:8003 (mode: local)
   ```

## 服务端口映射

在本地开发模式下，API Gateway 将使用以下地址：

| 服务名称 | 本地地址 |
|---------|---------|
| auth-service | http://localhost:8003 |
| workflow-engine | http://localhost:8002 |
| mcp-gateway | http://localhost:8001 |
| knowledge-base | http://localhost:8004 |
| metadata-service | http://localhost:8005 |
| chat-service | http://localhost:8006 |
| config-center | http://localhost:8090 |
| registry-service | http://localhost:8000 |

## 注意事项

- 在 Docker Compose 环境中，不需要设置 `LOCAL_DEV=true`，因为 Docker 网络会自动解析服务名
- 只有在本地直接运行服务（非 Docker）时才需要设置此选项
- 确保所有后端服务都在正确的端口上运行

