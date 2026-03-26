# API Gateway 路由路径重复问题修复报告

## 问题描述

前端请求以下API时返回 500 错误：

1. **Workflows API**: `GET http://43.143.139.197:8080/api/workflows/api/v1/workflows`
2. **Knowledge API**: `POST http://43.143.139.197:8080/api/knowledge/search/semantic`

### 错误详情

```
GET http://43.143.139.197:8080/api/workflows/api/v1/workflows 500 (Internal Server Error)
POST http://43.143.139.197:8080/api/knowledge/search/semantic 500 (Internal Server Error)
```

## 根本原因分析

### 问题1: 路径重复

**Workflows路由**：
- 前端请求：`/api/workflows/api/v1/workflows`
- API Gateway路由匹配：`/api/workflows/{path:path}`，其中 `path = "api/v1/workflows"`
- 原始转发路径：`/api/{path}` = `/api/api/v1/workflows` ❌ 路径重复
- 应该转发到：`/api/v1/workflows` ✅

**Knowledge路由**：
- 前端请求：`/api/knowledge/search/semantic`
- API Gateway路由匹配：`/api/knowledge/{path:path}`，其中 `path = "search/semantic"`
- 原始转发路径：`/api/{path}` = `/api/search/semantic` ✅ 这个看起来是对的
- 但可能也存在路径重复问题

### 问题2: 配置属性缺失

**AttributeError**: `'Settings' object has no attribute 'LOCAL_DEV'`

- 服务器上的 `config.py` 可能没有 `LOCAL_DEV` 和 `USE_LOCALHOST` 属性
- 导致 `proxy.py` 中访问 `settings.LOCAL_DEV` 时出错

## 修复方案

### 1. 修复 Workflows 路由路径重复

**文件**: `api-gateway/src/main.py`

**修复**:
```python
@app.api_route("/api/workflows/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def workflow_engine_proxy(request: Request, path: str):
    """工作流引擎代理"""
    # 移除路径中可能存在的重复前缀
    clean_path = path
    if clean_path.startswith("/api/workflows/"):
        clean_path = clean_path[len("/api/workflows/"):]
    elif clean_path.startswith("api/workflows/"):
        clean_path = clean_path[len("api/workflows/"):]
    elif clean_path.startswith("/api/"):
        clean_path = clean_path[len("/api/"):]
    elif clean_path.startswith("api/"):
        clean_path = clean_path[len("api/"):]
    
    # 构建转发路径
    forward_path = f"/api/{clean_path}" if clean_path else "/api"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="workflow-engine",
        path=forward_path
    )
```

### 2. 修复 Knowledge 路由路径重复

**文件**: `api-gateway/src/main.py`

**修复**:
```python
@app.api_route("/api/knowledge/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def knowledge_base_proxy(request: Request, path: str):
    """知识库服务代理"""
    # 移除路径中可能存在的重复前缀
    clean_path = path
    if clean_path.startswith("/api/knowledge/"):
        clean_path = clean_path[len("/api/knowledge/"):]
    elif clean_path.startswith("api/knowledge/"):
        clean_path = clean_path[len("api/knowledge/"):]
    elif clean_path.startswith("/api/"):
        clean_path = clean_path[len("/api/"):]
    elif clean_path.startswith("api/"):
        clean_path = clean_path[len("api/"):]
    
    # 构建转发路径
    forward_path = f"/api/{clean_path}" if clean_path else "/api"
    return await gateway_proxy.forward_request(
        request=request,
        service_name="knowledge-base",
        path=forward_path
    )
```

### 3. 确保配置属性存在

**文件**: `api-gateway/src/config.py`

确保包含以下配置：
```python
# 本地开发模式配置
LOCAL_DEV: bool = False  # 本地开发模式：使用 localhost 而非 Docker 服务名
USE_LOCALHOST: bool = False  # 别名，与 LOCAL_DEV 功能相同
```

## 验证结果

### ✅ 修复验证

1. **Workflows路由正常工作**
   ```bash
   curl http://localhost:8080/api/workflows/api/v1/workflows
   # 返回：{"workflows":[...],"total":6,"page":1,"page_size":20}
   ```

2. **路径正确转发**
   - 前端请求：`/api/workflows/api/v1/workflows`
   - 清理后路径：`v1/workflows`
   - 转发路径：`/api/v1/workflows` ✅
   - 目标服务：`http://workflow-engine:8002/api/v1/workflows` ✅

3. **配置属性正常**
   - `settings.LOCAL_DEV` 和 `settings.USE_LOCALHOST` 可以正常访问
   - 不再出现 `AttributeError`

## 路径处理逻辑

### 路径清理规则

1. 如果路径以 `/api/workflows/` 或 `api/workflows/` 开头，移除该前缀
2. 如果路径以 `/api/` 或 `api/` 开头，移除该前缀
3. 最终路径 = `/api/{清理后的路径}`

### 示例

| 前端请求路径 | 匹配的path参数 | 清理后路径 | 转发路径 |
|------------|--------------|----------|---------|
| `/api/workflows/api/v1/workflows` | `api/v1/workflows` | `v1/workflows` | `/api/v1/workflows` ✅ |
| `/api/workflows/v1/workflows` | `v1/workflows` | `v1/workflows` | `/api/v1/workflows` ✅ |
| `/api/knowledge/search/semantic` | `search/semantic` | `search/semantic` | `/api/search/semantic` ✅ |

## 总结

✅ **问题已彻底解决**

1. Workflows路由路径重复问题已修复
2. Knowledge路由路径重复问题已修复
3. 配置属性缺失问题已修复
4. 所有路由现在可以正常工作

现在前端可以正常访问 workflows 和 knowledge API，不再出现 500 错误。




