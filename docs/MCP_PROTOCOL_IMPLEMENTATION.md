# MCP协议实现说明

## 概述

MCP Gateway现在同时支持两种接口风格：

1. **标准MCP协议** (`POST /mcp`) - 符合MCP（Model Context Protocol）标准，支持JSON-RPC 2.0和SSE格式
2. **RESTful API** (`/api/tools/*`) - 简化的REST接口，便于直接调用

## MCP标准协议

### 端点
- **URL**: `POST /mcp`
- **Content-Type**: `application/json`
- **Accept**: `application/json` 或 `text/event-stream`（SSE格式）

### 协议格式

MCP使用JSON-RPC 2.0协议，请求格式：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

响应格式（JSON）：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

响应格式（SSE）：
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

### 支持的方法

1. **initialize** - 初始化会话
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "initialize",
     "params": {
       "protocolVersion": "2024-11-05",
       "capabilities": {},
       "clientInfo": {
         "name": "client-name",
         "version": "1.0.0"
       }
     }
   }
   ```
   响应头包含 `mcp-session-id`，后续请求需要携带此会话ID。

2. **initialized** - 确认初始化完成（通知，无需响应）
   ```json
   {
     "jsonrpc": "2.0",
     "method": "initialized"
   }
   ```
   请求头需要包含 `mcp-session-id`。

3. **tools/list** - 列出所有可用工具
   ```json
   {
     "jsonrpc": "2.0",
     "id": 2,
     "method": "tools/list",
     "params": {}
   }
   ```

4. **tools/call** - 调用工具
   ```json
   {
     "jsonrpc": "2.0",
     "id": 3,
     "method": "tools/call",
     "params": {
       "name": "sap_query",
       "arguments": {
         "table": "I_SalesOrder",
         "$top": 10
       }
     }
   }
   ```

### 会话管理

- `initialize` 请求会创建新会话，响应头包含 `mcp-session-id`
- 后续请求需要在请求头中携带 `mcp-session-id: <session-id>`
- 会话存储在内存中（生产环境应使用Redis或数据库）

## RESTful API（简化接口）

保留原有的RESTful API接口，便于直接调用：

- `GET /api/tools` - 获取工具列表
- `GET /api/tools/{name}` - 获取工具详情
- `POST /api/tools/{name}/execute` - 执行工具
- `POST /api/tools/register` - 注册工具

## 使用场景

### 使用MCP协议的场景

1. **MCP客户端连接** - 标准的MCP客户端（如Claude Desktop、其他MCP工具）可以直接连接
2. **流式响应** - 需要SSE格式的流式响应时
3. **标准化集成** - 需要符合MCP标准的集成场景

### 使用RESTful API的场景

1. **简单调用** - 不需要会话管理的简单工具调用
2. **Web应用** - 前端直接调用，无需处理MCP协议
3. **快速集成** - 快速集成到现有系统

## 测试示例

### 使用curl测试MCP协议

```bash
# 1. 初始化会话
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

# 响应头包含 mcp-session-id，例如：abc-123-def

# 2. 列出工具（使用会话ID）
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: abc-123-def" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# 3. 调用工具
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: abc-123-def" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "sap_query",
      "arguments": {
        "table": "I_SalesOrder",
        "$top": 10
      }
    }
  }'
```

### 使用SSE格式

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

## 优势

1. **符合MCP标准** - 实现了标准的MCP协议，可以被标准MCP客户端连接
2. **向后兼容** - 保留了RESTful API，不影响现有调用
3. **灵活性** - 支持JSON和SSE两种响应格式
4. **标准化** - 使用JSON-RPC 2.0标准协议

## 注意事项

1. **会话管理** - 当前使用内存存储会话，生产环境应使用Redis或数据库
2. **错误处理** - 遵循JSON-RPC 2.0错误码规范
3. **超时处理** - 工具执行超时遵循MCP协议规范

