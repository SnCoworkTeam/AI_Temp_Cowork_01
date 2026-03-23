# 提示词API路由修复

## 问题
前端访问 `http://localhost:8080/api/v1/prompts` 返回404错误。

## 原因
API Gateway中没有配置`/api/v1/prompts`路由，导致请求无法转发到agent-service。

## 修复内容

### 1. API Gateway路由添加
**文件**：`api-gateway/src/main.py`

添加了`/api/v1/prompts`路由，将请求转发到agent-service：

```python
# Agent Service - /api/v1/prompts 路由（提示词管理，必须在 /api/v1/agents 之前注册）
@app.api_route("/api/v1/prompts", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/prompts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def prompts_service_proxy(request: Request, path: str = ""):
    """提示词管理服务代理 - /api/v1/prompts 路由"""
    logger.info(f"Prompts routing: {request.method} {request.url.path} -> agent-service:/api/v1/prompts/{path if path else ''}")
    
    return await gateway_proxy.forward_request(
        request=request,
        service_name="agent-service",
        path=f"/api/v1/prompts/{path}" if path else "/api/v1/prompts"
    )
```

### 2. 修复metadata字段问题
**文件**：`agent-service/src/routes/prompts.py`

- 修复了`create_prompt`中的metadata字段：使用`metadata_`而不是`metadata`
- 修复了`update_prompt`中的metadata字段转换
- 修复了`list_prompts`和`get_prompt`中的响应转换，确保metadata_正确转换为metadata

## API端点

现在可以通过以下端点访问提示词API：

- `GET /api/v1/prompts` - 列出所有提示词模板
- `GET /api/v1/prompts/{prompt_id}` - 获取单个提示词模板
- `POST /api/v1/prompts` - 创建新的提示词模板
- `PUT /api/v1/prompts/{prompt_id}` - 更新提示词模板
- `DELETE /api/v1/prompts/{prompt_id}` - 删除提示词模板
- `GET /api/v1/prompts/categories/list` - 获取所有任务分类列表

## 测试

重启API Gateway和agent-service后，前端应该能够正常访问提示词API。

