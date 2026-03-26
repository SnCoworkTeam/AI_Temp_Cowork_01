# 动态工作流路由修复完成

## 问题

前端请求 `POST http://localhost:8080/api/v1/dynamic-workflow/execute` 返回 404 错误。

## 解决方案

在 `api-gateway/src/main.py` 中添加了动态工作流路由，位置在 Agent Service 路由之前（第334-356行）：

```python
# Agent Service - 动态工作流路由（必须在 /api/agents/{path} 之前注册）
@app.api_route("/api/v1/dynamic-workflow/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def dynamic_workflow_proxy(request: Request, path: str):
    """动态工作流服务代理"""
    # 检查是否是流式请求
    accept_header = request.headers.get("accept", "")
    is_stream = "text/event-stream" in accept_header or "/stream" in path or "execute" in path
    
    logger.info(f"Dynamic workflow routing: {request.method} {request.url.path} -> agent-service:/api/v1/dynamic-workflow/{path}")
    
    if is_stream:
        # 流式请求，使用流式代理
        return await stream_proxy.proxy_stream(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/dynamic-workflow/{path}" if path else "/api/v1/dynamic-workflow"
        )
    else:
        # 非流式请求，使用普通代理
        return await gateway_proxy.forward_request(
            request=request,
            service_name="agent-service",
            path=f"/api/v1/dynamic-workflow/{path}" if path else "/api/v1/dynamic-workflow"
        )
```

## 路由说明

- **API Gateway路径**: `/api/v1/dynamic-workflow/{path:path}`
- **目标服务**: `agent-service`
- **目标路径**: `/api/v1/dynamic-workflow/{path}`
- **流式支持**: 自动检测流式请求（通过 `accept` 头或路径中的 `execute`/`stream`）
- **位置**: 必须在 `/api/agents/{path}` 路由之前注册，确保优先匹配

## 测试步骤

1. **重启 API Gateway 服务**
   ```bash
   # 如果使用Docker
   docker-compose restart api-gateway
   
   # 或者直接重启服务
   cd api-gateway && python -m uvicorn src.main:app --reload
   ```

2. **验证路由**
   - 前端请求 `POST http://localhost:8080/api/v1/dynamic-workflow/execute` 应该能够正常路由
   - 检查 API Gateway 日志，应该看到 "Dynamic workflow routing" 日志

3. **测试流式输出**
   - 前端应该能够接收到流式响应
   - 响应格式为 Server-Sent Events (SSE)

## 相关文件

- `api-gateway/src/main.py` - API Gateway 主文件（已修改）
- `agent-service/src/routes/dynamic_workflow.py` - 动态工作流路由（已存在）
- `agent-service/src/main.py` - Agent Service 主文件（路由已注册）

## 总结

✅ **路由已添加** - API Gateway 现在可以正确路由动态工作流请求到 agent-service
✅ **流式支持** - 自动检测并支持流式响应
✅ **日志记录** - 添加了路由日志以便调试

重启 API Gateway 后，前端应该能够正常使用动态工作流功能！


