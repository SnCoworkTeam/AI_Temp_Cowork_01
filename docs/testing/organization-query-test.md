# 查询组织机构功能测试指南

## 问题描述
在服务器上测试"查询组织机构"时，执行到第二步就停止了。

## 测试步骤

### 1. 启动本地Docker服务

```bash
cd e:\enterprise-ai-platform
docker-compose up -d postgres redis metadata-service agent-service api-gateway web-ui
```

### 2. 检查服务状态

```bash
docker-compose ps
```

确保以下服务状态为 `healthy` 或 `Up`:
- postgres
- redis
- metadata-service
- agent-service
- api-gateway
- web-ui

### 3. 测试流程

#### 3.1 检查服务健康状态

```bash
# API Gateway
curl http://localhost:8080/health

# Agent Service
curl http://localhost:8010/api/v1/health

# Metadata Service
curl http://localhost:8005/api/health
```

#### 3.2 测试组织架构API

```bash
curl http://localhost:8005/api/enterprise-architecture/organizations
```

#### 3.3 测试动态工作流执行

在浏览器中访问：`http://localhost:3000/chat`

输入："查询组织机构"

观察执行流程：
1. **思考阶段**：应该看到思考过程流式输出
2. **执行阶段**：
   - Step 1: 元数据增强（metadata_agent）
   - Step 2: 数据查询（data_query_agent）- **这里可能卡住**
   - Step 3: 数据清洗（data_clean_agent）
   - Step 4: 结果合成（result_synthesis_agent）

### 4. 排查第二步停止的问题

#### 4.1 查看Agent Service日志

```bash
docker-compose logs -f agent-service
```

关注以下日志：
- `[DataQueryAgent]` - 数据查询智能体执行日志
- `[DynamicExecutionEngine]` - 执行引擎日志
- `[MetadataService]` - 元数据服务调用日志

#### 4.2 可能的问题原因

1. **超时问题**：
   - `data_query_agent` 调用 `metadata-service` 超时
   - 检查 `METADATA_SERVICE_URL` 环境变量
   - 默认超时时间：30秒（在 `data_query_agent.py` 中）

2. **网络连接问题**：
   - Agent Service 无法连接到 Metadata Service
   - 检查 Docker 网络：`docker network inspect enterprise-ai-platform_enterprise-ai-network`

3. **API响应问题**：
   - Metadata Service 返回错误或空数据
   - 检查 Metadata Service 日志：`docker-compose logs metadata-service`

4. **智能体执行异常**：
   - `data_query_agent` 执行时抛出异常
   - 查看异常堆栈信息

#### 4.3 调试步骤

1. **直接测试组织架构API**：
```bash
docker exec -it enterprise-ai-agent-service curl http://metadata-service:8005/api/enterprise-architecture/organizations
```

2. **检查环境变量**：
```bash
docker exec -it enterprise-ai-agent-service env | grep METADATA_SERVICE_URL
```

3. **查看执行上下文**：
在 `agent-service/src/core/dynamic_execution_engine.py` 的 `_execute_network_with_streaming` 方法中添加更多日志

### 5. 修复建议

如果发现是超时问题，可以：

1. **增加超时时间**：
   在 `agent-service/src/core/agents/data_query_agent.py` 中：
   ```python
   async with httpx.AsyncClient(timeout=60.0) as client:  # 从30秒增加到60秒
   ```

2. **添加重试机制**：
   在调用 metadata-service API 时添加重试逻辑

3. **改进错误处理**：
   确保所有异常都被正确捕获并返回友好的错误消息

### 6. 预期结果

成功执行后应该看到：
1. 思考过程完整输出
2. 元数据增强结果
3. 组织架构查询结果（6条记录）
4. 数据清洗结果（如果需要）
5. 最终合成结果（格式化的Markdown报告）

### 7. 服务器环境检查

在服务器上执行以下检查：

```bash
# 检查服务状态
docker-compose ps

# 查看agent-service日志（重点关注第二步）
docker-compose logs --tail=100 agent-service | grep -i "step\|layer\|data_query\|organization"

# 检查网络连接
docker exec -it enterprise-ai-agent-service ping -c 3 metadata-service

# 检查环境变量
docker exec -it enterprise-ai-agent-service env | grep -E "METADATA|SERVICE"
```

### 8. 常见问题解决

#### 问题1：第二步卡住，没有错误信息
- **原因**：可能是流式输出中断
- **解决**：检查前端网络连接，查看浏览器控制台是否有网络错误

#### 问题2：超时错误
- **原因**：Metadata Service 响应慢或不可用
- **解决**：检查 Metadata Service 日志，确认数据库连接正常

#### 问题3：智能体未找到
- **原因**：Agent Registry 未正确初始化
- **解决**：重启 agent-service，检查初始化日志

## 测试检查清单

- [ ] 所有服务正常启动
- [ ] 健康检查通过
- [ ] 组织架构API可访问
- [ ] 思考过程正常输出
- [ ] Step 1 (metadata_agent) 执行成功
- [ ] Step 2 (data_query_agent) 执行成功
- [ ] Step 3 (data_clean_agent) 执行成功（如果需要）
- [ ] Step 4 (result_synthesis_agent) 执行成功
- [ ] 最终结果正确显示








