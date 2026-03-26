# 动态工作流路由修复

## 问题

前端请求 `POST http://localhost:8080/api/v1/dynamic-workflow/execute` 返回 404 错误。

## 原因

API Gateway 没有配置 `/api/v1/dynamic-workflow/{path}` 路由到 agent-service。

## 解决方案

在 `api-gateway/src/main.py` 中添加了动态工作流路由：

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

- **路径**: `/api/v1/dynamic-workflow/{path:path}`
- **目标服务**: `agent-service`
- **目标路径**: `/api/v1/dynamic-workflow/{path}`
- **流式支持**: 自动检测流式请求并使用流式代理

## 测试

重启 API Gateway 后，前端请求应该能够正常路由到 agent-service。


