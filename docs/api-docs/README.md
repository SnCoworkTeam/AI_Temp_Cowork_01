# API文档

本目录包含完整的API文档，包括OpenAPI规范、Postman集合和使用示例。

## 目录结构

- **openapi/**: OpenAPI 3.0规范文件
- **postman/**: Postman API集合
- **examples/**: 使用示例代码

## 服务API文档

### MCP Gateway
- **端口**: 8001
- **文档**: http://localhost:8001/api/docs
- **OpenAPI**: [openapi/mcp-gateway-openapi.json](./openapi/mcp-gateway-openapi.json)
- **服务文档**: [../../mcp-gateway/README.md](../../mcp-gateway/README.md)

### Workflow Engine
- **端口**: 8002
- **文档**: http://localhost:8002/api/docs
- **OpenAPI**: [openapi/workflow-engine-openapi.json](./openapi/workflow-engine-openapi.json)
- **服务文档**: [../../workflow-engine/README.md](../../workflow-engine/README.md)

### Auth Service
- **端口**: 8003
- **文档**: http://localhost:8003/api/docs
- **OpenAPI**: [openapi/auth-service-openapi.json](./openapi/auth-service-openapi.json)
- **服务文档**: [../../auth-service/README.md](../../auth-service/README.md)

### Knowledge Base
- **端口**: 8004
- **文档**: http://localhost:8004/api/docs
- **OpenAPI**: [openapi/knowledge-base-openapi.json](./openapi/knowledge-base-openapi.json)
- **服务文档**: [../../knowledge-base/README.md](../../knowledge-base/README.md)

### Metadata Service
- **端口**: 8005
- **文档**: http://localhost:8005/api/docs
- **OpenAPI**: [openapi/metadata-service-openapi.json](./openapi/metadata-service-openapi.json)
- **服务文档**: [../../metadata-service/README.md](../../metadata-service/README.md)

## 使用示例

### Python示例
参见 [examples/python-examples.py](./examples/python-examples.py)

### cURL示例
参见 [examples/curl-examples.sh](./examples/curl-examples.sh)

## 生成文档

运行以下命令生成API文档：

```bash
python scripts/docs/generate-api-docs.py
```

## 文档要求

- 所有公共API必须有文档字符串
- 所有端点必须在OpenAPI规范中定义
- 参数和返回值必须有类型注解
- 错误响应必须有文档说明







