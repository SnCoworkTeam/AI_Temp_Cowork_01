# SAP MM元数据和知识库构建指南（基于MCP服务）

## 📋 概述

本指南说明如何使用SAP OData MCP服务和网络数据构建SAP MM模块的元数据和知识库。

## 🎯 目标

1. **从SAP OData MCP服务获取系统数据** - 通过MCP服务查询SAP MM相关表和数据
2. **从网络生成知识库文档** - 基于SAP MM标准知识生成文档
3. **构建完整的元数据和知识库** - 导入实体、文档，建立关联关系

## 🏗️ 架构流程

```
┌─────────────────┐
│  SAP OData MCP  │
│     服务        │
│  (localhost:3001)│
└────────┬────────┘
         │
         │ 查询SAP MM数据
         ▼
┌─────────────────┐
│ fetch_sap_mm_   │
│ from_mcp.py     │
└────────┬────────┘
         │
         │ 导入实体
         ▼
┌─────────────────┐
│ metadata-service│
│  (localhost:8005)│
└─────────────────┘

┌─────────────────┐
│ 网络知识库      │
│ (预定义文档)    │
└────────┬────────┘
         │
         │ 生成文档
         ▼
┌─────────────────┐
│ generate_sap_   │
│ mm_documents_   │
│ from_web.py     │
└────────┬────────┘
         │
         │ 导入文档
         ▼
┌─────────────────┐
│ knowledge-base  │
│  (localhost:8003)│
└─────────────────┘
```

## 📦 前置条件

### 1. 服务状态检查

确保以下服务正在运行：

```bash
# 检查SAP OData MCP服务
curl http://localhost:3001/health

# 检查metadata-service
curl http://localhost:8005/health

# 检查knowledge-base
curl http://localhost:8003/health
```

### 2. 环境准备

```bash
# 安装Python依赖
pip install requests

# 确保Python 3.7+
python --version
```

## 🚀 执行步骤

### 步骤1: 从MCP服务获取SAP MM数据并导入实体

```bash
python fetch_sap_mm_from_mcp.py
```

**功能说明：**
- 连接SAP OData MCP服务（`http://localhost:3001`）
- 初始化MCP会话
- 搜索SAP MM相关的OData服务
- 发现服务中的实体
- 获取示例数据（如可用）
- 创建SAP MM业务实体并导入到metadata-service

**预期输出：**
```
=== 导入 8 个SAP MM实体 ===
[1/8] 创建: 物料主数据...
   ✅ 成功 (ID: 123)
[2/8] 创建: 供应商主数据...
   ✅ 成功 (ID: 124)
...
```

**创建的实体：**
- 物料主数据（MARA）
- 供应商主数据（LFA1）
- 采购订单抬头（EKKO）
- 采购订单行项目（EKPO）
- 采购申请（EBAN）
- 物料库存地点视图（MARD）
- 物料凭证抬头（MKPF）
- 物料凭证行项目（MSEG）

### 步骤2: 从网络生成SAP MM文档并导入知识库

```bash
python generate_sap_mm_documents_from_web.py
```

**功能说明：**
- 基于SAP MM标准知识生成7个核心文档
- 包含模块概述、物料管理、采购订单、供应商管理、库存管理、采购申请、物料凭证等主题
- 导入文档到knowledge-base服务

**预期输出：**
```
=== 导入 7 个SAP MM文档 ===
[1/7] 导入: SAP MM物料管理模块概述...
   ✅ 成功 (ID: 456)
[2/7] 导入: SAP MM物料主数据管理...
   ✅ 成功 (ID: 457)
...
```

**生成的文档：**
1. SAP MM物料管理模块概述
2. SAP MM物料主数据管理
3. SAP MM采购订单管理
4. SAP MM供应商管理
5. SAP MM库存管理
6. SAP MM采购申请管理
7. SAP MM物料凭证管理

### 步骤3: 建立文档-实体关联

```bash
python link_sap_mm_documents.py
```

**功能说明：**
- 基于文档内容和实体名称/描述进行语义匹配
- 建立文档与实体的关联关系
- 支持向量搜索和相似度计算

### 步骤4: 构建SAP MM知识图谱

```bash
# 调用本体构建API
curl -X POST http://localhost:8005/api/ontology/sap/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'
```

**功能说明：**
- 基于已导入的SAP MM实体构建知识图谱
- 使用LLM增强关系发现
- 生成实体间的关联关系

## 📊 数据验证

### 验证实体导入

```bash
# 查询SAP MM实体
curl "http://localhost:8005/api/metadata/business-entities?filter=metadata.sap_module:MM"
```

### 验证文档导入

```bash
# 查询SAP MM文档
curl "http://localhost:8003/api/knowledge/documents?category=sap_mm"
```

### 验证知识图谱

```bash
# 查询知识图谱节点
curl "http://localhost:8005/api/knowledge-graph/nodes?domain=metadata&entity_type=data_object"
```

## 🔧 故障排除

### 问题1: MCP服务连接失败

**症状：**
```
❌ MCP会话初始化失败: Connection refused
```

**解决方案：**
1. 检查MCP服务是否运行：`docker ps | grep sap-mcp`
2. 检查端口映射：`netstat -an | grep 3001`
3. 检查服务健康状态：`curl http://localhost:3001/health`

### 问题2: 实体导入失败

**症状：**
```
❌ 失败: HTTP 500
```

**解决方案：**
1. 检查metadata-service日志
2. 验证数据库连接
3. 检查实体数据格式是否正确

### 问题3: 文档导入失败

**症状：**
```
❌ 失败: HTTP 503
```

**解决方案：**
1. 检查knowledge-base服务状态
2. 验证文档内容格式
3. 检查服务依赖（如向量化服务）

## 📈 预期结果

### 实体统计
- **业务实体**: 8个SAP MM核心实体
- **实体类型**: data_object, business_process
- **元数据**: 包含SAP表名、OData服务、关键字段等信息

### 文档统计
- **知识库文档**: 7个SAP MM核心文档
- **文档类别**: overview, master_data, procurement, vendor, inventory, requisition, document
- **文档标签**: 包含SAP MM、物料管理、采购等标签

### 知识图谱统计
- **节点数**: 8+个实体节点
- **边数**: 15+个关系边
- **关系类型**: parent_of, related_to, depends_on等

## 🎯 后续优化

### 1. 扩展实体覆盖
- 添加更多SAP MM表（如发票、合同等）
- 从MCP服务动态发现新实体

### 2. 丰富文档内容
- 从SAP官方文档获取更多内容
- 集成实际业务案例
- 添加配置指南和最佳实践

### 3. 增强关联关系
- 使用LLM发现更多隐含关系
- 建立跨模块关联（如MM与SD、FI的关联）
- 优化关系置信度计算

### 4. 数据同步机制
- 定期从MCP服务同步最新数据
- 监控SAP系统变更
- 自动更新元数据和知识库

## 📝 注意事项

1. **MCP服务配置**: 确保SAP OData MCP服务已正确配置SAP连接信息
2. **服务依赖**: 确保metadata-service和knowledge-base服务正常运行
3. **数据权限**: 确保MCP服务有权限访问SAP MM相关数据
4. **网络连接**: 确保可以访问SAP系统和本地服务

## 🔗 相关文档

- [SAP_MM_QUICK_START.md](./SAP_MM_QUICK_START.md) - SAP MM快速开始指南
- [SAP_MM_METADATA_AND_KNOWLEDGE_BASE_BUILD_PLAN.md](./SAP_MM_METADATA_AND_KNOWLEDGE_BASE_BUILD_PLAN.md) - 详细构建计划
- [sap-odata-to-mcp-server/docs/API_DOCUMENTATION.md](./sap-odata-to-mcp-server/docs/API_DOCUMENTATION.md) - MCP服务API文档




