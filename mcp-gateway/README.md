# MCP Gateway 服务

企业AI平台的MCP工具网关服务，提供统一的工具注册、发现和执行接口。

## 功能特性

- 🔧 **工具注册**: 动态注册MCP工具，支持多种工具类型
- 📋 **工具发现**: 查询和列出可用工具，支持分类和标签过滤
- ⚡ **工具执行**: 执行工具并返回结果，支持异步执行
- 📊 **工具监控**: 工具执行统计和性能监控
- 🔍 **工具配置**: 工具配置管理和版本控制
- 📈 **健康检查**: 服务状态监控和就绪检查

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL (通过database模块)
- **缓存**: Redis
- **Python版本**: 3.11+

## API端点

### 工具管理

- `POST /api/tools/register` - 注册新工具
- `GET /api/tools` - 获取工具列表（支持分页、过滤、搜索）
- `GET /api/tools/{name}` - 获取工具详情
- `PUT /api/tools/{name}` - 更新工具配置
- `POST /api/tools/{name}/execute` - 执行工具
- `DELETE /api/tools/{name}` - 注销工具

### 工具配置管理

- `GET /api/tool-config` - 获取工具配置列表
- `GET /api/tool-config/{tool_name}` - 获取工具配置
- `PUT /api/tool-config/{tool_name}` - 更新工具配置
- `DELETE /api/tool-config/{tool_name}` - 删除工具配置

### 工具监控

- `GET /api/tool-monitoring/stats` - 获取工具统计信息
- `GET /api/tool-monitoring/executions` - 获取工具执行历史
- `GET /api/tool-monitoring/performance` - 获取工具性能指标

### 监控

- `GET /api/monitoring/stats` - 获取API统计信息
- `GET /api/monitoring/health` - 获取服务健康状态

### 健康检查

- `GET /api/health` - 健康检查
- `GET /api/health/ready` - 就绪检查
- `GET /api/health/live` - 存活检查

## 配置

### 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8001
DEBUG=false

# CORS配置（逗号分隔）
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 工作流引擎配置
WORKFLOW_ENGINE_URL=http://workflow-engine:8002

# 知识库服务配置
KNOWLEDGE_BASE_URL=http://knowledge-base:8004

# 元数据服务配置
METADATA_SERVICE_URL=http://metadata-service:8005

# MCP服务器配置（JSON格式）
# 示例: [{"name": "weather_mcp", "url": "ws://localhost:8080/mcp", "timeout": 30, "auto_connect": true}]
MCP_SERVERS=[]

# 工具自动刷新配置
AUTO_REFRESH_TOOLS=true
TOOL_REFRESH_INTERVAL=300

# MCP连接池配置
MCP_CONNECTION_POOL_SIZE=5
MCP_MAX_RETRIES=3

# 日志配置
LOG_LEVEL=info  # 注意：uvicorn需要小写
```

## 使用示例

### 1. 注册工具

```bash
curl -X POST "http://localhost:8001/api/tools/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "query_database",
    "display_name": "查询数据库",
    "description": "执行SQL查询",
    "tool_type": "database",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "SQL查询语句"
        }
      },
      "required": ["query"]
    },
    "required_parameters": ["query"]
  }'
```

### 2. 获取工具列表

```bash
curl -X GET "http://localhost:8001/api/tools?page=1&page_size=20&tool_type=database"
```

### 3. 执行工具

```bash
curl -X POST "http://localhost:8001/api/tools/query_database/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "query": "SELECT * FROM users LIMIT 10"
    }
  }'
```

### 4. 获取工具详情

```bash
curl -X GET "http://localhost:8001/api/tools/query_database"
```

## 开发

### 本地运行

```bash
cd mcp-gateway
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

### Docker开发

```bash
# 构建开发镜像
docker build -f Dockerfile.dev -t mcp-gateway:dev .

# 运行容器
docker run -p 8001:8001 -v $(pwd):/app mcp-gateway:dev
```

### Docker Compose

```bash
# 启动服务
docker-compose up mcp-gateway

# 查看日志
docker-compose logs -f mcp-gateway
```

## 工具类型

支持以下工具类型：

- `database` - 数据库操作工具
- `api` - API调用工具
- `file` - 文件操作工具
- `workflow` - 工作流工具
- `custom` - 自定义工具

## 工具执行流程

1. **工具注册**: 通过 `POST /api/tools/register` 注册工具定义
2. **工具发现**: 通过 `GET /api/tools` 查询可用工具
3. **工具执行**: 通过 `POST /api/tools/{name}/execute` 执行工具
4. **结果返回**: 返回执行结果和元数据

## 数据库集成

服务使用 `database` 模块进行数据持久化：

- **MCPTool**: 工具配置和元数据
- **MCPToolExecution**: 工具执行历史记录

## 监控和日志

- 所有API请求都会记录日志
- 工具执行统计存储在数据库中
- 支持通过监控端点查询统计信息

## 依赖

主要依赖项：
- `fastapi>=0.104.1` - Web框架
- `uvicorn[standard]>=0.24.0` - ASGI服务器
- `pydantic>=2.5.0` - 数据验证
- `redis>=5.0.1` - Redis客户端
- `httpx>=0.25.2` - HTTP客户端
- `cryptography>=41.0.0` - 加密库

## 端口说明

⚠️ **注意**: 默认使用端口 **8001**。确保该端口未被其他服务占用。

## 相关文档

- [项目主文档](../../README.md)
- [数据库模块文档](../database/README.md)
- [共享库文档](../shared_libs/README.md)
- [API文档](../../docs/api-docs/README.md)

