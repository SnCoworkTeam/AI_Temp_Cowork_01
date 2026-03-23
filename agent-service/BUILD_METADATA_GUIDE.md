# SAP OData 智能体元数据构建指南

## 概述

本指南说明如何重启服务并构建 SAP OData 智能体的元数据。

## 快速开始

### 方式1: 使用自动化脚本（推荐）

#### Windows (PowerShell)

```powershell
# 1. 重启服务
docker-compose restart agent-service

# 2. 等待服务启动（约10-20秒）
Start-Sleep -Seconds 20

# 3. 运行构建脚本
cd agent-service
python build_sap_odata_agent_metadata.py
```

#### Linux/Mac (Bash)

```bash
# 使用一键脚本（自动重启并构建）
cd agent-service
chmod +x restart_and_build_metadata.sh
./restart_and_build_metadata.sh
```

### 方式2: 手动步骤

#### 步骤1: 重启 Agent Service

```bash
# 重启服务
docker-compose restart agent-service

# 或重新创建容器
docker-compose up -d --force-recreate agent-service

# 查看日志确认服务已启动
docker-compose logs -f agent-service
```

#### 步骤2: 等待服务就绪

等待服务完全启动（通常需要10-30秒），可以通过健康检查确认：

```bash
# 检查服务健康状态
curl http://localhost:8010/api/v1/health
```

#### 步骤3: 运行元数据构建脚本

```bash
cd agent-service
python build_sap_odata_agent_metadata.py
```

## 构建脚本功能

`build_sap_odata_agent_metadata.py` 脚本会：

1. **检查服务健康状态**
   - 验证 Agent Service 是否运行
   - 验证 Metadata Service 是否运行

2. **触发元数据构建**
   - 获取 SAP OData 智能体实例
   - 检查当前元数据状态
   - 如果未构建，自动开始构建（首次构建限制30个服务）

3. **验证注册**
   - 检查智能体是否已注册到 metadata-service
   - 验证 AI 模型注册
   - 验证业务实体注册

## 构建参数

### 首次构建（快速）

默认情况下，脚本会限制构建30个服务，避免超时：

```python
await agent.build_metadata(limit_services=30)
```

### 完整构建（所有服务）

如果需要构建所有服务的元数据，可以修改脚本或直接调用：

```python
# 构建所有服务（可能需要较长时间）
result = await agent.build_metadata(
    force_rebuild=True,
    limit_services=None  # 不限制数量
)
```

### 分批构建

对于大量服务，建议分批构建：

```python
# 第一批：前50个服务
result1 = await agent.build_metadata(limit_services=50, offset=0)

# 第二批：接下来50个服务
result2 = await agent.build_metadata(limit_services=50, offset=50)

# 继续...
```

## 验证构建结果

### 1. 查看构建状态

```python
from agent_service.src.core.dynamic_execution_engine import DynamicExecutionEngine

engine = DynamicExecutionEngine()
await engine.initialize()
sap_agent = engine.agent_pool["sap_odata_agent"]

# 获取元数据摘要
summary = sap_agent.get_metadata_summary()
print(f"服务数量: {summary['total_services']}")
print(f"实体数量: {summary['total_entities']}")
```

### 2. 查看服务元数据

```python
# 获取所有服务元数据
all_metadata = await sap_agent.get_service_metadata()

# 获取特定服务元数据
service_meta = await sap_agent.get_service_metadata("SERVICE_ID")
```

### 3. 检查 metadata-service

```bash
# 检查 AI 模型注册
curl "http://localhost:8005/api/ai-models?name=agent_sap_odata_agent"

# 检查业务实体注册
curl "http://localhost:8005/api/business-entities?name=sap_odata_agent"
```

## 故障排除

### 问题1: 服务未启动

**症状**: 脚本报告服务未就绪

**解决方案**:
```bash
# 检查服务状态
docker-compose ps agent-service

# 查看日志
docker-compose logs agent-service

# 重启服务
docker-compose restart agent-service
```

### 问题2: MCP 服务连接失败

**症状**: 构建时无法连接到 SAP OData MCP 服务器

**解决方案**:
1. 检查 SAP OData MCP 服务器是否运行
2. 检查环境变量 `SAP_ODATA_MCP_SERVER_URL` 是否正确
3. 确认网络连接正常

### 问题3: 构建超时

**症状**: 构建过程中超时

**解决方案**:
1. 减少 `limit_services` 参数值
2. 分批构建
3. 检查网络和 SAP 系统响应速度

### 问题4: 元数据未注册到 metadata-service

**症状**: 构建成功但 metadata-service 中找不到

**解决方案**:
1. 检查 metadata-service 是否运行
2. 查看 agent-service 启动日志，确认注册是否成功
3. 手动触发注册（服务重启时会自动注册）

## 高级用法

### 编程方式构建

```python
import asyncio
from agent_service.src.core.dynamic_execution_engine import DynamicExecutionEngine

async def build_metadata():
    engine = DynamicExecutionEngine()
    await engine.initialize()
    
    sap_agent = engine.agent_pool["sap_odata_agent"]
    
    # 构建元数据
    result = await sap_agent.build_metadata(
        force_rebuild=False,
        limit_services=50
    )
    
    print(f"构建结果: {result}")
    return result

# 运行
asyncio.run(build_metadata())
```

### 定时构建

可以设置定时任务定期更新元数据：

```bash
# 添加到 crontab (每天凌晨2点构建)
0 2 * * * cd /path/to/agent-service && python build_sap_odata_agent_metadata.py
```

## 注意事项

1. **首次构建时间**: 首次构建可能需要较长时间，取决于服务数量
2. **资源消耗**: 构建过程会消耗一定的 CPU 和内存资源
3. **网络依赖**: 需要能够访问 SAP OData MCP 服务器
4. **缓存机制**: 已构建的元数据会被缓存，避免重复构建

## 相关文件

- `build_sap_odata_agent_metadata.py` - 元数据构建脚本
- `restart_and_build_metadata.sh` - 一键重启和构建脚本（Linux/Mac）
- `src/core/agents/sap_odata_agent.py` - SAP OData 智能体实现

## 支持

如有问题，请查看：
- Agent Service 日志: `docker-compose logs agent-service`
- Metadata Service 日志: `docker-compose logs metadata-service`
- SAP OData MCP Server 日志: `docker-compose logs sap-odata-mcp-server`

