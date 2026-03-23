# 知识库服务请求和日志问题修复总结

## 问题描述

用户反馈：知识库服务的请求都发不过去，并且日志里也没有任何记录。

## 问题分析

经过检查，发现了以下问题：

### 1. 请求日志中间件缺少异常处理 ⚠️

**问题**：`log_requests` 中间件没有异常处理，如果请求处理过程中抛出异常，中间件不会记录任何日志。

**位置**：`knowledge-base/src/main.py` 第 180-194 行

**影响**：
- 如果请求在到达路由之前失败，不会记录日志
- 如果请求处理过程中抛出异常，不会记录请求信息
- 导致用户看不到任何请求记录

### 2. 服务未注册到服务发现中心 ⚠️

**问题**：知识库服务没有实现服务注册功能，无法被 API Gateway 通过服务发现找到。

**影响**：
- API Gateway 需要通过服务发现或 fallback 机制才能找到服务
- 如果 fallback 配置不正确，请求可能无法到达服务

### 3. 日志记录不够详细 ⚠️

**问题**：启动日志和请求日志不够详细，难以诊断问题。

**影响**：
- 无法快速定位服务启动问题
- 无法追踪请求的完整生命周期

## 修复方案

### 1. 修复请求日志中间件 ✅

**修改内容**：
- 添加了异常处理，确保所有请求（包括失败的）都被记录
- 在请求到达时立即记录日志
- 记录请求的完整信息（方法、路径、客户端IP、状态码、处理时间）
- 异常时记录详细的错误信息

**代码变更**：
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志和监控统计"""
    start_time = time.time()
    
    # 记录请求到达
    logger.info(
        f"Request received: {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.3f}s",
            exc_info=True
        )
        raise
```

### 2. 添加服务注册功能 ✅

**修改内容**：
- 实现了 `register_to_registry()` 函数，在服务启动时注册到 Registry Service
- 实现了 `send_heartbeat()` 函数，定期发送心跳保持注册状态
- 实现了 `heartbeat_loop()` 后台任务，每10秒发送一次心跳
- 在 `lifespan` 函数中集成服务注册和心跳机制

**功能特性**：
- 自动注册到服务发现中心
- 定期发送心跳保持服务状态
- 优雅关闭时取消心跳任务
- 注册失败不影响服务启动（仅记录警告）

### 3. 增强启动日志 ✅

**修改内容**：
- 添加了更详细的启动日志
- 记录服务监听地址和端口
- 记录存储目录信息
- 记录服务注册状态
- 添加了异常堆栈跟踪（`exc_info=True`）

## 验证步骤

### 1. 检查服务启动日志

重启知识库服务后，应该看到以下日志：

```
[INFO] Knowledge Base Service starting up...
[INFO] Service will listen on 0.0.0.0:8004
[INFO] Database initialized successfully
[INFO] Vector store initialized
[INFO] Embedding manager initialized: dimension=384
[INFO] Storage directories ready: ./documents, ./chroma_db
[INFO] Knowledge Base Service registered successfully, service_id: <service_id>
[INFO] Knowledge Base Service started successfully
```

### 2. 检查请求日志

发送请求到知识库服务后，应该看到：

```
[INFO] Request received: GET /api/health - Client: <client_ip>
[INFO] Request completed: GET /api/health - Status: 200 - Time: 0.012s
```

如果请求失败，应该看到：

```
[ERROR] Request failed: GET /api/health - Error: <error_message> - Time: 0.005s
```

### 3. 检查服务注册

通过 API Gateway 或直接访问 Registry Service 检查服务是否已注册：

```bash
# 检查服务列表
curl http://localhost:8000/api/services

# 检查知识库服务
curl http://localhost:8000/api/discover/knowledge-base
```

### 4. 测试请求路由

通过 API Gateway 发送请求：

```bash
# 健康检查
curl http://localhost:8080/api/knowledge/health

# 获取文档列表
curl http://localhost:8080/api/knowledge/documents
```

## 环境变量配置

确保以下环境变量已正确配置：

```bash
# 服务配置
HOST=0.0.0.0
PORT=8004

# 服务发现（可选，有默认值）
REGISTRY_SERVICE_URL=http://registry-service:8000
SERVICE_HOST=knowledge-base  # Docker 模式使用服务名，本地模式使用 localhost
```

## 注意事项

1. **服务注册失败不影响服务运行**：如果 Registry Service 不可用，服务仍然可以正常运行，API Gateway 会使用 fallback 机制。

2. **日志级别**：确保日志级别设置为 `INFO` 或更低，才能看到请求日志。

3. **Docker 网络**：在 Docker 环境中，确保服务在同一个网络中，服务名可以正确解析。

4. **端口映射**：确保端口映射正确，服务可以从外部访问。

## 后续建议

1. **监控和告警**：建议添加监控和告警机制，及时发现服务问题。

2. **日志聚合**：建议使用日志聚合工具（如 ELK、Loki）集中管理日志。

3. **健康检查**：确保健康检查端点正常工作，用于服务发现和负载均衡。

4. **性能监控**：可以添加性能监控中间件，记录请求的详细性能指标。

