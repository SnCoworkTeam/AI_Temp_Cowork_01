# 阶段一第2周工作计划：采购场景图谱构建

**周次**: 第2周  
**目标**: 构建采购场景的企业语义能力图谱  
**时间**: 2025-12-02 开始  
**状态**: 进行中

---

## 📋 本周目标

1. **数据采集与原子化**
   - 收集采购场景的业务文档
   - 提取业务活动、实体和关系
   - 创建采购场景的初始数据

2. **向量化与图谱构建**
   - 为业务活动生成语义向量
   - 创建知识图谱节点
   - 建立活动-能力映射关系

3. **数据质量验证**
   - 验证数据完整性
   - 验证向量质量
   - 验证映射关系准确性

---

## 🎯 具体任务

### 任务1: 创建采购场景数据采集脚本

**目标**: 创建脚本用于采集和结构化采购场景数据

**交付物**:
- `scripts/collect_procurement_data.py` - 数据采集脚本
- `data/procurement/activities.json` - 业务活动数据
- `data/procurement/entities.json` - 业务实体数据
- `data/procurement/mappings.json` - 活动-能力映射数据

**验收标准**:
- 至少采集10个核心采购活动
- 至少采集5个业务实体
- 至少建立10个活动-能力映射

### 任务2: 创建向量化服务

**目标**: 为业务活动生成语义向量嵌入

**交付物**:
- `services/vectorization_service.py` - 向量化服务
- 向量化配置和参数
- 向量质量验证脚本

**验收标准**:
- 所有业务活动都有向量嵌入
- 向量维度正确（如1536维）
- 相似活动向量距离较近

### 任务3: 创建图谱构建服务

**目标**: 将业务活动、实体和映射关系构建为知识图谱

**交付物**:
- `services/graph_builder_service.py` - 图谱构建服务
- 图谱节点创建逻辑
- 图谱边（关系）创建逻辑

**验收标准**:
- 所有节点已创建
- 所有边（关系）已创建
- 图谱查询功能正常

### 任务4: 创建数据质量验证脚本

**目标**: 验证采购场景数据的质量和完整性

**交付物**:
- `tests/test_procurement_graph_quality.py` - 数据质量测试
- 质量报告生成脚本

**验收标准**:
- 数据完整性 > 95%
- 向量质量评分 > 80%
- 映射准确率 > 90%

---

## 📊 数据模型

### 采购场景核心活动

1. **创建采购订单** (activity:procurement:create_po)
   - 描述: 在SAP系统中创建标准采购订单
   - 类型: action
   - 领域: procurement
   - 前置条件: 供应商已存在、物料主数据已维护
   - 成功标准: PO号生成且状态为已保存

2. **查询采购订单** (activity:procurement:query_po)
   - 描述: 查询指定条件的采购订单
   - 类型: query
   - 领域: procurement
   - 前置条件: 无
   - 成功标准: 返回符合条件的订单列表

3. **审批采购订单** (activity:procurement:approve_po)
   - 描述: 审批采购订单
   - 类型: approval
   - 领域: procurement
   - 前置条件: 订单已创建、未审批
   - 成功标准: 订单状态变为已审批

4. **处理采购异常** (activity:procurement:handle_exception)
   - 描述: 处理采购过程中的异常情况
   - 类型: action
   - 领域: procurement
   - 前置条件: 异常已识别
   - 成功标准: 异常已处理并记录

5. **生成采购报告** (activity:procurement:generate_report)
   - 描述: 生成采购相关的统计报告
   - 类型: query
   - 领域: procurement
   - 前置条件: 有采购数据
   - 成功标准: 报告已生成

### 采购场景核心实体

1. **采购订单** (entity:procurement:purchase_order)
2. **供应商** (entity:procurement:supplier)
3. **物料** (entity:procurement:material)
4. **采购部门** (entity:procurement:department)
5. **审批流程** (entity:procurement:approval_workflow)

### 活动-能力映射示例

- `activity:procurement:create_po` → `component:sap:create_po`
- `activity:procurement:query_po` → `component:sap:query_po`
- `activity:procurement:approve_po` → `component:workflow:approve_po`

---

## 🛠️ 技术实现

### 向量化

- **模型**: text-embedding-3-large 或 text-embedding-ada-002
- **维度**: 1536 或 3072
- **服务**: OpenAI Embeddings API 或本地模型

### 图谱存储

- **数据库**: PostgreSQL (已有)
- **图数据库**: 可选 Neo4j 或使用PostgreSQL的JSONB
- **向量存储**: 使用vector_coordinator服务

### 数据流程

```
业务文档/数据
    ↓
数据采集脚本
    ↓
结构化数据 (JSON)
    ↓
向量化服务
    ↓
向量嵌入
    ↓
图谱构建服务
    ↓
知识图谱节点和边
    ↓
数据质量验证
    ↓
入库存储
```

---

## 📝 实施步骤

### 第1天: 数据采集
- [ ] 创建数据采集脚本
- [ ] 定义采购场景数据模型
- [ ] 采集初始数据

### 第2天: 向量化服务
- [ ] 创建向量化服务
- [ ] 配置向量化参数
- [ ] 为所有活动生成向量

### 第3天: 图谱构建
- [ ] 创建图谱构建服务
- [ ] 创建节点和边
- [ ] 验证图谱结构

### 第4天: 数据质量验证
- [ ] 创建质量验证脚本
- [ ] 运行质量检查
- [ ] 修复质量问题

### 第5天: 测试和文档
- [ ] 编写测试用例
- [ ] 运行完整测试
- [ ] 更新文档

---

## ✅ 验收标准

1. **数据完整性**
   - ✅ 至少10个业务活动
   - ✅ 至少5个业务实体
   - ✅ 至少10个活动-能力映射

2. **向量质量**
   - ✅ 所有活动都有向量
   - ✅ 向量维度正确
   - ✅ 相似度计算正常

3. **图谱完整性**
   - ✅ 所有节点已创建
   - ✅ 所有边已创建
   - ✅ 图谱查询正常

4. **测试通过**
   - ✅ 所有测试用例通过
   - ✅ 数据质量评分 > 80%
   - ✅ 无严重错误

---

## 📚 相关文档

- `STAGE1_WEEK1_TEST_REPORT.md` - 第1周测试报告
- `FINAL_ARCHITECTURE_IMPLEMENTATION_ROADMAP.md` - 实施路线图
- `ENTERPRISE_SEMANTIC_GRAPH_IMPLEMENTATION_PLAN.md` - 图谱实施计划

---

**创建时间**: 2025-12-02  
**状态**: 进行中




