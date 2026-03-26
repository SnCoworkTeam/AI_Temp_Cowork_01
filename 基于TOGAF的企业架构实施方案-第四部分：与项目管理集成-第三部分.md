# 基于TOGAF的企业架构实施方案 - 第四部分：与项目管理集成

## 第三部分：实施检查清单和使用指南

**报告日期**: 2025-12-07  
**承接**: 第一部分集成策略、第二部分治理与工作流集成

---

## 📋 第三部分概述

本部分提供完整的实施检查清单、使用指南和最佳实践，确保企业架构与项目管理的成功集成。

---

## ✅ 一、实施检查清单

### 1.1 数据库层

#### 1.1.1 映射关系表

- [ ] 创建 `ea_project_mappings` 表
  - [ ] 源类型和目标类型字段
  - [ ] 映射类型字段
  - [ ] 同步启用标志
  - [ ] 索引创建

- [ ] 更新现有表结构
  - [ ] `adm_iterations` 表添加 `meta_data` 字段（如果不存在）
  - [ ] `adm_phases` 表添加 `meta_data` 字段（如果不存在）
  - [ ] `pm_projects` 表添加 `extra_metadata` 字段（如果不存在）
  - [ ] `pm_project_phases` 表添加 `extra_metadata` 字段（如果不存在）

- [ ] 创建数据库迁移脚本
  - [ ] 文件: `database/src/migrations/versions/026_add_ea_project_mapping_tables.py`
  - [ ] 包含升级和降级函数
  - [ ] 测试迁移脚本

#### 1.1.2 数据模型

- [ ] 创建映射模型
  - [ ] `EAProjectMapping` 模型类
  - [ ] 关系定义
  - [ ] 索引定义

- [ ] 更新现有模型
  - [ ] `ADMIteration` 模型添加关系
  - [ ] `ADMPhase` 模型添加关系
  - [ ] `Project` 模型添加关系

### 1.2 服务层

#### 1.2.1 集成服务

- [ ] 创建 `EAProjectIntegrationService`
  - [ ] `create_project_from_adm_iteration` 方法
  - [ ] `create_phases_from_adm_phases` 方法
  - [ ] `create_tasks_from_phase_deliverables` 方法
  - [ ] `sync_progress` 方法
  - [ ] `sync_status` 方法

- [ ] 创建 `UnifiedGovernanceService`
  - [ ] `validate_project_architecture_compliance` 方法
  - [ ] `create_governance_checklist` 方法
  - [ ] `check_compliance` 方法

- [ ] 创建 `ChangeManagementIntegrationService`
  - [ ] `create_architecture_change_request` 方法
  - [ ] `approve_change_with_impact_analysis` 方法

#### 1.2.2 工作流集成

- [ ] 创建 `ADMPhaseWorkflow` 类
  - [ ] 定义各阶段工作流模板
  - [ ] `create_phase_workflow` 方法
  - [ ] `create_tasks_from_workflow_steps` 方法

- [ ] 创建工作流执行同步服务
  - [ ] `sync_workflow_execution_to_tasks` 方法
  - [ ] 状态转换逻辑

### 1.3 API层

#### 1.3.1 集成API端点

- [ ] 创建 `/api/enterprise-architecture/projects` 路由
  - [ ] `POST /create-from-iteration/{iteration_id}` - 从迭代创建项目
  - [ ] `GET /stats` - 获取统计信息
  - [ ] `GET /` - 获取架构项目列表
  - [ ] `POST /sync/{iteration_id}` - 同步进度

- [ ] 更新项目管理API
  - [ ] `GET /api/v1/projects/{id}` - 返回架构信息
  - [ ] `GET /api/v1/projects/{id}/architecture` - 获取架构视图

- [ ] 创建治理API
  - [ ] `POST /api/enterprise-architecture/governance/validate/{project_id}` - 验证合规性
  - [ ] `GET /api/enterprise-architecture/governance/checklist/{project_id}` - 获取检查清单

### 1.4 前端层

#### 1.4.1 项目页面增强

- [ ] 项目详情页添加架构视图标签
  - [ ] ADM阶段时间线
  - [ ] 架构进度总览
  - [ ] 合规性检查结果

- [ ] 项目列表页添加架构筛选
  - [ ] 按架构迭代筛选
  - [ ] 显示架构进度
  - [ ] 显示合规率

#### 1.4.2 架构页面增强

- [ ] 架构迭代详情页添加项目视图
  - [ ] 显示关联项目信息
  - [ ] 项目进度同步显示
  - [ ] 快速跳转到项目页面

- [ ] 创建架构项目仪表板
  - [ ] 统计卡片
  - [ ] 项目列表
  - [ ] 进度可视化

### 1.5 测试

#### 1.5.1 单元测试

- [ ] 集成服务单元测试
  - [ ] `EAProjectIntegrationService` 测试
  - [ ] `UnifiedGovernanceService` 测试
  - [ ] `ChangeManagementIntegrationService` 测试

- [ ] 工作流集成测试
  - [ ] `ADMPhaseWorkflow` 测试
  - [ ] 工作流执行同步测试

#### 1.5.2 集成测试

- [ ] 端到端测试
  - [ ] 从ADM迭代创建项目
  - [ ] 阶段和任务自动创建
  - [ ] 进度同步测试
  - [ ] 合规性检查测试

---

## 📖 二、使用指南

### 2.1 创建架构项目

#### 2.1.1 步骤1: 创建ADM迭代

```python
# 通过API创建ADM迭代
POST /api/enterprise-architecture/adm/iterations
{
    "name": "G437项目企业架构设计",
    "description": "化工事业部工厂ERP系统升级推广项目的企业架构设计",
    "iteration_type": "full",
    "owner": "架构师姓名"
}
```

#### 2.1.2 步骤2: 从迭代创建项目

```python
# 自动创建项目
POST /api/enterprise-architecture/projects/create-from-iteration/{iteration_id}

# 系统会自动：
# 1. 创建项目（项目编码: EA-FULL-2025-001）
# 2. 创建9个项目阶段（对应ADM的9个阶段）
# 3. 为每个阶段创建任务（基于交付物）
# 4. 创建关键里程碑
```

#### 2.1.3 步骤3: 配置项目

```python
# 更新项目信息
PUT /api/v1/projects/{project_id}
{
    "manager_id": "项目经理ID",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "budget": 1000000
}
```

### 2.2 执行ADM阶段

#### 2.2.1 启动阶段

```python
# 执行ADM阶段
POST /api/enterprise-architecture/adm/phases/{phase_id}/execute
{
    "target_state": {
        "business_processes": 50,
        "application_systems": 20
    }
}

# 系统会自动：
# 1. 更新阶段状态为"in_progress"
# 2. 创建对应的工作流（如果配置了）
# 3. 从工作流步骤创建任务
# 4. 更新项目阶段进度
```

#### 2.2.2 跟踪进度

```python
# 查看阶段进度
GET /api/enterprise-architecture/adm/phases/{phase_id}

# 返回：
{
    "phase": {
        "phase_letter": "A",
        "phase_name": "架构愿景",
        "status": "in_progress",
        "progress_percent": 60
    },
    "deliverables": [
        {"name": "架构愿景文档", "status": "completed"},
        {"name": "利益相关者地图", "status": "in_progress"},
        {"name": "差距分析报告", "status": "todo"}
    ],
    "project_phase": {
        "id": "项目阶段ID",
        "progress_percent": 60
    },
    "tasks": [
        {"name": "创建架构愿景文档", "status": "completed"},
        {"name": "创建利益相关者地图", "status": "in_progress"}
    ]
}
```

### 2.3 同步进度

#### 2.3.1 手动同步

```python
# 同步迭代和项目进度
POST /api/enterprise-architecture/projects/sync/{iteration_id}

# 系统会：
# 1. 从项目阶段同步到ADM阶段
# 2. 从任务状态同步到交付物状态
# 3. 更新整体进度
```

#### 2.3.2 自动同步

```python
# 配置自动同步（通过定时任务）
# 每小时自动同步一次
# 配置在 config-center 中
{
    "ea_project_sync": {
        "enabled": true,
        "interval_minutes": 60,
        "auto_sync_on_task_update": true
    }
}
```

### 2.4 治理检查

#### 2.4.1 创建检查清单

```python
# 为项目创建治理检查清单
GET /api/enterprise-architecture/governance/checklist/{project_id}

# 返回：
{
    "checklist": [
        {
            "type": "architecture_principle",
            "principle_name": "标准化原则",
            "status": "pending",
            "check_items": [
                "检查命名规范",
                "检查数据结构",
                "检查接口规范"
            ]
        },
        {
            "type": "project_standard",
            "standard_name": "项目文档标准",
            "status": "pending",
            "check_items": [
                "检查文档模板",
                "检查文档完整性"
            ]
        }
    ]
}
```

#### 2.4.2 执行合规性检查

```python
# 验证项目架构合规性
POST /api/enterprise-architecture/governance/validate/{project_id}

# 返回：
{
    "compliant": false,
    "violations": [
        {
            "phase": "业务架构",
            "entity": {
                "type": "BusinessProcess",
                "name": "采购流程"
            },
            "violations": [
                {
                    "principle": "标准化原则",
                    "reason": "命名不符合规范"
                }
            ]
        }
    ],
    "compliance_rate": 85.5
}
```

---

## 🎯 三、最佳实践

### 3.1 项目创建最佳实践

1. **先创建ADM迭代，再创建项目**
   - 确保架构框架完整
   - 自动生成项目结构

2. **使用完整的ADM迭代类型**
   - `full`: 完整ADM循环
   - `targeted`: 目标架构迭代
   - `capability`: 能力架构迭代

3. **配置项目元数据**
   - 记录迭代类型
   - 记录架构框架版本
   - 记录行业分类

### 3.2 阶段执行最佳实践

1. **按顺序执行阶段**
   - 阶段A完成后开始阶段B
   - 确保依赖关系正确

2. **及时更新交付物状态**
   - 完成交付物后立即更新
   - 触发里程碑完成

3. **定期同步进度**
   - 每天同步一次
   - 关键节点立即同步

### 3.3 治理最佳实践

1. **建立检查清单**
   - 项目启动时创建
   - 定期更新检查项

2. **及时处理违规**
   - 发现违规立即处理
   - 记录处理过程

3. **持续改进**
   - 收集治理反馈
   - 优化治理流程

### 3.4 工作流集成最佳实践

1. **为关键阶段配置工作流**
   - 阶段A、B、C建议配置
   - 自动化重复性任务

2. **工作流步骤要细化**
   - 每个步骤对应一个任务
   - 明确输入输出

3. **监控工作流执行**
   - 及时处理失败步骤
   - 优化工作流性能

---

## 🔧 四、故障排查

### 4.1 常见问题

#### 问题1: 项目创建失败

**症状**: 从ADM迭代创建项目时失败

**可能原因**:
- 迭代不存在
- 项目编码冲突
- 数据库连接问题

**解决方案**:
```python
# 1. 检查迭代是否存在
GET /api/enterprise-architecture/adm/iterations/{iteration_id}

# 2. 检查项目编码
GET /api/v1/projects?project_code=EA-FULL-2025-001

# 3. 检查数据库连接
GET /api/health
```

#### 问题2: 进度不同步

**症状**: 项目进度和架构进度不一致

**可能原因**:
- 同步服务未运行
- 映射关系丢失
- 状态转换错误

**解决方案**:
```python
# 1. 手动触发同步
POST /api/enterprise-architecture/projects/sync/{iteration_id}

# 2. 检查映射关系
GET /api/enterprise-architecture/mappings?iteration_id={iteration_id}

# 3. 检查状态转换配置
GET /api/enterprise-architecture/config/status-mapping
```

#### 问题3: 任务未自动创建

**症状**: ADM阶段执行后，任务未自动创建

**可能原因**:
- 交付物配置缺失
- 工作流未配置
- 任务创建服务错误

**解决方案**:
```python
# 1. 检查阶段交付物配置
GET /api/enterprise-architecture/adm/phases/{phase_id}/deliverables

# 2. 检查工作流配置
GET /api/workflows?adm_phase={phase_letter}

# 3. 手动创建任务
POST /api/v1/tasks
{
    "project_id": "...",
    "phase_id": "...",
    "name": "任务名称"
}
```

---

## 📊 五、监控与报告

### 5.1 关键指标

```yaml
监控指标:
  集成指标:
    - 架构项目总数
    - 活跃迭代数
    - 同步成功率
    - 映射关系完整性
  
  进度指标:
    - 阶段完成率
    - 任务完成率
    - 交付物完成率
    - 里程碑达成率
  
  治理指标:
    - 合规率
    - 违规数量
    - 检查清单完成率
    - 变更请求数量
```

### 5.2 报告模板

#### 5.2.1 周报模板

```markdown
# 架构项目周报

## 项目概览
- 项目名称: {project_name}
- 架构迭代: {iteration_name}
- 报告周期: {week_start} - {week_end}

## 阶段进度
- 已完成阶段: {completed_phases}/{total_phases}
- 当前阶段: {current_phase}
- 阶段进度: {phase_progress}%

## 关键交付物
- 已完成: {completed_deliverables}
- 进行中: {in_progress_deliverables}
- 待开始: {pending_deliverables}

## 治理检查
- 合规率: {compliance_rate}%
- 违规项: {violations_count}
- 已处理: {resolved_violations}

## 风险与问题
- 高风险项: {high_risks}
- 待解决问题: {open_issues}

## 下周计划
- 计划完成阶段: {next_phase}
- 计划交付物: {planned_deliverables}
```

---

## 🎓 六、培训材料

### 6.1 用户培训

#### 6.1.1 架构师培训

**培训内容**:
1. TOGAF ADM方法论
2. 如何创建ADM迭代
3. 如何从迭代创建项目
4. 如何跟踪架构进度
5. 如何进行治理检查

**培训时长**: 4小时

#### 6.1.2 项目经理培训

**培训内容**:
1. 架构项目的特点
2. 如何查看架构视图
3. 如何同步进度
4. 如何管理架构任务
5. 如何理解架构交付物

**培训时长**: 2小时

### 6.2 操作手册

- [ ] 创建架构项目操作手册
- [ ] 执行ADM阶段操作手册
- [ ] 治理检查操作手册
- [ ] 故障排查操作手册

---

## 📝 七、总结

### 7.1 集成价值

1. **统一管理**: 架构和项目在一个平台管理
2. **自动同步**: 减少手动维护工作
3. **治理统一**: 架构治理和项目治理统一
4. **可视化**: 清晰的架构和项目视图

### 7.2 实施建议

1. **分阶段实施**: 先实现核心功能，再逐步增强
2. **充分测试**: 确保集成稳定可靠
3. **用户培训**: 确保用户理解使用方法
4. **持续改进**: 根据反馈优化功能

---

**第三部分完成**  
**完整集成方案报告生成完毕**




