# 智能路由功能文档

## 📋 概述

API Gateway 的智能路由功能可以根据请求内容自动选择最佳的后端服务，实现基于意图的路由决策。

## 🎯 功能特性

### ✅ 已实现的功能

1. **基础静态路由** - 基于路径前缀的路由映射
2. **智能体路由** - 支持 `/api/agents/*`, `/api/orchestrate/*`, `/api/agent-registry/*`
3. **智能路由决策** - 基于请求内容的动态路由
4. **意图识别** - 支持规则匹配和LLM两种模式
5. **服务发现集成** - 与Registry Service集成，动态发现服务

### 🔄 路由决策流程

```
用户请求
    ↓
判断请求类型
    ↓
┌─────────────────┬─────────────────┐
│   API路径路由    │   内容智能路由   │
│  (静态路由)      │  (动态路由)      │
└─────────────────┴─────────────────┘
    ↓                    ↓
服务发现             意图分析
    ↓                    ↓
转发到目标服务        路由到最佳服务
```

## 🛣️ 路由配置

### 静态路由映射

| 路径前缀 | 目标服务 | 端口 | 说明 |
|---------|---------|------|------|
| `/api/workflows/*` | workflow-engine | 8002 | 工作流引擎 |
| `/api/mcp/*` | mcp-gateway | 8001 | MCP网关 |
| `/api/auth/*` | auth-service | 8003 | 认证服务 |
| `/api/knowledge/*` | knowledge-base | 8004 | 知识库 |
| `/api/metadata/*` | metadata-service | 8005 | 元数据服务 |
| `/api/chat/*` | chat-service | 8006 | 对话服务 |
| `/api/dag/*` | dag-orchestrator | 8009 | DAG编排器 |
| `/api/agents/*` | agent-service | 8010 | 智能体服务 |
| `/api/orchestrate/*` | agent-orchestrator | 8011 | 智能体编排器 |
| `/api/agent-registry/*` | agent-registry | 8012 | 智能体注册中心 |
| `/api/joyagent/*` | joyagent-adapter | 8007 | JoyAgent适配器 |
| `/api/registry/*` | registry-service | 8000 | 服务注册中心 |

### 智能路由端点

#### `/api/chat/intelligent` (POST)

智能路由对话端点，根据请求内容自动路由到最佳服务。

**请求示例：**
```json
{
  "message": "帮我执行一个数据分析任务",
  "conversation_id": "optional-conversation-id"
}
```

**路由决策逻辑：**

| 意图类型 | 关键词/特征 | 目标服务 | 转发路径 |
|---------|------------|---------|---------|
| 简单对话 | 普通聊天、问答 | chat-service | `/api/chat` |
| 工具执行 | "执行"、"调用"、"工具" | agent-service | `/api/v1/chat` |
| 工作流任务 | "工作流"、"流程"、"pipeline" | workflow-engine | `/api/v1/workflows/execute` |
| 智能体任务 | "智能体"、"agent"、"复杂任务" | agent-service | `/api/v1/chat` |
| 数据分析 | "分析数据"、"统计"、"报表" | dag-orchestrator | `/api/v1/dag/execute` |
| 知识搜索 | "搜索"、"查找"、"知识库" | knowledge-base | `/api/search` |

## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# 智能路由配置
INTELLIGENT_ROUTING_ENABLED=true
INTELLIGENT_ROUTER_USE_LLM=false  # 是否使用LLM进行意图识别

# LLM配置（如果启用LLM模式）
OPENAI_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 配置选项

- **INTELLIGENT_ROUTING_ENABLED**: 是否启用智能路由（默认: `true`）
- **INTELLIGENT_ROUTER_USE_LLM**: 是否使用LLM进行意图识别（默认: `false`）
  - `false`: 使用规则匹配（快速，无需API调用）
  - `true`: 使用LLM分析（更准确，但需要API调用）

## 📝 使用示例

### 示例1: 简单对话

```bash
curl -X POST http://localhost:8080/api/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，今天天气怎么样？"
  }'
```

**路由结果**: `chat-service` → `/api/chat`

### 示例2: 工具执行请求

```bash
curl -X POST http://localhost:8080/api/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行一个API调用，获取用户信息"
  }'
```

**路由结果**: `agent-service` → `/api/v1/chat`

### 示例3: 工作流任务

```bash
curl -X POST http://localhost:8080/api/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "创建一个数据处理工作流"
  }'
```

**路由结果**: `workflow-engine` → `/api/v1/workflows/execute`

### 示例4: 数据分析任务

```bash
curl -X POST http://localhost:8080/api/chat/intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析一下最近一个月的销售数据"
  }'
```

**路由结果**: `dag-orchestrator` → `/api/v1/dag/execute`

## 🔍 意图识别机制

### 规则匹配模式（默认）

使用关键词和正则表达式进行快速匹配：

- **优点**: 快速、无需API调用、无成本
- **缺点**: 准确性相对较低，需要维护关键词列表
- **适用场景**: 生产环境，高并发场景

### LLM模式（可选）

使用大语言模型进行意图分析：

- **优点**: 准确性高，能理解上下文和语义
- **缺点**: 需要API调用，有延迟和成本
- **适用场景**: 对准确性要求高的场景

## 🎨 架构设计

```
┌─────────────────────────────────────────┐
│         API Gateway                     │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   IntelligentRoutingMiddleware    │  │
│  │   (智能路由中间件)                  │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │   IntelligentRouter               │  │
│  │   (智能路由决策器)                  │  │
│  │                                    │  │
│  │  ┌────────────┐  ┌─────────────┐ │  │
│  │  │ 规则匹配   │  │  LLM分析    │ │  │
│  │  └────────────┘  └─────────────┘ │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │   GatewayProxy                    │  │
│  │   (网关代理)                       │  │
│  └──────────────┬────────────────────┘  │
└─────────────────┼───────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
   ┌────▼───┐ ┌───▼───┐ ┌───▼────┐
   │ Chat   │ │ Agent │ │Workflow│
   │Service │ │Service│ │ Engine │
   └────────┘ └───────┘ └────────┘
```

## 🚀 性能优化

1. **缓存机制**: 可以添加意图分析结果缓存，减少重复分析
2. **异步处理**: 所有路由决策都是异步的，不会阻塞请求
3. **降级策略**: LLM失败时自动降级到规则匹配
4. **超时控制**: 设置合理的超时时间，避免长时间等待

## 📊 监控和日志

智能路由会记录以下日志：

- 路由决策结果（目标服务、意图、置信度）
- 路由决策耗时
- 路由失败情况

示例日志：
```
INFO: Intelligent routing: intent=agent_task, confidence=0.85, service=agent-service, reasoning=Rule-based matching
```

## 🔮 未来改进

1. **学习机制**: 基于历史路由结果优化路由决策
2. **A/B测试**: 支持路由策略的A/B测试
3. **动态权重**: 根据服务负载动态调整路由权重
4. **多意图支持**: 支持一个请求路由到多个服务
5. **路由链**: 支持请求在多个服务间流转

## 📚 相关文档

- [API Gateway README](../README.md)
- [服务发现文档](./core/service_discovery.py)
- [代理配置文档](./core/proxy.py)




