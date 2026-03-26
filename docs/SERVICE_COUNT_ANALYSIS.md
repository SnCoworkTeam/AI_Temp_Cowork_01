# 服务数量分析

## 预期服务数量：22个

根据 README.md，系统应该包含以下22个服务：

### 基础设施层（4个）
1. ✅ postgres - PostgreSQL数据库
2. ✅ redis - Redis缓存
3. ✅ redis-commander - Redis管理界面
4. ✅ qdrant - 向量数据库

### 核心架构层（3个）
5. ✅ registry-service - 服务注册与发现中心
6. ✅ api-gateway - 统一API网关
7. ✅ config-center - 配置管理中心

### 业务服务层（14个）
8. ✅ sap-mcp-server - SAP OData to MCP服务
9. ✅ mcp-gateway - MCP工具网关
10. ✅ workflow-engine - 工作流引擎
11. ✅ auth-service - 认证服务
12. ✅ knowledge-base - 知识库服务
13. ✅ metadata-service - 元数据服务
14. ✅ sap-metadata-agent - SAP元数据代理服务
15. ✅ chat-service - 聊天服务
16. ✅ joyagent-adapter - JoyAgent适配器
17. ✅ dag-orchestrator - DAG编排服务
18. ✅ agent-service - 智能体核心服务
19. ✅ agent-orchestrator - 智能体编排服务
20. ✅ agent-registry - 智能体注册中心
21. ✅ memory-service - 记忆服务

### 前端层（1个）
22. ✅ web-ui - Next.js前端界面

## docker-compose.yml 中的服务

从 `docker-compose.yml` 文件中，我找到了以下服务定义：

1. ✅ postgres
2. ✅ redis
3. ✅ redis-commander
4. ✅ registry-service
5. ✅ api-gateway
6. ✅ config-center
7. ✅ sap-mcp-server
8. ✅ mcp-gateway
9. ✅ workflow-engine
10. ✅ web-ui
11. ✅ auth-service
12. ✅ knowledge-base
13. ✅ metadata-service
14. ✅ chat-service
15. ✅ dag-orchestrator
16. ✅ agent-service
17. ✅ agent-orchestrator
18. ✅ agent-registry
19. ✅ joyagent-adapter
20. ✅ memory-service
21. ✅ qdrant
22. ✅ sap-metadata-agent

**总计：22个服务**

## 可能的问题

如果 Docker 中只有21个服务在运行，可能的原因：

1. **某个服务启动失败** - 检查 `docker-compose ps` 查看哪些服务状态不是 "Up"
2. **某个服务被手动停止** - 检查是否有服务被 `docker-compose stop` 停止
3. **健康检查失败** - 某些服务可能因为健康检查失败而重启失败
4. **依赖服务未就绪** - 某些服务可能因为依赖服务未就绪而无法启动

## 检查命令

```bash
# 查看所有服务状态
docker-compose ps

# 查看未运行的服务
docker-compose ps | grep -v "Up"

# 查看服务日志
docker-compose logs [service-name]

# 查看所有服务名称
docker-compose config --services
```

## 建议

1. 运行 `docker-compose ps` 查看实际运行的服务
2. 运行 `docker-compose config --services` 查看配置中的所有服务
3. 对比两者，找出缺失的服务
4. 检查缺失服务的日志，找出启动失败的原因


