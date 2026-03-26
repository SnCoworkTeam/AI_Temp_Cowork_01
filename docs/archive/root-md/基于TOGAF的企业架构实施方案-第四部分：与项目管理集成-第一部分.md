# 基于TOGAF的企业架构实施方案 - 第四部分：与项目管理集成

## 第一部分：集成策略与映射关系

**报告日期**: 2025-12-07  
**项目背景**: 化工事业部工厂ERP系统升级推广项目（G437）  
**承接**: 前三部分实施方案

---

## 📋 第一部分概述

本部分详细说明如何将TOGAF ADM企业架构过程与项目管理过程有机结合，实现架构驱动的项目管理。

### 核心目标

1. **架构项目化**: 将ADM迭代作为项目进行管理
2. **阶段任务化**: 将ADM阶段映射为项目阶段和任务
3. **交付物跟踪**: 将架构交付物作为项目任务和里程碑
4. **治理一体化**: 架构治理与项目治理统一管理

---

## 🎯 一、集成策略

### 1.1 集成原则

```yaml
集成原则:
  1. 架构驱动: 以TOGAF ADM为框架，项目管理为执行手段
  2. 双向映射: ADM迭代 ↔ 项目，ADM阶段 ↔ 项目阶段
  3. 交付物管理: 架构交付物 ↔ 项目任务和里程碑
  4. 治理统一: 架构治理与项目治理统一管理
  5. 进度同步: 架构进度与项目进度实时同步
```

### 1.2 集成架构

```
┌─────────────────────────────────────────────────────────┐
│              企业架构与项目管理集成架构                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌────────▼───────┐
│  企业架构层    │                    │   项目管理层    │
│                │                    │                 │
│ ADM迭代        │◄───映射关系───────►│ 项目 (Project)  │
│ ADM阶段        │◄───映射关系───────►│ 项目阶段        │
│ 架构交付物     │◄───映射关系───────►│ 任务/里程碑     │
│ 架构治理       │◄───统一管理───────►│ 项目治理        │
└────────────────┘                    └─────────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        │
            ┌───────────▼───────────┐
            │   集成服务层           │
            │                        │
            │ - 映射服务             │
            │ - 同步服务             │
            │ - 治理服务             │
            └────────────────────────┘
```

---

## 🔗 二、核心映射关系

### 2.1 ADM迭代 ↔ 项目映射

#### 2.1.1 映射规则

```python
# ADM迭代到项目的映射规则
ADM_ITERATION_TO_PROJECT = {
    "映射字段": {
        "iteration.name": "project.name",
        "iteration.description": "project.description",
        "iteration.iteration_type": "project.extra_metadata['iteration_type']",
        "iteration.status": "project.status (转换)",
        "iteration.start_date": "project.start_date",
        "iteration.end_date": "project.end_date",
        "iteration.owner": "project.manager_id"
    },
    "状态转换": {
        "planning": "planning",
        "in_progress": "active",
        "completed": "completed",
        "cancelled": "cancelled"
    },
    "项目编码规则": "EA-{iteration_type}-{year}-{sequence}"
}
```

#### 2.1.2 映射服务实现

```python
# metadata-service/src/services/ea_project_integration_service.py

class EAProjectIntegrationService:
    """企业架构与项目管理集成服务"""
    
    def __init__(self, db: Session, project_service_client):
        self.db = db
        self.project_client = project_service_client
    
    async def create_project_from_adm_iteration(self, iteration_id: UUID) -> Dict:
        """从ADM迭代创建项目"""
        # 获取ADM迭代
        iteration = self.db.query(ADMIteration).filter(
            ADMIteration.id == iteration_id
        ).first()
        
        if not iteration:
            raise ValueError(f"ADM迭代不存在: {iteration_id}")
        
        # 生成项目编码
        project_code = self._generate_project_code(iteration)
        
        # 创建项目
        project_data = {
            "project_code": project_code,
            "name": f"企业架构迭代: {iteration.name}",
            "description": iteration.description or f"基于TOGAF ADM的架构迭代项目",
            "status": self._convert_iteration_status(iteration.status),
            "start_date": iteration.start_date,
            "end_date": iteration.end_date,
            "manager_id": self._get_user_id(iteration.owner),
            "priority": "high",
            "extra_metadata": {
                "iteration_id": str(iteration.id),
                "iteration_type": iteration.iteration_type,
                "adm_framework": "TOGAF",
                "source": "enterprise_architecture"
            }
        }
        
        # 调用项目管理服务创建项目
        project = await self.project_client.create_project(project_data)
        
        # 建立映射关系
        iteration.meta_data = iteration.meta_data or {}
        iteration.meta_data["project_id"] = project["id"]
        iteration.meta_data["project_code"] = project["project_code"]
        self.db.commit()
        
        # 为每个ADM阶段创建项目阶段
        await self._create_phases_from_adm_phases(iteration.id, project["id"])
        
        return {
            "iteration_id": str(iteration.id),
            "project_id": project["id"],
            "project_code": project["project_code"],
            "mapping": "created"
        }
    
    def _generate_project_code(self, iteration: ADMIteration) -> str:
        """生成项目编码"""
        year = datetime.now().year
        sequence = self._get_next_sequence(year)
        iteration_type = iteration.iteration_type or "FULL"
        return f"EA-{iteration_type}-{year}-{sequence:03d}"
    
    def _convert_iteration_status(self, iteration_status: str) -> str:
        """转换迭代状态到项目状态"""
        status_map = {
            "planning": "planning",
            "in_progress": "active",
            "completed": "completed",
            "cancelled": "cancelled"
        }
        return status_map.get(iteration_status, "planning")
```

### 2.2 ADM阶段 ↔ 项目阶段映射

#### 2.2.1 映射规则

```python
# ADM阶段到项目阶段的映射
ADM_PHASE_TO_PROJECT_PHASE = {
    "阶段映射": {
        "P": {"name": "架构治理框架", "sequence": 0},
        "A": {"name": "架构愿景", "sequence": 1},
        "B": {"name": "业务架构", "sequence": 2},
        "C": {"name": "信息系统架构", "sequence": 3},
        "D": {"name": "技术架构", "sequence": 4},
        "E": {"name": "机会与解决方案", "sequence": 5},
        "F": {"name": "迁移规划", "sequence": 6},
        "G": {"name": "实施治理", "sequence": 7},
        "H": {"name": "架构变更管理", "sequence": 8}
    },
    "阶段顺序": ["P", "A", "B", "C", "D", "E", "F", "G", "H"]
}
```

#### 2.2.2 阶段创建服务

```python
async def _create_phases_from_adm_phases(self, iteration_id: UUID, project_id: str):
    """从ADM阶段创建项目阶段"""
    # 获取所有ADM阶段
    adm_phases = self.db.query(ADMPhase).filter(
        ADMPhase.iteration_id == iteration_id
    ).order_by(ADMPhase.phase_letter).all()
    
    phase_mapping = {}
    
    for adm_phase in adm_phases:
        # 创建项目阶段
        phase_data = {
            "project_id": project_id,
            "name": f"阶段{adm_phase.phase_letter}: {adm_phase.phase_name}",
            "description": adm_phase.phase_name,
            "sequence": self._get_phase_sequence(adm_phase.phase_letter),
            "start_date": adm_phase.start_date,
            "end_date": adm_phase.end_date,
            "extra_metadata": {
                "adm_phase_id": str(adm_phase.id),
                "phase_letter": adm_phase.phase_letter,
                "phase_name": adm_phase.phase_name,
                "adm_framework": "TOGAF"
            }
        }
        
        phase = await self.project_client.create_phase(phase_data)
        phase_mapping[str(adm_phase.id)] = phase["id"]
        
        # 更新ADM阶段的映射关系
        adm_phase.meta_data = adm_phase.meta_data or {}
        adm_phase.meta_data["project_phase_id"] = phase["id"]
        
        # 为阶段创建任务和里程碑
        await self._create_tasks_from_phase_deliverables(adm_phase, phase["id"])
        await self._create_milestones_from_phase(adm_phase, phase["id"])
    
    self.db.commit()
    return phase_mapping
    
def _get_phase_sequence(self, phase_letter: str) -> int:
    """获取阶段顺序"""
    sequence_map = {
        "P": 0, "A": 1, "B": 2, "C": 3, "D": 4,
        "E": 5, "F": 6, "G": 7, "H": 8
    }
    return sequence_map.get(phase_letter, 0)
```

### 2.3 架构交付物 ↔ 任务/里程碑映射

#### 2.3.1 交付物映射规则

```python
# ADM阶段交付物到任务/里程碑的映射
ADM_DELIVERABLES_MAPPING = {
    "阶段A (架构愿景)": {
        "deliverables": [
            {"name": "架构愿景文档", "type": "document", "task": True, "milestone": True},
            {"name": "利益相关者地图", "type": "artifact", "task": True, "milestone": False},
            {"name": "差距分析报告", "type": "document", "task": True, "milestone": True}
        ],
        "artifacts": [
            {"name": "业务架构图", "type": "diagram", "task": True},
            {"name": "应用架构图", "type": "diagram", "task": True},
            {"name": "技术架构图", "type": "diagram", "task": True}
        ]
    },
    "阶段B (业务架构)": {
        "deliverables": [
            {"name": "业务架构文档", "type": "document", "task": True, "milestone": True},
            {"name": "业务能力地图", "type": "artifact", "task": True, "milestone": False},
            {"name": "业务流程地图", "type": "artifact", "task": True, "milestone": False}
        ],
        "artifacts": [
            {"name": "业务能力模型", "type": "model", "task": True},
            {"name": "业务流程模型", "type": "model", "task": True},
            {"name": "业务服务模型", "type": "model", "task": True}
        ]
    }
    # ... 其他阶段的映射
}
```

#### 2.3.2 任务创建服务

```python
async def _create_tasks_from_phase_deliverables(
    self, adm_phase: ADMPhase, project_phase_id: str
):
    """从ADM阶段交付物创建项目任务"""
    deliverables = adm_phase.deliverables or []
    artifacts = adm_phase.artifacts or []
    
    all_items = deliverables + artifacts
    
    for item in all_items:
        # 创建任务
        task_data = {
            "project_id": adm_phase.iteration.meta_data.get("project_id"),
            "phase_id": project_phase_id,
            "name": item.get("name", "未命名交付物"),
            "description": f"ADM阶段{adm_phase.phase_letter}的交付物: {item.get('name')}",
            "status": "todo",
            "extra_metadata": {
                "adm_phase_id": str(adm_phase.id),
                "deliverable_type": item.get("type", "unknown"),
                "is_deliverable": item in deliverables,
                "is_artifact": item in artifacts,
                "adm_framework": "TOGAF"
            }
        }
        
        task = await self.project_client.create_task(task_data)
        
        # 如果是关键交付物，创建里程碑
        if item.get("milestone", False):
            milestone_data = {
                "project_id": adm_phase.iteration.meta_data.get("project_id"),
                "phase_id": project_phase_id,
                "name": f"完成: {item.get('name')}",
                "description": f"ADM阶段{adm_phase.phase_letter}的关键交付物",
                "target_date": adm_phase.end_date,
                "status": "planned",
                "extra_metadata": {
                    "task_id": task["id"],
                    "adm_phase_id": str(adm_phase.id),
                    "deliverable_name": item.get("name")
                }
            }
            await self.project_client.create_milestone(milestone_data)
```

---

## 🔄 三、双向同步机制

### 3.1 进度同步

```python
async def sync_progress(self, iteration_id: UUID):
    """同步ADM迭代和项目进度"""
    iteration = self.db.query(ADMIteration).filter(
        ADMIteration.id == iteration_id
    ).first()
    
    if not iteration or "project_id" not in (iteration.meta_data or {}):
        return
    
    project_id = iteration.meta_data["project_id"]
    
    # 获取项目进度
    project = await self.project_client.get_project(project_id)
    
    # 同步项目状态到迭代
    iteration.status = self._convert_project_status(project["status"])
    
    # 同步各阶段进度
    for adm_phase in iteration.phases:
        if "project_phase_id" in (adm_phase.meta_data or {}):
            phase_id = adm_phase.meta_data["project_phase_id"]
            phase = await self.project_client.get_phase(phase_id)
            
            # 更新阶段状态
            adm_phase.status = self._convert_phase_status(phase.get("status"))
            adm_phase.end_date = phase.get("end_date")
            
            # 更新交付物状态
            await self._sync_deliverables_status(adm_phase, phase_id)
    
    self.db.commit()
    
    return {
        "iteration_id": str(iteration_id),
        "project_id": project_id,
        "sync_status": "completed"
    }
```

### 3.2 状态同步

```python
async def sync_status(self, source: str, source_id: str, target_status: str):
    """同步状态（从项目到架构或从架构到项目）"""
    if source == "project":
        # 从项目同步到ADM迭代
        project = await self.project_client.get_project(source_id)
        iteration_id = project.get("extra_metadata", {}).get("iteration_id")
        
        if iteration_id:
            iteration = self.db.query(ADMIteration).filter(
                ADMIteration.id == UUID(iteration_id)
            ).first()
            
            if iteration:
                iteration.status = self._convert_project_status(target_status)
                self.db.commit()
    
    elif source == "iteration":
        # 从ADM迭代同步到项目
        iteration = self.db.query(ADMIteration).filter(
            ADMIteration.id == UUID(source_id)
        ).first()
        
        if iteration and "project_id" in (iteration.meta_data or {}):
            project_id = iteration.meta_data["project_id"]
            await self.project_client.update_project_status(
                project_id, 
                self._convert_iteration_status(target_status)
            )
```

---

## 📊 四、集成数据模型

### 4.1 映射关系表

```python
# database/src/models/ea_project_mapping_models.py

class EAProjectMapping(BaseModel, TimestampMixin):
    """企业架构与项目映射关系表"""
    __tablename__ = "ea_project_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(50), nullable=False, comment="源类型")
    source_id = Column(UUID(as_uuid=True), nullable=False, comment="源ID")
    target_type = Column(String(50), nullable=False, comment="目标类型")
    target_id = Column(UUID(as_uuid=True), nullable=False, comment="目标ID")
    mapping_type = Column(String(50), nullable=False, comment="映射类型")
    sync_enabled = Column(Boolean, default=True, comment="是否启用同步")
    meta_data = Column(JSONB, nullable=True, default=dict)
    
    __table_args__ = (
        Index('idx_ea_project_mapping_source', 'source_type', 'source_id'),
        Index('idx_ea_project_mapping_target', 'target_type', 'target_id'),
    )
```

---

## 🎯 五、使用场景

### 5.1 场景1: 创建架构项目

```python
# 使用示例
async def create_architecture_project_example():
    """创建架构项目示例"""
    integration_service = EAProjectIntegrationService(db, project_client)
    
    # 1. 创建ADM迭代
    iteration = await adm_service.create_iteration({
        "name": "G437项目企业架构设计",
        "description": "化工事业部工厂ERP系统升级推广项目的企业架构设计",
        "iteration_type": "full"
    })
    
    # 2. 从迭代创建项目
    result = await integration_service.create_project_from_adm_iteration(iteration.id)
    
    # 3. 自动创建阶段、任务和里程碑
    # - 9个项目阶段（对应ADM的9个阶段）
    # - 每个阶段的交付物作为任务
    # - 关键交付物作为里程碑
    
    return result
```

### 5.2 场景2: 跟踪架构进度

```python
# 在项目页面查看架构进度
async def view_architecture_progress(project_id: str):
    """在项目页面查看架构进度"""
    # 获取项目
    project = await project_client.get_project(project_id)
    
    # 获取关联的ADM迭代
    iteration_id = project.get("extra_metadata", {}).get("iteration_id")
    if iteration_id:
        iteration = await adm_service.get_iteration(iteration_id)
        
        # 显示架构进度
        return {
            "project": project,
            "architecture": {
                "iteration": iteration,
                "phases": iteration.phases,
                "progress": calculate_architecture_progress(iteration)
            }
        }
```

---

**第一部分完成**  
**下一部分**: 治理集成、工作流集成、前端集成




