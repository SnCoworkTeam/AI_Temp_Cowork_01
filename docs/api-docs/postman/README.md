# Postman集合

本目录包含各服务的Postman API集合。

## 文件说明

- `mcp-gateway-postman.json` - MCP Gateway API集合
- `workflow-engine-postman.json` - Workflow Engine API集合
- `auth-service-postman.json` - Auth Service API集合
- `knowledge-base-postman.json` - Knowledge Base API集合

## 使用方法

### 导入Postman

1. 打开Postman
2. 点击 "Import"
3. 选择JSON文件
4. 集合将自动导入

### 配置环境变量

在Postman中创建环境，设置以下变量：

- `base_url`: 服务基础URL
- `auth_token`: 认证Token

### 使用示例

1. 导入集合
2. 设置环境变量
3. 先调用登录接口获取token
4. 使用token调用其他API

## 生成方式

Postman集合从OpenAPI规范自动生成：

```bash
python scripts/docs/generate-api-docs.py
```









