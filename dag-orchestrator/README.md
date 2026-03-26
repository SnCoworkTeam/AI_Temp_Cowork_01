# DAG Orchestrator Service

智能任务分解与编排服务

## 功能特性

- **智能任务分解**: 使用LLM将用户输入的自然语言任务分解为可执行的DAG计划
- **多服务编排**: 协调MCP工具、工作流引擎、知识库等微服务协同工作
- **并行执行**: 支持无依赖任务的并行执行，提高执行效率
- **状态管理**: 完整的执行状态跟踪和监控
- **错误处理**: 优雅的错误处理和重试机制

## 架构设计

```
用户输入 → 任务分解器(LLM) → DAG计划 → DAG引擎 → 后端服务 → 结果聚合
```

## API接口

### 执行复杂任务

```bash
POST /api/v1/tasks/execute
Content-Type: application/json

{
  "user_input": "生成一个MM模块的蓝图设计，包括技术架构、数据库设计、API接口设计",
  "context": {
    "project_type": "backend",
    "complexity": "high"
  },
  "priority": "high"
}
```

### 仅分解任务（不执行）

```bash
POST /api/v1/tasks/decompose
Content-Type: application/json

{
  "user_input": "搜索Python相关文档并生成摘要",
  "context": {}
}
```

### 获取执行状态

```bash
GET /api/v1/executions/{execution_id}
```

## 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8009
DEBUG=true
LOG_LEVEL=info

# 后端服务地址
MCP_GATEWAY_URL=http://mcp-gateway:8001
WORKFLOW_ENGINE_URL=http://workflow-engine:8002
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
CHAT_SERVICE_URL=http://chat-service:8005

# LLM配置（用于智能分解）
OPENAI_API_KEY=your_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 使用示例

### 在AI助手中使用

在聊天对话框中输入：

```
/dag 生成一个MM模块的蓝图设计，包括技术架构、数据库设计、API接口设计
```

系统会：
1. 使用LLM智能分解任务为多个子任务
2. 创建DAG执行计划
3. 按依赖关系执行各个任务节点
4. 聚合结果并返回

### 任务类型

- **mcp_tool**: 调用MCP工具（如GitHub搜索、文件操作等）
- **workflow**: 执行已定义的工作流
- **knowledge**: 从知识库检索信息
- **calculation**: 简单计算或数据处理
- **condition**: 条件判断

## 开发

### 本地开发

```bash
cd dag-orchestrator
pip install -r requirements.txt
python -m src.main
```

### Docker开发

```bash
docker-compose up dag-orchestrator
```

## 部署

服务已集成到 `docker-compose.yml` 中，通过API Gateway访问：

```
http://localhost:8080/api/dag/tasks/execute
```











































