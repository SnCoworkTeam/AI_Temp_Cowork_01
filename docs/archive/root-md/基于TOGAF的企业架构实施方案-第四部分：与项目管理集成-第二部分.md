# 基于TOGAF的企业架构实施方案 - 第四部分：与项目管理集成

## 第二部分：治理集成、工作流集成与前端集成

**报告日期**: 2025-12-07  
**承接**: 第一部分集成策略与映射关系

---

## 📋 第二部分概述

本部分详细说明架构治理与项目治理的集成、工作流自动化集成以及前端界面的统一展示。

---

## 🏛️ 一、治理集成

### 1.1 架构治理与项目治理统一

#### 1.1.1 治理框架集成

```python
# metadata-service/src/services/unified_governance_service.py

class UnifiedGovernanceService:
    """统一治理服务（架构治理 + 项目治理）"""
    
    def __init__(self, db: Session, architecture_governance_service, project_governance_service):
        self.db = db
        self.arch_governance = architecture_governance_service
        self.proj_governance = project_governance_service
    
    async def validate_project_architecture_compliance(
        self, project_id: str
    ) -> Dict:
        """验证项目的架构合规性"""
        # 获取项目
        project = await self.proj_governance.get_project(project_id)
        
        # 获取关联的ADM迭代
        iteration_id = project.get("extra_metadata", {}).get("iteration_id")
        if not iteration_id:
            return {"compliant": True, "message": "项目未关联架构迭代"}
        
        # 获取迭代关联的架构实体
        iteration = self.db.query(ADMIteration).filter(
            ADMIteration.id == UUID(iteration_id)
        ).first()
        
        violations = []
        
        # 检查各阶段的架构合规性
        for adm_phase in iteration.phases:
            # 获取阶段创建的架构实体
            phase_entities = await self._get_phase_entities(adm_phase)
            
            for entity in phase_entities:
                # 验证架构合规性
                compliance = await self.arch_governance.validate_entity_compliance(
                    entity["type"], entity["id"]
                )
                
                if not compliance["compliant"]:
                    violations.extend([
                        {
                            "phase": adm_phase.phase_name,
                            "entity": entity,
                            "violations": compliance["violations"]
                        }
                    ])
        
        return {
            "project_id": project_id,
            "iteration_id": iteration_id,
            "compliant": len(violations) == 0,
            "violations": violations,
            "compliance_rate": self._calculate_compliance_rate(violations)
        }
    
    async def create_governance_checklist(self, project_id: str) -> Dict:
        """创建治理检查清单"""
        project = await self.proj_governance.get_project(project_id)
        iteration_id = project.get("extra_metadata", {}).get("iteration_id")
        
        if not iteration_id:
            return {"checklist": []}
        
        checklist = []
        
        # 架构原则检查
        principles = await self.arch_governance.get_principles()
        for principle in principles:
            checklist.append({
                "type": "architecture_principle",
                "principle_id": str(principle.id),
                "principle_name": principle.name,
                "category": principle.category,
                "status": "pending",
                "check_items": await self._get_principle_check_items(principle)
            })
        
        # 项目标准检查
        project_standards = await self.proj_governance.get_project_standards()
        for standard in project_standards:
            checklist.append({
                "type": "project_standard",
                "standard_id": str(standard.id),
                "standard_name": standard.name,
                "status": "pending",
                "check_items": await self._get_standard_check_items(standard)
            })
        
        return {
            "project_id": project_id,
            "checklist": checklist,
            "total_items": len(checklist)
        }
```

### 1.2 架构变更与项目变更管理

#### 1.2.1 变更请求集成

```python
# metadata-service/src/services/change_management_integration_service.py

class ChangeManagementIntegrationService:
    """变更管理集成服务"""
    
    async def create_architecture_change_request(
        self, change_data: Dict
    ) -> Dict:
        """创建架构变更请求，同时创建项目变更请求"""
        # 创建架构变更请求
        arch_change = await self.arch_change_service.create_change_request(change_data)
        
        # 如果变更影响项目，创建项目变更请求
        if change_data.get("affects_project", False):
            project_id = change_data.get("project_id")
            if project_id:
                project_change_data = {
                    "project_id": project_id,
                    "change_type": "architecture_change",
                    "title": f"架构变更: {change_data.get('title')}",
                    "description": change_data.get("description"),
                    "priority": change_data.get("priority", "medium"),
                    "extra_metadata": {
                        "architecture_change_id": str(arch_change.id),
                        "entity_type": change_data.get("entity_type"),
                        "entity_id": change_data.get("entity_id")
                    }
                }
                
                project_change = await self.project_change_service.create_change_request(
                    project_change_data
                )
                
                # 建立关联
                arch_change.meta_data = arch_change.meta_data or {}
                arch_change.meta_data["project_change_id"] = project_change["id"]
                self.db.commit()
        
        return {
            "architecture_change": arch_change,
            "project_change": project_change if "project_change" in locals() else None
        }
    
    async def approve_change_with_impact_analysis(
        self, change_request_id: str, approver_id: str
    ) -> Dict:
        """批准变更并进行影响分析"""
        # 获取变更请求
        change_request = await self.arch_change_service.get_change_request(change_request_id)
        
        # 进行影响分析
        impact_analysis = await self.arch_service.analyze_impact(
            change_request["entity_id"],
            change_request["entity_type"]
        )
        
        # 如果影响较大，需要项目审批
        if impact_analysis["risk_level"] in ["high", "critical"]:
            # 创建项目变更请求
            project_change = await self._create_project_change_for_approval(
                change_request, impact_analysis
            )
            
            return {
                "change_request_id": change_request_id,
                "impact_analysis": impact_analysis,
                "requires_project_approval": True,
                "project_change_id": project_change["id"]
            }
        
        # 直接批准架构变更
        await self.arch_change_service.approve_change(change_request_id, approver_id)
        
        return {
            "change_request_id": change_request_id,
            "impact_analysis": impact_analysis,
            "approved": True
        }
```

---

## 🔄 二、工作流集成

### 2.1 ADM阶段工作流自动化

#### 2.1.1 阶段工作流模板

```python
# workflow-engine/src/workflows/adm_phase_workflow.py

class ADMPhaseWorkflow:
    """ADM阶段工作流"""
    
    PHASE_WORKFLOWS = {
        "A": {
            "name": "架构愿景阶段工作流",
            "steps": [
                {
                    "step": "stakeholder_analysis",
                    "name": "利益相关者分析",
                    "agent": "stakeholder_analysis_agent",
                    "inputs": ["project_context", "business_requirements"],
                    "outputs": ["stakeholder_map"]
                },
                {
                    "step": "current_state_assessment",
                    "name": "现状评估",
                    "agent": "architecture_assessment_agent",
                    "inputs": ["existing_systems", "current_processes"],
                    "outputs": ["current_state_report"]
                },
                {
                    "step": "gap_analysis",
                    "name": "差距分析",
                    "agent": "gap_analysis_agent",
                    "inputs": ["current_state_report", "target_state"],
                    "outputs": ["gap_analysis_report"]
                },
                {
                    "step": "create_vision_document",
                    "name": "创建架构愿景文档",
                    "agent": "document_generation_agent",
                    "inputs": ["stakeholder_map", "gap_analysis_report"],
                    "outputs": ["architecture_vision_document"]
                }
            ]
        },
        "B": {
            "name": "业务架构阶段工作流",
            "steps": [
                {
                    "step": "identify_business_capabilities",
                    "name": "识别业务能力",
                    "agent": "capability_identification_agent",
                    "inputs": ["business_requirements", "stakeholder_map"],
                    "outputs": ["business_capabilities"]
                },
                {
                    "step": "model_business_processes",
                    "name": "建模业务流程",
                    "agent": "process_modeling_agent",
                    "inputs": ["business_capabilities", "current_processes"],
                    "outputs": ["business_process_models"]
                },
                {
                    "step": "create_business_architecture_document",
                    "name": "创建业务架构文档",
                    "agent": "document_generation_agent",
                    "inputs": ["business_capabilities", "business_process_models"],
                    "outputs": ["business_architecture_document"]
                }
            ]
        }
        # ... 其他阶段的工作流
    }
    
    async def create_phase_workflow(self, phase_letter: str, project_id: str, phase_id: str):
        """为ADM阶段创建工作流"""
        workflow_def = self.PHASE_WORKFLOWS.get(phase_letter)
        if not workflow_def:
            raise ValueError(f"未找到阶段{phase_letter}的工作流定义")
        
        # 创建工作流定义
        workflow_data = {
            "name": workflow_def["name"],
            "description": f"ADM阶段{phase_letter}的自动化工作流",
            "steps": workflow_def["steps"],
            "extra_metadata": {
                "adm_phase": phase_letter,
                "project_id": project_id,
                "phase_id": phase_id,
                "framework": "TOGAF"
            }
        }
        
        workflow = await self.workflow_service.create_workflow(workflow_data)
        
        # 关联到项目阶段
        await self.project_service.update_phase_workflow(phase_id, workflow["id"])
        
        return workflow
```

### 2.2 任务自动创建工作流

#### 2.2.1 从工作流步骤创建任务

```python
async def create_tasks_from_workflow_steps(
    self, workflow_id: str, project_id: str, phase_id: str
):
    """从工作流步骤创建项目任务"""
    workflow = await self.workflow_service.get_workflow(workflow_id)
    
    tasks = []
    for i, step in enumerate(workflow["steps"]):
        task_data = {
            "project_id": project_id,
            "phase_id": phase_id,
            "name": step["name"],
            "description": f"工作流步骤: {step['step']}",
            "status": "todo",
            "sequence": i + 1,
            "extra_metadata": {
                "workflow_id": workflow_id,
                "workflow_step": step["step"],
                "agent": step.get("agent"),
                "inputs": step.get("inputs", []),
                "outputs": step.get("outputs", [])
            }
        }
        
        task = await self.project_service.create_task(task_data)
        tasks.append(task)
    
    return tasks
```

### 2.3 工作流执行与任务状态同步

```python
async def sync_workflow_execution_to_tasks(
    self, workflow_execution_id: str
):
    """同步工作流执行状态到任务"""
    execution = await self.workflow_service.get_execution(workflow_execution_id)
    
    # 获取关联的任务
    tasks = await self.project_service.get_tasks_by_workflow(execution["workflow_id"])
    
    for step_execution in execution["step_executions"]:
        # 找到对应的任务
        task = next(
            (t for t in tasks if t["extra_metadata"].get("workflow_step") == step_execution["step"]),
            None
        )
        
        if task:
            # 同步状态
            task_status = self._convert_workflow_status(step_execution["status"])
            await self.project_service.update_task_status(task["id"], task_status)
            
            # 如果步骤完成，更新任务完成日期
            if step_execution["status"] == "completed":
                await self.project_service.update_task_completion(
                    task["id"],
                    step_execution["completed_at"]
                )
```

---

## 🎨 三、前端集成

### 3.1 项目页面中的架构视图

#### 3.1.1 项目详情页增强

```typescript
// web-ui/src/app/admin/projects/[id]/page.tsx

'use client';

import { useState, useEffect } from 'react';
import { Tabs, Card, Timeline, Progress } from 'antd';
import { ApartmentOutlined, CheckCircleOutlined } from '@ant-design/icons';

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const [project, setProject] = useState<any>(null);
  const [architecture, setArchitecture] = useState<any>(null);

  useEffect(() => {
    loadProject();
    loadArchitecture();
  }, [params.id]);

  const loadArchitecture = async () => {
    if (!project?.extra_metadata?.iteration_id) return;
    
    const response = await fetch(
      `/api/enterprise-architecture/iterations/${project.extra_metadata.iteration_id}`
    );
    const data = await response.json();
    setArchitecture(data);
  };

  const tabItems = [
    {
      key: 'overview',
      label: '项目概览',
      children: <ProjectOverviewTab project={project} />
    },
    {
      key: 'architecture',
      label: '架构视图',
      children: <ArchitectureViewTab 
        project={project} 
        architecture={architecture} 
      />
    },
    {
      key: 'phases',
      label: '项目阶段',
      children: <ProjectPhasesTab project={project} />
    },
    {
      key: 'tasks',
      label: '任务管理',
      children: <TasksTab project={project} />
    },
    {
      key: 'governance',
      label: '治理检查',
      children: <GovernanceTab project={project} />
    }
  ];

  return (
    <div className="project-detail-page">
      <h1>{project?.name}</h1>
      <Tabs items={tabItems} />
    </div>
  );
}
```

#### 3.1.2 架构视图标签页

```typescript
// web-ui/src/components/projects/ArchitectureViewTab.tsx

'use client';

import { Card, Timeline, Progress, Tag, Button } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';

interface ArchitectureViewTabProps {
  project: any;
  architecture: any;
}

export default function ArchitectureViewTab({ project, architecture }: ArchitectureViewTabProps) {
  if (!architecture) {
    return <div>项目未关联架构迭代</div>;
  }

  const admPhases = architecture.phases || [];
  
  const timelineItems = admPhases.map((phase: any) => ({
    color: phase.status === 'completed' ? 'green' : 
           phase.status === 'in_progress' ? 'blue' : 'gray',
    dot: phase.status === 'completed' ? <CheckCircleOutlined /> : <ClockCircleOutlined />,
    children: (
      <Card size="small" title={`阶段${phase.phase_letter}: ${phase.phase_name}`}>
        <div>
          <Tag color={phase.status === 'completed' ? 'green' : 'blue'}>
            {phase.status === 'completed' ? '已完成' : 
             phase.status === 'in_progress' ? '进行中' : '未开始'}
          </Tag>
          <Progress 
            percent={phase.progress_percent || 0} 
            size="small" 
            style={{ marginTop: 8 }}
          />
          {phase.deliverables && (
            <div style={{ marginTop: 8 }}>
              <strong>交付物:</strong>
              <ul>
                {phase.deliverables.map((deliverable: string, idx: number) => (
                  <li key={idx}>{deliverable}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </Card>
    )
  }));

  return (
    <div className="architecture-view-tab">
      <Card title="TOGAF ADM过程" style={{ marginBottom: 16 }}>
        <Timeline items={timelineItems} mode="left" />
      </Card>
      
      <Card title="架构进度总览">
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="已完成阶段"
              value={admPhases.filter((p: any) => p.status === 'completed').length}
              suffix={`/ ${admPhases.length}`}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="总体进度"
              value={architecture.progress_percent || 0}
              suffix="%"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="架构合规率"
              value={architecture.compliance_rate || 0}
              suffix="%"
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
}
```

### 3.2 架构页面中的项目视图

#### 3.2.1 架构迭代详情页增强

```typescript
// web-ui/src/app/enterprise-architecture/iterations/[id]/page.tsx

'use client';

import { Card, Tabs, Tag, Button, Descriptions } from 'antd';
import { ProjectOutlined, LinkOutlined } from '@ant-design/icons';

export default function ADMIterationDetailPage({ params }: { params: { id: string } }) {
  const [iteration, setIteration] = useState<any>(null);
  const [project, setProject] = useState<any>(null);

  useEffect(() => {
    loadIteration();
  }, [params.id]);

  const loadIteration = async () => {
    const response = await fetch(`/api/enterprise-architecture/iterations/${params.id}`);
    const data = await response.json();
    setIteration(data);
    
    // 如果有关联项目，加载项目信息
    if (data.meta_data?.project_id) {
      loadProject(data.meta_data.project_id);
    }
  };

  const loadProject = async (projectId: string) => {
    const response = await fetch(`/api/v1/projects/${projectId}`);
    const data = await response.json();
    setProject(data);
  };

  const tabItems = [
    {
      key: 'overview',
      label: '迭代概览',
      children: <IterationOverviewTab iteration={iteration} />
    },
    {
      key: 'phases',
      label: 'ADM阶段',
      children: <ADMPhasesTab iteration={iteration} />
    },
    {
      key: 'project',
      label: '关联项目',
      children: project ? (
        <ProjectLinkTab project={project} />
      ) : (
        <div>
          <p>此迭代尚未关联项目</p>
          <Button 
            type="primary" 
            onClick={() => createProjectFromIteration(iteration.id)}
          >
            创建项目
          </Button>
        </div>
      )
    }
  ];

  return (
    <div className="adm-iteration-detail-page">
      <Card 
        title={
          <div>
            <span>{iteration?.name}</span>
            {project && (
              <Tag 
                icon={<ProjectOutlined />} 
                color="blue" 
                style={{ marginLeft: 8 }}
              >
                已关联项目: {project.name}
              </Tag>
            )}
          </div>
        }
        extra={
          project && (
            <Button 
              type="link" 
              icon={<LinkOutlined />}
              href={`/admin/projects/${project.id}`}
            >
              查看项目详情
            </Button>
          )
        }
      >
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
}
```

### 3.3 统一仪表板

#### 3.3.1 架构项目仪表板

```typescript
// web-ui/src/app/dashboard/architecture-projects/page.tsx

'use client';

import { Row, Col, Card, Statistic, Table, Progress } from 'antd';
import { ProjectOutlined, ApartmentOutlined, CheckCircleOutlined } from '@ant-design/icons';

export default function ArchitectureProjectsDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    // 加载统计信息
    const statsResponse = await fetch('/api/enterprise-architecture/projects/stats');
    const statsData = await statsResponse.json();
    setStats(statsData);
    
    // 加载项目列表
    const projectsResponse = await fetch('/api/enterprise-architecture/projects');
    const projectsData = await projectsResponse.json();
    setProjects(projectsData.items || []);
  };

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name'
    },
    {
      title: '架构迭代',
      dataIndex: 'iteration_name',
      key: 'iteration_name'
    },
    {
      title: 'ADM阶段进度',
      key: 'phase_progress',
      render: (_: any, record: any) => (
        <Progress 
          percent={record.phase_progress} 
          size="small"
          format={(percent) => `${record.completed_phases}/${record.total_phases}`}
        />
      )
    },
    {
      title: '架构合规率',
      dataIndex: 'compliance_rate',
      key: 'compliance_rate',
      render: (rate: number) => `${rate}%`
    },
    {
      title: '项目状态',
      dataIndex: 'project_status',
      key: 'project_status',
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>
    }
  ];

  return (
    <div className="architecture-projects-dashboard">
      <h1>架构项目仪表板</h1>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="架构项目总数"
              value={stats?.total_projects || 0}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="进行中的迭代"
              value={stats?.active_iterations || 0}
              prefix={<ApartmentOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成阶段"
              value={stats?.completed_phases || 0}
              suffix={`/ ${stats?.total_phases || 0}`}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均合规率"
              value={stats?.avg_compliance_rate || 0}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>
      
      {/* 项目列表 */}
      <Card title="架构项目列表">
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="project_id"
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}
```

---

## 📊 四、API集成端点

### 4.1 集成API端点

```python
# metadata-service/src/api/ea_project_integration.py

router = APIRouter(prefix="/api/enterprise-architecture/projects", tags=["架构项目集成"])

@router.post("/create-from-iteration/{iteration_id}")
async def create_project_from_iteration(
    iteration_id: str,
    db: Session = Depends(get_db)
):
    """从ADM迭代创建项目"""
    service = EAProjectIntegrationService(db, project_client)
    result = await service.create_project_from_adm_iteration(UUID(iteration_id))
    return result

@router.get("/stats")
async def get_architecture_projects_stats(db: Session = Depends(get_db)):
    """获取架构项目统计信息"""
    service = EAProjectIntegrationService(db, project_client)
    stats = await service.get_statistics()
    return stats

@router.get("")
async def list_architecture_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取架构项目列表"""
    service = EAProjectIntegrationService(db, project_client)
    projects = await service.list_architecture_projects(skip, limit)
    return projects

@router.post("/sync/{iteration_id}")
async def sync_iteration_project(
    iteration_id: str,
    db: Session = Depends(get_db)
):
    """同步迭代和项目进度"""
    service = EAProjectIntegrationService(db, project_client)
    result = await service.sync_progress(UUID(iteration_id))
    return result
```

---

**第二部分完成**  
**下一部分**: 实施检查清单和使用指南




