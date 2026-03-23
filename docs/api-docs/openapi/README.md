# OpenAPI规范

本目录包含各服务的OpenAPI规范文件。

## 文件说明

- `mcp-gateway-openapi.json` - MCP Gateway API规范
- `workflow-engine-openapi.json` - Workflow Engine API规范
- `auth-service-openapi.json` - Auth Service API规范
- `knowledge-base-openapi.json` - Knowledge Base API规范

## 生成方式

OpenAPI规范由FastAPI自动生成，运行以下命令更新：

```bash
python scripts/docs/generate-api-docs.py
```

## 查看文档

### Swagger UI
访问各服务的 `/api/docs` 端点查看交互式API文档。

### 使用工具
- **Postman**: 导入JSON文件
- **Insomnia**: 导入JSON文件
- **Redoc**: 生成HTML文档

## 版本管理

OpenAPI规范版本与代码版本同步，通过Git标签管理。









