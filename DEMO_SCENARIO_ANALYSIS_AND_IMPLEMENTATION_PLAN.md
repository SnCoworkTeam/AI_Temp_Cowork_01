# 采购业务演示方案分析与实施计划

**分析日期**: 2025-12-04  
**演示场景**: 采购业务标准流程与异常处理  
**状态**: 📋 **分析完成，待实施**

---

## 📊 当前系统状态分析

### ✅ 已具备的核心能力

#### 1. 业务活动定义 ✅
- ✅ `activity:procurement:create_po` - 创建采购订单
- ✅ `activity:procurement:query_po` - 查询采购订单
- ✅ `activity:procurement:approve_po` - 审批采购订单
- ✅ `activity:procurement:handle_exception` - 处理采购异常
- ✅ `activity:procurement:process_payment` - 处理付款

**位置**: `data/procurement/activities.json`

#### 2. 业务实体定义 ✅
- ✅ `entity:procurement:purchase_order` - 采购订单
- ✅ `entity:procurement:supplier` - 供应商
- ✅ `entity:procurement:material` - 物料

**位置**: `data/procurement/entities.json`

#### 3. 活动-能力映射 ✅
- ✅ `activity:procurement:create_po` → `component:sap:create_po`
- ✅ `activity:procurement:query_po` → `component:sap:query_po`

**位置**: `data/procurement/mappings.json`

#### 4. 核心服务 ✅
- ✅ **统一意图识别服务** (`services/unified_intent_service.py`) - 已集成LLM增强
- ✅ **企业语义引擎** (`services/enterprise_semantic_engine.py`)
- ✅ **SAP MCP服务器** (`sap-odata-to-mcp-server/`)
- ✅ **知识库服务** (`knowledge-base/`)

---

## ❌ 缺失内容清单

### 1. 演示数据缺失

#### 1.1 供应商主数据 ❌
**需求**: `demo_data/suppliers.json`
```json
{
  "supplier_code": "SUP_001",
  "name": "苏州精密零件有限公司",
  "contact": "张经理",
  "payment_terms": "Net 30",
  "credit_limit": 200000,
  "quality_score": 4.2
}
```

#### 1.2 物料主数据 ❌
**需求**: `demo_data/materials.json`
```json
{
  "material_code": "MAT001",
  "name": "铝合金板",
  "description": "6061铝合金",
  "unit_price": 420,
  "unit": "件",
  "current_stock": 150,
  "safety_stock": 50
}
```

#### 1.3 采购订单历史数据 ❌
**需求**: `demo_data/po_history.csv`
- 最近3个月的10张采购订单
- 包含订单号、供应商、物料、数量、金额、状态、问题标记

#### 1.4 质量问题记录 ❌
**需求**: `demo_data/quality_issues.json`
- 苏州精密零件的3次质量问题记录
- 日期、问题描述、处理状态、影响订单号

---

### 2. 业务活动缺失

#### 2.1 暂停付款业务活动 ❌
**需求**: `activity:procurement:hold_payment`
```json
{
  "id": "activity:procurement:hold_payment",
  "name": "暂停付款",
  "description": "因质量问题暂停对供应商的付款",
  "activity_type": "approval",
  "business_domain": "procurement",
  "success_criteria": "付款状态更新为暂停",
  "prerequisites": ["质量问题已确认"]
}
```

---

### 3. 能力单元缺失

#### 3.1 供应商质量检查组件 ❌
**需求**: `component:quality:check_supplier`
```json
{
  "id": "component:quality:check_supplier",
  "name": "供应商质量检查组件",
  "type": "Component",
  "endpoint": "http://quality-service/api/check",
  "input_schema": {
    "supplier_code": {"type": "string", "required": true},
    "days_back": {"type": "integer", "default": 90}
  },
  "output_schema": {
    "quality_score": {"type": "float"},
    "issues_count": {"type": "integer"},
    "issue_details": {"type": "array"}
  }
}
```

#### 3.2 SAP付款暂停组件 ❌
**需求**: `component:sap:payment_hold`
```json
{
  "id": "component:sap:payment_hold",
  "name": "SAP付款暂停组件",
  "type": "Component",
  "endpoint": "http://sap-mcp-server/api/payment/hold",
  "input_schema": {
    "supplier_code": {"type": "string", "required": true},
    "po_numbers": {"type": "array", "required": true},
    "reason": {"type": "string", "required": true}
  }
}
```

---

### 4. 工作流定义缺失

#### 4.1 标准采购工作流 ❌
**需求**: `workflow:standard_procurement`
- 验证需求 → 预算检查 → 创建PO → 发送确认

#### 4.2 质量问题处理工作流 ❌
**需求**: `workflow:quality_issue_handling`
- 验证问题 → 暂停付款 → 通知供应商 → 创建调查任务

**位置**: `workflow-engine/examples/` 或 `config/workflows/`

---

### 5. 知识库文档缺失

#### 5.1 采购知识库文档 ❌
**需求**: `demo_knowledge/` 目录
- `采购流程指南.md` - 标准操作流程
- `供应商管理规范.md` - 供应商选择与评估标准
- `质量问题处理SOP.md` - 异常处理步骤
- `SAP_ME21N操作手册.md` - 系统操作指南
- `采购审批权限矩阵.md` - 审批规则与权限

---

### 6. 演示脚本缺失

#### 6.1 场景一演示脚本 ❌
**需求**: `demos/demo_scenario_1_standard_procurement.py`
- 标准采购订单创建流程演示

#### 6.2 场景二演示脚本 ❌
**需求**: `demos/demo_scenario_2_quality_issue.py`
- 异常采购处理流程演示

---

## 🎯 实施计划

### 阶段1: 数据准备 (优先级: P0)

#### 任务1.1: 创建演示数据目录结构
```bash
mkdir -p demo_data
mkdir -p demo_knowledge
mkdir -p demos
```

#### 任务1.2: 生成供应商主数据
- 文件: `demo_data/suppliers.json`
- 包含: 苏州精密零件有限公司等3-5个供应商
- 字段: 供应商编码、名称、联系人、付款条件、信用额度、质量评分

#### 任务1.3: 生成物料主数据
- 文件: `demo_data/materials.json`
- 包含: MAT001铝合金板等5-10个物料
- 字段: 物料编码、名称、描述、单价、单位、库存信息

#### 任务1.4: 生成采购订单历史数据
- 文件: `demo_data/po_history.csv`
- 包含: 最近3个月的10-15张采购订单
- 字段: 订单号、供应商、物料、数量、金额、状态、创建日期、问题标记

#### 任务1.5: 生成质量问题记录
- 文件: `demo_data/quality_issues.json`
- 包含: 苏州精密零件的3-5次质量问题记录
- 字段: 日期、供应商、问题描述、严重程度、处理状态、影响订单号

**预计时间**: 2-3小时

---

### 阶段2: 业务活动扩展 (优先级: P0)

#### 任务2.1: 添加暂停付款业务活动
- 文件: `data/procurement/activities.json`
- 添加: `activity:procurement:hold_payment`
- 同步: 更新数据库中的业务活动表

#### 任务2.2: 添加质量问题验证活动
- 文件: `data/procurement/activities.json`
- 添加: `activity:quality:verify_issue`
- 同步: 更新数据库

**预计时间**: 1小时

---

### 阶段3: 能力单元扩展 (优先级: P0)

#### 任务3.1: 创建供应商质量检查组件
- 文件: `data/procurement/components.json` (新建)
- 或: 注册到组件注册表
- 实现: 质量检查服务接口（可以是模拟实现）

#### 任务3.2: 创建SAP付款暂停组件
- 文件: `data/procurement/components.json`
- 实现: SAP MCP工具或模拟实现

#### 任务3.3: 更新活动-能力映射
- 文件: `data/procurement/mappings.json`
- 添加: `activity:procurement:hold_payment` → `component:sap:payment_hold`
- 添加: `activity:quality:verify_issue` → `component:quality:check_supplier`

**预计时间**: 2-3小时

---

### 阶段4: 工作流定义 (优先级: P1)

#### 任务4.1: 创建标准采购工作流
- 文件: `config/workflows/standard_procurement.yaml`
- 步骤:
  1. 验证需求 (validate_requirement)
  2. 预算检查 (check_budget)
  3. 创建PO (create_po)
  4. 发送确认 (send_confirmation)

#### 任务4.2: 创建质量问题处理工作流
- 文件: `config/workflows/quality_issue_handling.yaml`
- 步骤:
  1. 验证问题 (verify_issue)
  2. 暂停付款 (hold_payments)
  3. 通知供应商 (notify_supplier)
  4. 创建调查任务 (create_task)

**预计时间**: 2-3小时

---

### 阶段5: 知识库文档 (优先级: P1)

#### 任务5.1: 创建采购流程指南
- 文件: `demo_knowledge/采购流程指南.md`
- 内容: 标准采购操作流程

#### 任务5.2: 创建供应商管理规范
- 文件: `demo_knowledge/供应商管理规范.md`
- 内容: 供应商选择与评估标准

#### 任务5.3: 创建质量问题处理SOP
- 文件: `demo_knowledge/质量问题处理SOP.md`
- 内容: 异常处理步骤

#### 任务5.4: 创建SAP操作手册
- 文件: `demo_knowledge/SAP_ME21N操作手册.md`
- 内容: 系统操作指南

#### 任务5.5: 创建审批权限矩阵
- 文件: `demo_knowledge/采购审批权限矩阵.md`
- 内容: 审批规则与权限

**预计时间**: 2-3小时

---

### 阶段6: 演示脚本开发 (优先级: P1)

#### 任务6.1: 创建场景一演示脚本
- 文件: `demos/demo_scenario_1_standard_procurement.py`
- 功能:
  - 用户输入解析
  - 意图理解展示
  - 能力匹配展示
  - 执行过程模拟
  - 结果展示

#### 任务6.2: 创建场景二演示脚本
- 文件: `demos/demo_scenario_2_quality_issue.py`
- 功能:
  - 用户输入解析
  - 意图分析与关联
  - 智能诊断展示
  - 多系统协同执行
  - 结果与建议展示

**预计时间**: 3-4小时

---

## 📋 实施优先级总结

| 优先级 | 阶段 | 预计时间 | 状态 |
|--------|------|----------|------|
| **P0** | 阶段1: 数据准备 | 2-3小时 | ❌ 待实施 |
| **P0** | 阶段2: 业务活动扩展 | 1小时 | ❌ 待实施 |
| **P0** | 阶段3: 能力单元扩展 | 2-3小时 | ❌ 待实施 |
| **P1** | 阶段4: 工作流定义 | 2-3小时 | ❌ 待实施 |
| **P1** | 阶段5: 知识库文档 | 2-3小时 | ❌ 待实施 |
| **P1** | 阶段6: 演示脚本开发 | 3-4小时 | ❌ 待实施 |

**总预计时间**: 12-17小时

---

## 🎯 快速启动方案 (MVP)

如果时间紧迫，可以先实现最小可行演示版本：

### MVP包含内容:
1. ✅ 基础演示数据 (供应商、物料各3个)
2. ✅ 暂停付款业务活动
3. ✅ 质量检查组件 (模拟实现)
4. ✅ 场景一演示脚本 (简化版)
5. ✅ 场景二演示脚本 (简化版)

**MVP预计时间**: 4-6小时

---

## 📝 下一步行动

1. **确认优先级**: 与业务方确认演示重点
2. **分配资源**: 确定实施人员和时间
3. **开始实施**: 按优先级顺序执行
4. **测试验证**: 每个阶段完成后进行测试
5. **文档完善**: 同步更新演示文档

---

**状态**: 📋 **分析完成，等待实施决策**

