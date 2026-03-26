# 测试任务编排功能指南

## 📋 前置条件

在测试任务编排功能之前，**必须先完成所有元数据的构建**，包括：

1. ✅ ABAP数据字典信息
2. ✅ 业务术语映射
3. ✅ 语义关系
4. ✅ 数据库表和OData服务元数据
5. ✅ 语义索引

## 🚀 步骤1: 构建完整元数据

### 使用增强版构建脚本

```bash
cd sap-metadata-agent
python build_complete_enhanced_metadata.py
```

或使用Python 3：

```bash
python3 build_complete_enhanced_metadata.py
```

### 构建内容

脚本会自动执行：

1. **数据库发现**（如果数据库连接可用）
   - 发现所有SAP数据库表
   - 获取ABAP字典信息（DD02L, DD03L, DD04T, DD07T）
   - 提取业务术语
   - 构建语义关系

2. **OData服务发现**（分批处理）
   - 发现所有OData服务和实体
   - 提取业务术语
   - 构建语义关系
   - 同步到metadata-service

3. **语义索引构建**
   - 为所有元数据构建语义索引
   - 支持语义搜索

4. **验证**
   - 验证元数据是否成功同步到metadata-service

### 预期输出

构建完成后，应该看到类似以下输出：

```
构建完成报告
============================================================

数据库发现:
  - 数据资产: 5000+
  - 表: 5000+
  - 业务实体: 100+
  - 业务流程: 50+
  - 业务术语映射: 200+
  - 语义关系: 300+

OData服务发现:
  - 完成批次: 35/35
  - 数据资产: 20000+
  - 业务实体: 500+
  - 业务流程: 200+
  - 业务术语映射: 500+
  - 语义关系: 800+

总计:
  - 数据资产: 25000+
  - 业务实体: 600+
  - 业务流程: 250+
  - 业务术语映射: 700+
  - 语义关系: 1100+
  - 语义索引: ✓ 完成
  - metadata-service中的资产: 25000+
```

## 🧪 步骤2: 验证元数据完整性

### 检查业务术语映射

```bash
# 查询包含业务术语的资产
curl "http://localhost:8005/api/search?q=客户&limit=10"
```

应该返回包含"客户"业务术语的数据资产。

### 检查语义关系

```bash
# 查询特定资产，查看语义关系
curl "http://localhost:8005/api/data-assets?search=KNA1&limit=1"
```

检查返回的资产metadata中是否包含`semantic_relationships`字段。

### 检查ABAP字典信息

```bash
# 查询包含ABAP字典信息的表
curl "http://localhost:8005/api/data-assets?classification=sap_master_data_customer&limit=1"
```

检查返回的资产的`schema_info`中是否包含`abap_dictionary`字段。

## 🎯 步骤3: 测试任务编排

### 测试1: 简单业务术语识别

```bash
curl -X POST http://localhost:8009/api/v1/tasks/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询客户主数据",
    "context": {}
  }'
```

**预期行为**:
- 系统识别"客户"业务术语
- 查询元数据，找到KNA1表、客户OData实体
- 在任务分解提示词中包含这些技术资产信息
- 生成任务节点，推荐使用SAP相关工具

### 测试2: 复杂任务依赖关系

```bash
curl -X POST http://localhost:8009/api/v1/tasks/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询客户主数据，然后查询该客户的销售订单",
    "context": {}
  }'
```

**预期行为**:
- 识别"客户"和"销售订单"业务术语
- 获取客户-订单的语义关系
- 生成两个任务节点：
  - 节点1: 查询客户主数据（KNA1）
  - 节点2: 查询销售订单（VBAK）
- 节点2依赖节点1（基于语义关系）

### 测试3: 执行完整任务

```bash
curl -X POST http://localhost:8009/api/v1/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询客户主数据，然后查询该客户的销售订单",
    "context": {}
  }'
```

**预期行为**:
- 任务分解（如上）
- 按依赖关系执行：
  1. 先执行客户查询
  2. 使用客户查询结果作为输入，执行订单查询
- 返回聚合结果

## 📊 验证要点

### 1. 业务术语识别

检查任务分解结果中是否包含：
- 相关的技术资产信息
- SAP表名（如KNA1, VBAK）
- 推荐的SAP工具

### 2. 依赖关系优化

检查任务节点之间的依赖关系：
- 是否基于语义关系建立依赖
- 依赖顺序是否合理（客户 → 订单）

### 3. 元数据增强提示词

查看dag-orchestrator日志：
```bash
docker-compose logs dag-orchestrator | grep "metadata-enhanced"
```

应该看到：
- "检测到的业务术语: 客户, 销售订单"
- "相关的技术资产: ..."
- "语义关系: ..."

## 🐛 故障排查

### 问题1: 业务术语未识别

**症状**: 任务分解结果中没有包含元数据信息

**排查**:
1. 检查元数据是否已构建（业务术语映射是否存在）
2. 检查metadata-service是否运行
3. 检查dag-orchestrator的METADATA_SERVICE_URL配置
4. 查看日志确认元数据查询是否成功

### 问题2: 依赖关系未优化

**症状**: 任务依赖关系没有基于语义关系

**排查**:
1. 检查语义关系是否已构建
2. 检查语义关系查询是否成功
3. 查看日志确认依赖优化是否执行

### 问题3: 元数据服务连接失败

**症状**: 日志显示"Failed to search assets"或"Failed to get semantic relationships"

**排查**:
1. 检查metadata-service是否运行
2. 检查网络连接
3. 检查METADATA_SERVICE_URL配置
4. 验证metadata-service的搜索API是否正常

## 📝 测试检查清单

- [ ] 元数据构建完成（数据资产、业务实体、业务流程）
- [ ] 业务术语映射已生成
- [ ] 语义关系已构建
- [ ] ABAP字典信息已包含
- [ ] 语义索引已构建
- [ ] metadata-service中的数据资产数量正确
- [ ] 业务术语搜索功能正常
- [ ] 任务分解包含元数据信息
- [ ] 依赖关系基于语义关系优化
- [ ] 完整任务执行成功

## 🎯 下一步

完成测试后，可以：

1. **性能优化**: 优化元数据查询性能
2. **扩展业务术语**: 添加更多业务术语关键词
3. **增强依赖关系**: 完善语义关系的识别和利用
4. **个性化推荐**: 基于使用统计推荐相关资产

## 📚 相关文档

- [SAP元数据增强实施文档](./ENHANCED_METADATA_IMPLEMENTATION.md)
- [集成指南](../INTEGRATION_GUIDE.md)
- [优化总结](../OPTIMIZATION_SUMMARY.md)


