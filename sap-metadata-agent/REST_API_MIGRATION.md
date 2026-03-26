# REST API统一方案

## 问题
SAP MCP服务器使用MCP协议和SSE（Server-Sent Events）格式返回数据，导致：
1. SSE响应解析复杂（多行JSON、流式数据）
2. MCP协议需要session管理
3. 错误处理困难

## 解决方案
统一使用REST API，避免MCP协议和SSE解析问题。

## 已添加的REST API端点

### 1. 获取所有服务
```
GET /api/services
```
返回所有已发现的SAP OData服务列表。

**响应格式：**
```json
{
  "success": true,
  "count": 348,
  "services": [
    {
      "id": "service-id",
      "name": "service-name",
      "url": "service-url",
      "description": "service-description",
      "category": "category",
      "entities": [],
      "metadata": {}
    }
  ]
}
```

### 2. 获取服务详情
```
GET /api/services/:serviceId
```
返回指定服务的详细信息。

### 3. 获取服务的实体列表
```
GET /api/services/:serviceId/entities
```
返回指定服务中的所有实体。

### 4. 获取实体结构
```
GET /api/services/:serviceId/entities/:entityName/schema
```
返回指定实体的详细结构信息。

## 代码修改

### SAP MCP服务器 (`sap-odata-to-mcp-server/src/index.ts`)
- ✅ 添加了 `/api/services` 端点
- ✅ 添加了 `/api/services/:serviceId` 端点
- ✅ 添加了 `/api/services/:serviceId/entities` 端点
- ✅ 添加了 `/api/services/:serviceId/entities/:entityName/schema` 端点

### SAP元数据智能体 (`sap-metadata-agent/src/services/sap_mcp_client.py`)
- ✅ 添加了 `_discover_services_rest_api()` 方法
- ✅ 修改了 `discover_services()` 方法，优先使用REST API
- ✅ 修改了 `get_entity_structure()` 方法，优先使用REST API

## 优势

1. **简单可靠**：REST API返回标准JSON，无需解析SSE格式
2. **无session管理**：REST API是无状态的，不需要管理session
3. **易于调试**：可以直接用curl或浏览器测试
4. **向后兼容**：如果REST API失败，会自动回退到MCP协议

## 使用方式

sap-metadata-agent会自动优先使用REST API，如果失败则回退到MCP协议：

```python
# 优先使用REST API
services = await mcp_client.discover_services()  # 自动使用REST API

# 如果REST API失败，自动回退到MCP协议
```

## 测试

```bash
# 测试获取所有服务
curl http://localhost:3001/api/services

# 测试获取服务详情
curl http://localhost:3001/api/services/API_BUSINESS_PARTNER

# 测试获取实体列表
curl http://localhost:3001/api/services/API_BUSINESS_PARTNER/entities

# 测试获取实体结构
curl http://localhost:3001/api/services/API_BUSINESS_PARTNER/entities/A_BusinessPartner/schema
```

## 状态

- ✅ REST API端点已添加
- ✅ sap-metadata-agent已修改为优先使用REST API
- ✅ 向后兼容（失败时回退到MCP协议）
- ⏳ 等待服务重启以加载新代码


