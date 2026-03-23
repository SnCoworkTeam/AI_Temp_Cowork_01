# SAP MCP Server 集成指南

本文档说明如何将 `sap-odata-to-mcp-server` 集成到企业AI平台中。

## 📋 概述

SAP MCP Server 是一个基于 Node.js 的 MCP 服务器，它将 SAP OData 服务暴露为 MCP 工具，使 AI 代理可以通过自然语言与 SAP 系统交互。

### 架构

```
AI Agent → Agent Service → MCP Gateway → SAP MCP Server → SAP System
```

## 🔧 集成步骤

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# SAP MCP Server 配置
SAP_BASE_URL=http://your-sap-server:8000
SAP_CLIENT=810
SAP_USERNAME=your_username
SAP_PASSWORD=your_password
SAP_LANGUAGE=ZH

# MCP Gateway 配置（自动配置，无需手动设置）
# MCP_SERVERS 环境变量会在 docker-compose.yml 中自动设置
```

### 2. Docker Compose 配置

SAP MCP Server 已经添加到 `docker-compose.yml` 中：

```yaml
sap-mcp-server:
  build:
    context: ./sap-odata-to-mcp-server
    dockerfile: Dockerfile
  container_name: enterprise-ai-sap-mcp-server
  ports:
    - "3000:3000"
  environment:
    - SAP_BASE_URL=${SAP_BASE_URL}
    - SAP_CLIENT=${SAP_CLIENT}
    - SAP_USERNAME=${SAP_USERNAME}
    - SAP_PASSWORD=${SAP_PASSWORD}
    - SAP_LANGUAGE=${SAP_LANGUAGE}
  networks:
    - enterprise-ai-network
```

MCP Gateway 会自动连接到 SAP MCP Server：

```yaml
mcp-gateway:
  environment:
    - MCP_SERVERS=[{"name":"sap-mcp-server","url":"http://sap-mcp-server:3000/mcp","transport":"http","timeout":60,"auto_connect":true}]
```

### 3. 启动服务

```bash
# 启动所有服务（包括 SAP MCP Server）
docker-compose up -d

# 或者只启动 SAP MCP Server 和 MCP Gateway
docker-compose up -d sap-mcp-server mcp-gateway
```

### 4. 验证集成

#### 检查 SAP MCP Server 健康状态

```bash
curl http://localhost:3000/health
```

#### 检查 MCP Gateway 是否发现 SAP 工具

```bash
curl http://localhost:8001/api/tools/list | jq '.tools[] | select(.metadata.source | contains("sap"))'
```

#### 查看 MCP Gateway 日志

```bash
docker logs enterprise-ai-mcp-gateway | grep -i sap
```

## 📝 MCP 服务器配置格式

MCP Gateway 支持两种传输方式：

### WebSocket 传输

```json
{
  "name": "websocket-mcp-server",
  "url": "ws://mcp-server:8080",
  "transport": "websocket",
  "timeout": 30,
  "auto_connect": true
}
```

### HTTP 传输（SAP MCP Server 使用）

```json
{
  "name": "sap-mcp-server",
  "url": "http://sap-mcp-server:3000/mcp",
  "transport": "http",
  "timeout": 60,
  "auto_connect": true
}
```

### 自动检测传输类型

如果不指定 `transport`，系统会根据 URL 协议自动检测：

- `ws://` 或 `wss://` → WebSocket
- `http://` 或 `https://` → HTTP

## 🛠️ 技术实现

### HTTP MCP 客户端

MCP Gateway 新增了 `MCPHTTPClient` 类（`mcp-gateway/src/core/mcp_http_client.py`），用于连接使用 HTTP SSE 传输的 MCP 服务器。

主要特性：
- 支持 Streamable HTTP 传输
- 自动会话管理
- 工具发现和执行
- 健康检查

### 连接池增强

`MCPConnectionPool` 现在支持同时管理 WebSocket 和 HTTP 客户端：

```python
# 自动检测传输类型
pool.add_server({
    "name": "sap-mcp-server",
    "url": "http://sap-mcp-server:3000/mcp",
    "transport": "auto"  # 自动检测
})
```

## 🧪 测试

### 测试 SAP 工具发现

```bash
# 通过 MCP Gateway API 列出所有工具
curl http://localhost:8001/api/tools/list

# 过滤 SAP 工具
curl http://localhost:8001/api/tools/list | jq '.tools[] | select(.name | contains("sap") or contains("SAP"))'
```

### 测试工具执行

```bash
# 执行 SAP 工具（示例）
curl -X POST http://localhost:8001/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "r-BankService-Bank",
    "parameters": {
      "$top": 10
    }
  }'
```

## 🔍 故障排查

### SAP MCP Server 无法连接

1. **检查容器状态**
   ```bash
   docker ps | grep sap-mcp-server
   ```

2. **查看日志**
   ```bash
   docker logs enterprise-ai-sap-mcp-server
   ```

3. **检查网络连接**
   ```bash
   docker exec enterprise-ai-mcp-gateway curl http://sap-mcp-server:3000/health
   ```

### MCP Gateway 无法发现 SAP 工具

1. **检查 MCP_SERVERS 配置**
   ```bash
   docker exec enterprise-ai-mcp-gateway printenv | grep MCP_SERVERS
   ```

2. **查看 MCP Gateway 启动日志**
   ```bash
   docker logs enterprise-ai-mcp-gateway | grep -i "sap\|mcp"
   ```

3. **手动测试连接**
   ```bash
   docker exec enterprise-ai-mcp-gateway python -c "
   import asyncio
   from src.core.mcp_http_client import MCPHTTPClient
   
   async def test():
       client = MCPHTTPClient('http://sap-mcp-server:3000/mcp', 30, 'test')
       if await client.connect():
           tools = await client.discover_tools()
           print(f'Found {len(tools)} tools')
       await client.close()
   
   asyncio.run(test())
   "
   ```

## 📚 相关文档

- [SAP MCP Server README](../sap-odata-to-mcp-server/README.md)
- [MCP Gateway README](../mcp-gateway/README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## 🎯 使用示例

### 通过 Agent Service 使用 SAP 工具

当用户发送自然语言请求时，Agent Service 的 OrchestrationEngine 会自动：

1. 分析用户意图
2. 识别需要 SAP 工具
3. 通过 MCP Gateway 调用 SAP 工具
4. 返回结果

示例对话：
```
用户: "查询前10个银行信息"
→ Agent Service 识别需要查询 SAP 数据
→ 调用 MCP Gateway 的 SAP 工具
→ 返回银行列表
```

## 🔐 安全注意事项

1. **凭证管理**：SAP 凭证存储在环境变量中，确保 `.env` 文件不被提交到版本控制
2. **网络隔离**：SAP MCP Server 仅在 Docker 网络内可访问
3. **权限控制**：SAP MCP Server 支持基于用户的权限控制

## 📞 支持

如有问题，请查看：
- SAP MCP Server 日志：`docker logs enterprise-ai-sap-mcp-server`
- MCP Gateway 日志：`docker logs enterprise-ai-mcp-gateway`
- 系统文档：`SYSTEM_EXECUTION_CHAIN.md`






























