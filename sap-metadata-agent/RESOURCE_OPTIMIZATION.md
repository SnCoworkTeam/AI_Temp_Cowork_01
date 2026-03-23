# SAP元数据构建资源优化指南

## 资源优化策略

为了确保SAP元数据构建顺利进行并节省系统资源，建议暂停非必需服务。

### 必需服务（保持运行）

以下服务是SAP元数据构建所必需的：

1. **postgres** - PostgreSQL数据库
   - metadata-service需要数据库存储元数据
   - 端口: 5432

2. **redis** - Redis缓存
   - metadata-service可能使用Redis缓存
   - 端口: 6379

3. **metadata-service** - 元数据服务
   - 存储和管理发现的SAP元数据
   - 端口: 8005

4. **mcp-gateway** - MCP工具网关
   - 提供对SAP MCP工具的访问
   - 端口: 8001

5. **sap-metadata-agent** - SAP元数据智能体
   - 执行元数据发现和构建
   - 端口: 8015

6. **sap-mcp-server** - SAP MCP服务器（可选但推荐）
   - 如果使用OData服务发现，需要此服务
   - 端口: 3001

### 可选服务

以下服务可以根据需要决定是否运行：

- **knowledge-base** - 知识库
  - 如果启用语义索引构建，需要此服务
  - 如果不需要语义索引，可以暂停

### 可以暂停的服务

以下服务在构建SAP元数据时不需要，可以暂停以节省资源：

1. **web-ui** - 前端界面
2. **chat-service** - 聊天服务
3. **workflow-engine** - 工作流引擎
4. **agent-service** - 智能体服务
5. **agent-orchestrator** - 智能体编排服务
6. **agent-registry** - 智能体注册服务
7. **dag-orchestrator** - DAG编排服务
8. **memory-service** - 记忆服务
9. **qdrant** - 向量数据库
10. **api-gateway** - API网关
11. **config-center** - 配置中心
12. **registry-service** - 注册服务
13. **auth-service** - 认证服务

## 快速操作命令

### 暂停非必需服务

```bash
docker-compose stop \
  web-ui \
  chat-service \
  workflow-engine \
  agent-service \
  agent-orchestrator \
  agent-registry \
  dag-orchestrator \
  memory-service \
  qdrant \
  api-gateway \
  config-center \
  registry-service \
  auth-service
```

### 确保必需服务运行

```bash
docker-compose up -d \
  postgres \
  redis \
  metadata-service \
  mcp-gateway \
  sap-metadata-agent \
  sap-mcp-server
```

### 检查服务状态

```bash
docker-compose ps
```

### 验证服务健康

```bash
# 检查metadata-service
curl http://localhost:8005/api/health

# 检查mcp-gateway
curl http://localhost:8001/api/health

# 检查sap-metadata-agent
curl http://localhost:8015/api/sap-metadata/health
```

## 资源节省效果

暂停非必需服务后，预计可以节省：
- **内存**: 约 2-4 GB
- **CPU**: 减少 30-50% 的使用率
- **网络**: 减少不必要的网络流量

## 构建完成后

构建完成后，如果需要使用其他功能，可以重新启动暂停的服务：

```bash
docker-compose start \
  web-ui \
  chat-service \
  workflow-engine \
  agent-service \
  # ... 其他需要的服务
```

或者启动所有服务：

```bash
docker-compose up -d
```

## 注意事项

1. **数据持久化**: 暂停服务不会影响数据库中的数据
2. **服务依赖**: 某些服务可能有依赖关系，暂停前请确认
3. **日志查看**: 暂停的服务日志仍然可以通过 `docker-compose logs` 查看
4. **快速恢复**: 使用 `docker-compose start` 可以快速恢复暂停的服务

## 监控资源使用

构建过程中可以监控资源使用情况：

```bash
# 查看容器资源使用
docker stats

# 查看特定服务资源使用
docker stats enterprise-ai-sap-metadata-agent
```


