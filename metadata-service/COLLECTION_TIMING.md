# 元数据采集时机实现说明

本文档说明元数据自动采集服务在不同时机的实现情况。

## ✅ 已实现的采集时机

### 1. 服务启动时：注册基础元数据 ✅

**实现位置：**
- `metadata-service/src/main.py` - 在应用启动时调用
- `metadata-service/src/collectors/collection_manager.py` - `register_on_startup()` 方法

**功能：**
- 服务启动时自动从各个服务采集基础元数据
- 并行采集工具、工作流、知识库文档、AI模型和数据血缘
- 不阻塞服务启动，在后台异步执行

**触发方式：**
- 自动：服务启动时自动触发
- 手动：`POST /api/collection/startup`

### 2. 数据变更时：更新元数据版本 ✅

**实现位置：**
- `mcp-gateway/src/services/tool_service.py` - 工具注册时
- `metadata-service/src/collectors/collection_manager.py` - `update_on_data_change()` 方法

**功能：**
- 工具注册/更新时自动同步元数据
- 工作流保存/更新时自动同步元数据
- 文档上传/更新时自动同步元数据

**触发方式：**
- 自动：数据变更时自动触发
- 手动：`POST /api/collection/data-change?entity_type={type}&entity_id={id}&change_type={type}`

### 3. 工具执行时：收集使用统计 ✅

**实现位置：**
- `mcp-gateway/src/services/tool_service.py` - `execute_tool()` 方法
- `metadata-service/src/collectors/collection_manager.py` - `collect_tool_usage_statistics()` 方法

**功能：**
- 记录工具执行次数（总调用、成功、失败）
- 计算平均执行时间
- 记录最后执行时间和状态

**触发方式：**
- 自动：工具执行时自动触发
- 手动：`POST /api/collection/tool-usage?tool_name={name}&execution_time={time}&success={bool}`

### 4. 工作流运行时：收集执行指标 ✅

**实现位置：**
- `workflow-engine/src/workflows/workflow_manager_db.py` - `execute_workflow()` 方法
- `metadata-service/src/collectors/collection_manager.py` - `collect_workflow_execution_metrics()` 方法

**功能：**
- 记录工作流执行次数（总执行、成功、失败）
- 计算成功率和平均执行时间
- 记录输入输出数据大小（可选）

**触发方式：**
- 自动：工作流执行时自动触发
- 手动：`POST /api/collection/workflow-execution?workflow_id={id}&execution_time={time}&success={bool}`

### 5. 用户交互时：收集访问模式 ✅

**实现位置：**
- `metadata-service/src/collectors/collection_manager.py` - `collect_user_access_pattern()` 方法

**功能：**
- 记录用户对数据资产、工作流、文档的访问
- 跟踪访问时间、用户ID、操作类型
- 保留最近100条访问记录

**触发方式：**
- 手动：`POST /api/collection/user-access?entity_type={type}&entity_id={id}&user_id={id}&action={action}`

## 📋 API端点

### 采集管理API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/collection/startup` | POST | 服务启动时注册基础元数据 |
| `/api/collection/data-change` | POST | 数据变更时更新元数据 |
| `/api/collection/tool-usage` | POST | 工具执行时收集使用统计 |
| `/api/collection/workflow-execution` | POST | 工作流运行时收集执行指标 |
| `/api/collection/user-access` | POST | 用户交互时收集访问模式 |
| `/api/collection/sync-all` | POST | 手动触发同步所有元数据 |

## 🔧 集成点

### 1. 工具服务集成
```python
# mcp-gateway/src/services/tool_service.py
# 工具注册时
await metadata_client.create_tool_metadata(tool_metadata)

# 工具执行时
await metadata_client.update_usage_statistics(tool_name, statistics)
```

### 2. 工作流服务集成
```python
# workflow-engine/src/workflows/workflow_manager_db.py
# 工作流执行时
await metadata_integration.update_execution_statistics(workflow_id, statistics)
```

### 3. 知识库服务集成
```python
# knowledge-base/src/services/document_service.py
# 文档上传/更新时（待实现）
await metadata_enrichment.create_document_metadata(document_metadata)
```

## 📊 采集的数据类型

### 工具元数据
- 工具名称、描述、版本
- 输入输出Schema
- 使用统计（调用次数、成功率、平均执行时间）
- 性能指标

### 工作流元数据
- 工作流定义、版本
- 执行统计（执行次数、成功率、平均执行时间）
- 数据源和输出
- 使用的AI模型

### 文档元数据
- 文档基本信息
- 质量评分
- 访问模式
- 向量嵌入状态

### 数据血缘
- 数据流关系
- 转换逻辑
- 业务规则
- 数据质量影响

## 🚀 使用示例

### 手动触发服务启动注册
```bash
curl -X POST http://localhost:8005/api/collection/startup
```

### 手动触发数据变更更新
```bash
curl -X POST "http://localhost:8005/api/collection/data-change?entity_type=tool&entity_id=my_tool&change_type=update"
```

### 手动触发工具使用统计收集
```bash
curl -X POST "http://localhost:8005/api/collection/tool-usage?tool_name=my_tool&execution_time=1.5&success=true"
```

### 手动触发工作流执行指标收集
```bash
curl -X POST "http://localhost:8005/api/collection/workflow-execution?workflow_id=my_workflow&execution_time=10.5&success=true"
```

### 手动触发用户访问模式收集
```bash
curl -X POST "http://localhost:8005/api/collection/user-access?entity_type=data_asset&entity_id=my_asset&user_id=user123&action=access"
```

## ⚠️ 注意事项

1. **异步执行**：大部分采集操作是异步执行的，不会阻塞主业务流程
2. **错误处理**：采集失败不会影响主业务，只会记录警告日志
3. **性能影响**：采集操作设计为轻量级，对主业务性能影响最小
4. **数据一致性**：采集的数据可能与实际数据有短暂延迟

## 🔮 未来改进

1. **批量采集**：支持批量更新多个实体的元数据
2. **增量采集**：只采集变更的数据，提高效率
3. **采集调度**：支持定时自动采集
4. **采集监控**：提供采集状态和统计的监控面板
5. **采集配置**：支持配置哪些时机需要采集，哪些不需要

