# API参考文档

企业AI平台所有服务的完整API参考文档。

## 目录

- [MCP Gateway API](#mcp-gateway-api)
- [Workflow Engine API](#workflow-engine-api)
- [Auth Service API](#auth-service-api)
- [Knowledge Base API](#knowledge-base-api)
- [Metadata Service API](#metadata-service-api)
- [通用响应格式](#通用响应格式)
- [错误处理](#错误处理)

## MCP Gateway API

**基础URL**: `http://localhost:8001`  
**文档**: http://localhost:8001/api/docs

### 工具管理

#### 注册工具

```http
POST /api/tools/register
Content-Type: application/json

{
  "name": "tool_name",
  "display_name": "工具显示名称",
  "description": "工具描述",
  "tool_type": "database",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "参数描述"
      }
    },
    "required": ["param1"]
  },
  "required_parameters": ["param1"]
}
```

#### 获取工具列表

```http
GET /api/tools?page=1&page_size=20&tool_type=database
```

#### 获取工具详情

```http
GET /api/tools/{tool_name}
```

#### 执行工具

```http
POST /api/tools/{tool_name}/execute
Content-Type: application/json

{
  "parameters": {
    "param1": "value1"
  }
}
```

#### 删除工具

```http
DELETE /api/tools/{tool_name}
```

### 工具配置管理

#### 获取工具配置

```http
GET /api/tool-config/{tool_name}
```

#### 更新工具配置

```http
PUT /api/tool-config/{tool_name}
Content-Type: application/json

{
  "config": {
    "key": "value"
  }
}
```

### 健康检查

```http
GET /api/health
GET /api/health/ready
GET /api/health/live
```

## Workflow Engine API

**基础URL**: `http://localhost:8002`  
**文档**: http://localhost:8002/api/docs

### 工作流管理

#### 创建工作流

```http
POST /api/workflows
Content-Type: application/json

{
  "name": "工作流名称",
  "description": "工作流描述",
  "nodes": [...],
  "connections": [...]
}
```

#### 获取工作流列表

```http
GET /api/workflows?page=1&page_size=20
```

#### 获取工作流详情

```http
GET /api/workflows/{workflow_id}
```

#### 更新工作流

```http
PUT /api/workflows/{workflow_id}
Content-Type: application/json

{
  "name": "更新后的名称",
  "nodes": [...],
  "connections": [...]
}
```

#### 删除工作流

```http
DELETE /api/workflows/{workflow_id}
```

### 工作流执行

#### 执行工作流

```http
POST /api/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "input_data": {
    "key": "value"
  },
  "context": {
    "user_id": "user123"
  }
}
```

#### 获取执行状态

```http
GET /api/executions/{execution_id}
```

#### 获取执行历史

```http
GET /api/executions?page=1&page_size=20
```

### 健康检查

```http
GET /api/health
GET /api/health/ready
GET /api/health/live
```

## Auth Service API

**基础URL**: `http://localhost:8003`  
**文档**: http://localhost:8003/api/docs

### 用户注册和登录

#### 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePassword123!",
  "full_name": "Test User"
}
```

**响应**:
```json
{
  "user_id": "uuid",
  "username": "testuser",
  "email": "test@example.com",
  "message": "用户注册成功"
}
```

#### 用户名密码登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "SecurePassword123!"
}
```

**响应**:
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "username": "testuser",
    "email": "test@example.com",
    "roles": ["user"]
  },
  "session_id": "session_uuid"
}
```

**注意**: 支持使用用户名或邮箱登录

#### 刷新访问令牌

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token"
}
```

#### 修改密码

```http
POST /api/auth/change-password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!"
}
```

#### 登出

```http
POST /api/auth/logout
Authorization: Bearer {access_token}
```

#### 获取用户会话列表

```http
GET /api/auth/sessions
Authorization: Bearer {access_token}
```

#### 撤销会话

```http
DELETE /api/auth/sessions/{session_id}
Authorization: Bearer {access_token}
```

### 认证端点

#### SSO登录

```http
GET /auth/sso/login
```

#### SSO回调

```http
GET /auth/sso/callback?code={code}&state={state}
```

#### 刷新令牌

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

#### 登出

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

### 用户端点

#### 获取当前用户

```http
GET /users/me
Authorization: Bearer {access_token}
```

### 健康检查

```http
GET /health
GET /health/ready
GET /health/live
```

## Knowledge Base API

**基础URL**: `http://localhost:8004`  
**文档**: http://localhost:8004/api/docs

### 文档管理

#### 上传文档

```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: (binary)
tags: "tag1,tag2"
process_async: true
```

#### 获取文档列表

```http
GET /api/documents?page=1&page_size=20&tags=tag1
```

#### 获取文档详情

```http
GET /api/documents/{document_id}
```

#### 删除文档

```http
DELETE /api/documents/{document_id}
```

### 搜索功能

#### 语义搜索

```http
POST /api/search/semantic
Content-Type: application/json

{
  "query": "搜索查询",
  "top_k": 10,
  "min_score": 0.5
}
```

#### 关键词搜索

```http
POST /api/search/keyword
Content-Type: application/json

{
  "keywords": ["关键词1", "关键词2"],
  "match_all": false,
  "page": 1,
  "page_size": 20
}
```

### 健康检查

```http
GET /api/health
GET /api/health/ready
GET /api/health/live
```

## Metadata Service API

**基础URL**: `http://localhost:8005`  
**文档**: http://localhost:8005/api/docs

### 数据资产

#### 创建数据资产

```http
POST /api/data-assets
Content-Type: application/json

{
  "name": "asset_name",
  "display_name": "资产显示名称",
  "description": "资产描述",
  "asset_type": "table",
  "source_system": "CRM",
  "tags": ["tag1", "tag2"]
}
```

#### 获取数据资产列表

```http
GET /api/data-assets?page=1&page_size=20
```

#### 获取数据资产详情

```http
GET /api/data-assets/{asset_id}
```

### 搜索

#### 全局搜索

```http
GET /api/search?q=query&entity_types=data_asset
```

#### 标签搜索

```http
GET /api/search/tags?tags=tag1,tag2
```

### 数据血缘

#### 创建血缘关系

```http
POST /api/lineage
Content-Type: application/json

{
  "source_type": "data_asset",
  "source_id": "1",
  "target_type": "workflow",
  "target_id": "workflow_123",
  "relation_type": "reads"
}
```

#### 获取上游血缘

```http
GET /api/lineage/upstream/{type}/{id}?max_depth=5
```

#### 获取下游血缘

```http
GET /api/lineage/downstream/{type}/{id}?max_depth=5
```

### 数据质量

#### 更新质量指标

```http
PUT /api/quality/assets/{id}/metrics
Content-Type: application/json

{
  "quality_score": 0.95,
  "completeness": 0.98,
  "accuracy": 0.92
}
```

#### 获取质量指标

```http
GET /api/quality/metrics/{asset_id}
```

### 健康检查

```http
GET /api/health
GET /api/health/ready
GET /api/health/live
```

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "message": "错误消息",
    "status_code": 400,
    "details": "错误详情"
  }
}
```

### HTTP状态码

- `200 OK` - 请求成功
- `201 Created` - 创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未授权
- `403 Forbidden` - 禁止访问
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器错误

## 认证

### Bearer Token

大多数API端点需要Bearer Token认证：

```http
Authorization: Bearer {access_token}
```

### 获取Token

通过Auth Service的SSO登录流程获取访问令牌。

## 相关文档

- [各服务README](../README.md)
- [环境变量配置](../development-docs/environment-variables.md)
- [快速开始指南](../development-docs/QUICK_START.md)

