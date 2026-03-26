# 登录超时问题诊断报告

**生成时间**: 2025-12-03  
**服务器**: 43.143.139.197  
**问题**: 登录请求超时

## 诊断结果

### ✅ 正常服务

1. **Auth Service (直接访问)** ✅
   - URL: `http://43.143.139.197:8003`
   - 状态: 健康 (HTTP 200)
   - 登录端点测试: 返回 401（正常，用户名/密码错误）

2. **Web UI** ✅
   - URL: `http://43.143.139.197:3000`
   - 状态: 可访问 (HTTP 200)

### ❌ 问题服务

1. **API Gateway** ❌
   - URL: `http://43.143.139.197:8080`
   - 状态: **无法访问（请求超时）**
   - 影响: 所有通过 API Gateway 的请求都失败

2. **Auth Service (通过 API Gateway)** ❌
   - URL: `http://43.143.139.197:8080/api/auth/health`
   - 状态: **无法访问（请求超时）**
   - 原因: API Gateway 不可用

## 问题分析

### 根本原因

**API Gateway 容器未运行或端口 8080 未开放**

登录流程：
1. Web UI (`http://43.143.139.197:3000`) 发送登录请求到 `http://43.143.139.197:8080/api/auth/login`
2. API Gateway 应该将请求转发到 Auth Service (`http://auth-service:8003/auth/login`)
3. 由于 API Gateway 不可用，请求超时

### 为什么直接访问 Auth Service 可以工作？

- Auth Service 容器正常运行在端口 8003
- 直接访问 `http://43.143.139.197:8003/auth/login` 可以正常工作
- 但 Web UI 配置使用 API Gateway，所以无法直接使用 Auth Service

## 解决方案

### 方案 1: 启动 API Gateway（推荐）

在服务器上执行以下命令：

```bash
# 1. 检查 API Gateway 容器状态
docker ps -a | grep api-gateway

# 2. 查看 API Gateway 日志
docker-compose logs api-gateway

# 3. 启动 API Gateway
docker-compose up -d api-gateway

# 4. 检查 API Gateway 是否启动成功
docker ps | grep api-gateway

# 5. 检查 API Gateway 健康状态
curl http://localhost:8080/health
```

### 方案 2: 检查端口映射

确认 `docker-compose.yml` 中 API Gateway 的端口映射：

```yaml
api-gateway:
  ports:
    - "${API_GATEWAY_PORT:-8080}:8080"
```

检查防火墙设置，确保端口 8080 对外开放。

### 方案 3: 临时解决方案 - 修改 Web UI 配置

如果 API Gateway 暂时无法修复，可以临时修改 Web UI 配置，直接访问 Auth Service：

**注意**: 这只是一个临时解决方案，不推荐在生产环境使用。

修改 `web-ui/.env` 或环境变量：

```env
# 临时：直接使用 Auth Service（不通过 API Gateway）
NEXT_PUBLIC_AUTH_SERVICE_URL=http://43.143.139.197:8003
```

然后修改 `web-ui/src/components/LoginForm.tsx` 中的登录 URL 逻辑。

## 验证步骤

修复后，运行诊断脚本验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-login-service-status.ps1
```

预期结果：
- ✅ API Gateway 健康检查通过
- ✅ 通过 API Gateway 访问 Auth Service 成功
- ✅ 登录端点可访问（返回 401 或 200）

## 预防措施

1. **监控服务状态**
   - 设置服务健康检查监控
   - 配置告警，当 API Gateway 不可用时立即通知

2. **服务依赖检查**
   - 确保 API Gateway 的依赖服务（Redis、Registry Service）正常运行
   - 检查服务启动顺序

3. **日志监控**
   - 定期检查 API Gateway 日志
   - 监控错误率和响应时间

## 相关文件

- 诊断脚本: `scripts/check-login-service-status.ps1`
- API Gateway 配置: `api-gateway/src/main.py`
- Auth Service 配置: `auth-service/src/main.py`
- Docker Compose 配置: `docker-compose.yml`

## 下一步行动

1. ✅ 诊断完成 - 已确认问题原因
2. ⏳ 在服务器上启动 API Gateway
3. ⏳ 验证修复效果
4. ⏳ 检查服务依赖（Redis、Registry Service）
5. ⏳ 设置监控和告警

