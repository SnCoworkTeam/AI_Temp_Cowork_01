# 元数据分类体系重新设计

## 问题分析

### 当前问题

1. **分类字段不统一**
   - `data_assets` 使用 `classification` 字段（String(50)）
   - `business_entities` 使用 `classification` 字段（String(50)）
   - `ai_models` 没有 `classification` 字段，只有 `model_type`
   - `workflows` 没有 `classification` 字段，只有 `workflow_type`
   - 部分数据使用 `category` 和 `domain` 存储在 `metadata` JSON 中

2. **分类数据缺失**
   - 很多元数据项没有设置 `classification` 值
   - 分类值是自由文本，没有标准化
   - 前端从数据中提取分类时，可能得到空列表

3. **分类筛选不完整**
   - 只有 `data-assets` 类型支持分类筛选
   - 其他类型（workflows、ai-models、business-entities）没有分类筛选功能

4. **分类体系混乱**
   - 没有统一的分类标准
   - 不同数据源使用不同的分类命名
   - 分类层级关系不清晰

## 重新设计方案

### 1. 统一分类字段

所有元数据类型都使用 `classification` 字段，但根据类型有不同的分类体系：

#### 数据资产分类 (DataAsset Classification)
```
- 数据安全分类
  - public (公开数据)
  - internal (内部数据)
  - confidential (机密数据)
  - restricted (受限数据)
  - pii (个人身份信息)
  
- 数据业务分类
  - master_data (主数据)
  - transaction_data (事务数据)
  - reference_data (参考数据)
  - analytical_data (分析数据)
  - operational_data (运营数据)
  
- 数据来源分类
  - sap (SAP系统)
  - erp (ERP系统)
  - crm (CRM系统)
  - database (数据库)
  - api (API接口)
  - file (文件系统)
  - stream (流数据)
```

#### AI模型分类 (AIModel Classification)
```
- 模型类型分类
  - llm (大语言模型)
  - embedding (嵌入模型)
  - classification (分类模型)
  - regression (回归模型)
  - clustering (聚类模型)
  - nlp (自然语言处理)
  - computer_vision (计算机视觉)
  - recommendation (推荐模型)
  
- 应用领域分类
  - business_intelligence (商业智能)
  - customer_service (客户服务)
  - sales_marketing (销售营销)
  - operations (运营管理)
  - finance (财务管理)
  - hr (人力资源)
```

#### 工作流分类 (Workflow Classification)
```
- 工作流类型分类
  - data_pipeline (数据管道)
  - ml_pipeline (机器学习管道)
  - etl (ETL流程)
  - batch (批处理)
  - streaming (流处理)
  - scheduled (定时任务)
  - manual (手动执行)
  
- 业务领域分类
  - data_integration (数据集成)
  - data_quality (数据质量)
  - data_governance (数据治理)
  - ml_training (模型训练)
  - ml_inference (模型推理)
  - reporting (报表生成)
```

#### 业务实体分类 (BusinessEntity Classification)
```
- 实体类型分类
  - domain (业务域)
  - concept (概念)
  - term (术语)
  - glossary (词汇表)
  - policy (政策)
  - rule (规则)
  - standard (标准)
  - metric (指标)
  
- 业务领域分类
  - sales (销售)
  - marketing (营销)
  - finance (财务)
  - hr (人力资源)
  - operations (运营)
  - it (信息技术)
```

### 2. 分类数据结构

```typescript
interface Classification {
  // 主分类（必填）
  primary: string
  // 子分类（可选）
  secondary?: string
  // 标签（可选，多个）
  tags?: string[]
}
```

存储方式：
- 简单模式：`classification = "master_data"`（单个字符串）
- 复合模式：`classification = "master_data:customer"`（主分类:子分类）
- JSON模式：`classification = '{"primary": "master_data", "secondary": "customer", "tags": ["sap", "critical"]}'`（复杂分类）

### 3. 分类获取策略

1. **从数据中提取**：从现有数据的 `classification` 字段提取
2. **从类型推断**：根据 `asset_type`、`model_type`、`workflow_type`、`entity_type` 推断分类
3. **从元数据提取**：从 `metadata` JSON 中的 `category`、`domain` 字段提取
4. **默认分类**：如果都没有，使用 "未分类" (uncategorized)

### 4. 分类筛选增强

- 所有元数据类型都支持分类筛选
- 支持多级分类筛选（主分类 + 子分类）
- 支持标签筛选
- 支持分类统计（每个分类的数量）

## 实施计划

### Phase 1: 数据修复和标准化（1周）
1. 为所有元数据类型添加 `classification` 字段（如果缺失）
2. 从现有数据中提取和标准化分类
3. 为没有分类的数据设置默认分类

### Phase 2: 前端增强（1周）
1. 统一分类筛选组件
2. 为所有类型添加分类筛选
3. 显示分类统计信息
4. 支持多级分类展示

### Phase 3: 分类管理（1周）
1. 分类管理界面
2. 分类层级管理
3. 分类自动推荐








