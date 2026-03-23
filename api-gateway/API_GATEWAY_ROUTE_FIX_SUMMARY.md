# API Gateway 路由修复总结

## 修复内容

### 1. 添加动态工作流路由
在 `api-gateway/src/main.py` 中添加了 `/api/v1/dynamic-workflow/{path:path}` 路由，用于将动态工作流请求代理到 `agent-service`。

### 2. 修复重复代码
删除了 `dynamic_workflow_proxy` 函数中的重复代码（第358-379行）。

## 路由配置

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

## 其他错误说明

从控制台日志中看到的其他错误：

1. **403 Forbidden** - `/api/admin/users` - 这是正常的权限检查，用户没有管理员权限
2. **502 Bad Gateway** - `/api/workflows/v1/*` - `workflow-engine` 服务可能未启动或不可用
3. **500 Internal Server Error** - `/api/tools` - MCP Gateway 工具列表的 Pydantic 验证错误

## 下一步

1. **重启 API Gateway 服务**以应用路由修复：
   ```bash
   # 如果使用 Docker
   docker-compose restart api-gateway
   
   # 或者直接重启
   cd api-gateway && python -m uvicorn src.main:app --reload
   ```

2. **测试动态工作流**：
   - 前端请求 `POST http://localhost:8080/api/v1/dynamic-workflow/execute` 应该能够正常路由
   - 检查 API Gateway 日志，应该看到 "Dynamic workflow routing" 日志

3. **检查其他服务**（如果需要）：
   - 确保 `workflow-engine` 服务正在运行
   - 检查 MCP Gateway 的工具列表 Pydantic 验证错误

## 修复状态

✅ **动态工作流路由已添加**
✅ **重复代码已删除**
✅ **流式支持已配置**

重启 API Gateway 后，动态工作流功能应该可以正常使用！


