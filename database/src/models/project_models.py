"""
项目管理相关数据模型
项目、阶段、里程碑、任务、周报、风险、项目群、计划
"""
from sqlalchemy import (
    Column, String, Integer, Float, Date, Boolean, Text,
    ForeignKey, Enum as SQLEnum, UniqueConstraint, DateTime, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PostgresEnum
import uuid
from enum import Enum

from .base import BaseModel, TimestampMixin


class ProjectStatus(str, Enum):
    """项目状态"""
    PLANNING = "planning"
    ACTIVE = "active"
    DELAYED = "delayed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """任务状态"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MilestoneStatus(str, Enum):
    """里程碑状态"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class PlanTaskStatus(str, Enum):
    """计划任务状态"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class ProgramStatus(str, Enum):
    """项目群状态"""
    PLANNING = "planning"
    ACTIVE = "active"
    DELAYED = "delayed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(BaseModel):
    """项目模型"""
    __tablename__ = "pm_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="项目ID")
    project_code = Column(String(50), unique=True, nullable=False, index=True, comment="项目编码")
    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(
        SQLEnum(ProjectStatus, native_enum=False, 
                values_callable=lambda x: [e.value for e in ProjectStatus]),
        default=ProjectStatus.PLANNING,
        nullable=False,
        index=True,
        comment="项目状态"
    )
    priority = Column(String(20), default="medium", comment="优先级")
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="项目经理ID")
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="填报人ID")
    program_id = Column(UUID(as_uuid=True), ForeignKey("pm_programs.id"), nullable=True, index=True, comment="所属项目群ID")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    budget = Column(Float, nullable=True, comment="预算")
    actual_cost = Column(Float, nullable=True, comment="实际成本")
    progress_percent = Column(Float, default=0.0, comment="进度百分比")
    health_score = Column(Float, default=0.0, comment="健康度评分")
    requires_weekly_report = Column(Boolean, default=False, nullable=False, comment="是否编写周报")
    
    # 重要里程碑日期
    milestone_implementation_start = Column(Date, nullable=True, comment="实施启动日期")
    milestone_solution_confirmation = Column(Date, nullable=True, comment="方案确认日期")
    milestone_delivery_online = Column(Date, nullable=True, comment="交付上线日期")
    milestone_project_acceptance = Column(Date, nullable=True, comment="项目验收日期")
    
    # 关联现有平台服务
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=True, comment="关联工作流ID")
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True, comment="关联知识库ID")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    program = relationship("Program", back_populates="projects")
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    weekly_reports = relationship("WeeklyReport", back_populates="project", cascade="all, delete-orphan")
    monthly_reports = relationship("MonthlyReport", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    basic_data_mappings = relationship("ProjectBasicDataMapping", back_populates="project", cascade="all, delete-orphan")
    plans = relationship("ProjectPlan", back_populates="project", cascade="all, delete-orphan")


class Program(BaseModel):
    """项目群模型"""
    __tablename__ = "pm_programs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="项目群ID")
    program_code = Column(String(50), unique=True, nullable=False, index=True, comment="项目群编码")
    name = Column(String(200), nullable=False, comment="项目群名称")
    description = Column(Text, nullable=True, comment="项目群描述")
    status = Column(
        SQLEnum(ProgramStatus, native_enum=False,
                values_callable=lambda x: [e.value for e in ProgramStatus]),
        default=ProgramStatus.PLANNING,
        nullable=False,
        index=True,
        comment="项目群状态"
    )
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="项目群经理ID")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    budget = Column(Float, nullable=True, comment="项目群预算")
    actual_cost = Column(Float, nullable=True, comment="实际成本")
    progress_percent = Column(Float, default=0.0, comment="整体进度百分比")
    health_score = Column(Float, default=0.0, comment="健康度评分")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=True, comment="项目群分类（从基础数据获取）")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    projects = relationship("Project", back_populates="program", cascade="all, delete-orphan")
    plans = relationship("ProgramPlan", back_populates="program", cascade="all, delete-orphan")
    category = relationship("BasicDataCategory", foreign_keys=[category_id])


class ProgramPlan(BaseModel):
    """项目群计划模型"""
    __tablename__ = "pm_program_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="计划ID")
    program_id = Column(UUID(as_uuid=True), ForeignKey("pm_programs.id"), nullable=False, index=True, comment="项目群ID")
    name = Column(String(200), nullable=False, comment="计划名称")
    description = Column(Text, nullable=True, comment="计划描述")
    version = Column(String(20), default="1.0", nullable=False, comment="计划版本")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    program = relationship("Program", back_populates="plans")
    plan_tasks = relationship("ProgramPlanTask", back_populates="plan", cascade="all, delete-orphan")


class ProgramPlanTask(BaseModel):
    """项目群计划任务模型"""
    __tablename__ = "pm_program_plan_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="任务ID")
    plan_id = Column(UUID(as_uuid=True), ForeignKey("pm_program_plans.id"), nullable=False, index=True, comment="计划ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=True, index=True, comment="关联的项目ID")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=False, comment="任务类型（从基础数据获取）")
    name = Column(String(200), nullable=False, comment="任务名称（从基础数据同步）")
    description = Column(Text, nullable=True, comment="任务描述")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    duration_days = Column(Integer, nullable=True, comment="持续时间（天）")
    dependencies = Column(JSONB, nullable=True, default=list, comment="依赖任务ID列表")
    predecessors = Column(JSONB, nullable=True, default=list, comment="前置任务ID列表")
    assigned_resources = Column(JSONB, nullable=True, default=list, comment="分配的资源ID列表")
    estimated_effort = Column(Float, nullable=True, comment="预估工作量（人天）")
    progress_percent = Column(Float, default=0.0, comment="进度百分比")
    status = Column(
        SQLEnum(PlanTaskStatus, native_enum=False,
                values_callable=lambda x: [e.value for e in PlanTaskStatus]),
        default=PlanTaskStatus.PLANNED,
        nullable=False,
        comment="任务状态"
    )
    is_critical = Column(Boolean, default=False, comment="是否关键任务")
    float_days = Column(Float, nullable=True, comment="浮动时间（天）")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    plan = relationship("ProgramPlan", back_populates="plan_tasks")
    project = relationship("Project", foreign_keys=[project_id])
    category = relationship("BasicDataCategory", foreign_keys=[category_id])


class ProjectPlan(BaseModel):
    """项目计划模型"""
    __tablename__ = "pm_project_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="计划ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    name = Column(String(200), nullable=False, comment="计划名称")
    description = Column(Text, nullable=True, comment="计划描述")
    version = Column(String(20), default="1.0", nullable=False, comment="计划版本")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_baseline = Column(Boolean, default=False, nullable=False, comment="是否基线计划")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    baseline_start_date = Column(Date, nullable=True, comment="基线开始日期")
    baseline_end_date = Column(Date, nullable=True, comment="基线结束日期")
    template_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_templates.id"), nullable=True, comment="基于的模板ID")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="plans")
    plan_tasks = relationship("ProjectPlanTask", back_populates="plan", cascade="all, delete-orphan")
    template = relationship("ProjectTemplate", foreign_keys=[template_id])
    change_logs = relationship("PlanChangeLog", back_populates="plan", cascade="all, delete-orphan")


class PlanChangeLog(BaseModel):
    """计划变更日志模型"""
    __tablename__ = "pm_plan_change_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="变更日志ID")
    plan_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_plans.id"), nullable=False, index=True, comment="计划ID")
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="变更人ID")
    change_type = Column(String(50), nullable=False, comment="变更类型")
    change_description = Column(Text, nullable=True, comment="变更描述")
    change_details = Column(JSONB, nullable=True, default=dict, comment="变更详情")
    before_snapshot = Column(JSONB, nullable=True, comment="变更前快照")
    after_snapshot = Column(JSONB, nullable=True, comment="变更后快照")
    critical_path_changed = Column(Boolean, default=False, comment="关键路径是否变更")
    affected_tasks = Column(JSONB, nullable=True, default=list, comment="受影响的任务ID列表")
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), comment="变更时间")
    
    # 关系
    plan = relationship("ProjectPlan", back_populates="change_logs")
    user = relationship("User", foreign_keys=[changed_by])


class ProjectPlanTask(BaseModel):
    """项目计划任务模型"""
    __tablename__ = "pm_project_plan_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="任务ID")
    plan_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_plans.id"), nullable=False, index=True, comment="计划ID")
    phase_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_phases.id"), nullable=True, index=True, comment="阶段ID")
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("pm_milestones.id"), nullable=True, index=True, comment="里程碑ID")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=False, comment="任务类型（从基础数据获取）")
    name = Column(String(200), nullable=False, comment="任务名称（从基础数据同步）")
    description = Column(Text, nullable=True, comment="任务描述")
    start_date = Column(Date, nullable=True, comment="计划开始日期")
    end_date = Column(Date, nullable=True, comment="计划结束日期")
    duration_days = Column(Integer, nullable=True, comment="持续时间（天）")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    dependencies = Column(JSONB, nullable=True, default=list, comment="依赖关系列表：[{task_id, type, lag_days}]")
    predecessors = Column(JSONB, nullable=True, default=list, comment="前置任务ID列表")
    successors = Column(JSONB, nullable=True, default=list, comment="后续任务ID列表")
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="负责人ID")
    assigned_resources = Column(JSONB, nullable=True, default=list, comment="分配的资源ID列表")
    estimated_hours = Column(Float, nullable=True, comment="预估工时（小时）")
    actual_hours = Column(Float, nullable=True, comment="实际工时（小时）")
    estimated_effort = Column(Float, nullable=True, comment="预估工作量（人天）")
    progress_percent = Column(Float, default=0.0, comment="进度百分比")
    status = Column(
        SQLEnum(PlanTaskStatus, native_enum=False,
                values_callable=lambda x: [e.value for e in PlanTaskStatus]),
        default=PlanTaskStatus.PLANNED,
        nullable=False,
        comment="任务状态"
    )
    priority = Column(String(20), default="medium", comment="优先级")
    is_critical = Column(Boolean, default=False, comment="是否关键任务")
    early_start = Column(Date, nullable=True, comment="最早开始时间")
    early_finish = Column(Date, nullable=True, comment="最早结束时间")
    late_start = Column(Date, nullable=True, comment="最晚开始时间")
    late_finish = Column(Date, nullable=True, comment="最晚结束时间")
    total_float = Column(Float, nullable=True, comment="总浮动时间（天）")
    free_float = Column(Float, nullable=True, comment="自由浮动时间（天）")
    actual_task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id"), nullable=True, comment="关联的实际任务ID")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    plan = relationship("ProjectPlan", back_populates="plan_tasks")
    phase = relationship("ProjectPhase", foreign_keys=[phase_id])
    milestone = relationship("Milestone", foreign_keys=[milestone_id])
    category = relationship("BasicDataCategory", foreign_keys=[category_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    actual_task = relationship("Task", foreign_keys=[actual_task_id])


class ProjectTemplate(BaseModel):
    """项目模板模型"""
    __tablename__ = "pm_project_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="模板ID")
    template_code = Column(String(50), unique=True, nullable=False, index=True, comment="模板编码")
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=True, comment="模板分类（从基础数据获取）")
    template_structure = Column(JSONB, nullable=True, default=dict, comment="模板结构（包含阶段、里程碑、任务模板）")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    category = relationship("BasicDataCategory", foreign_keys=[category_id])
    plans = relationship("ProjectPlan", back_populates="template", foreign_keys="ProjectPlan.template_id")


class ProjectPhase(BaseModel):
    """项目阶段模型"""
    __tablename__ = "pm_project_phases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="阶段ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=False, index=True, comment="基础数据分类ID（项目阶段）")
    name = Column(String(200), nullable=False, comment="阶段名称（从基础数据同步）")
    description = Column(Text, nullable=True, comment="阶段描述")
    sequence = Column(Integer, nullable=False, default=0, comment="阶段顺序")
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    progress_percent = Column(Float, default=0.0, comment="进度百分比")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="phases")
    category = relationship("BasicDataCategory", foreign_keys=[category_id], backref="project_phases")
    milestones = relationship("Milestone", back_populates="phase", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="phase", cascade="all, delete-orphan")
    plan_tasks = relationship("ProjectPlanTask", back_populates="phase", cascade="all, delete-orphan")


class Milestone(BaseModel):
    """里程碑模型"""
    __tablename__ = "pm_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="里程碑ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    phase_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_phases.id"), nullable=True, index=True, comment="阶段ID")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=False, index=True, comment="基础数据分类ID（里程碑）")
    name = Column(String(200), nullable=False, comment="里程碑名称（从基础数据同步）")
    description = Column(Text, nullable=True, comment="里程碑描述")
    target_date = Column(Date, nullable=True, comment="目标日期")
    actual_date = Column(Date, nullable=True, comment="实际完成日期")
    status = Column(
        SQLEnum(MilestoneStatus, native_enum=False,
                values_callable=lambda x: [e.value for e in MilestoneStatus]),
        default=MilestoneStatus.PLANNED,
        nullable=False,
        comment="里程碑状态"
    )
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="milestones")
    phase = relationship("ProjectPhase", back_populates="milestones")
    category = relationship("BasicDataCategory", foreign_keys=[category_id], backref="milestones")
    plan_tasks = relationship("ProjectPlanTask", back_populates="milestone", cascade="all, delete-orphan")


class Task(BaseModel):
    """任务模型"""
    __tablename__ = "pm_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="任务ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    phase_id = Column(UUID(as_uuid=True), ForeignKey("pm_project_phases.id"), nullable=True, index=True, comment="阶段ID")
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("pm_milestones.id"), nullable=True, index=True, comment="里程碑ID")
    name = Column(String(200), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(
        SQLEnum(TaskStatus, native_enum=False,
                values_callable=lambda x: [e.value for e in TaskStatus]),
        default=TaskStatus.TODO,
        nullable=False,
        index=True,
        comment="任务状态"
    )
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="负责人ID")
    start_date = Column(Date, nullable=True, comment="开始日期")
    due_date = Column(Date, nullable=True, comment="截止日期")
    completed_date = Column(Date, nullable=True, comment="完成日期")
    estimated_hours = Column(Float, nullable=True, comment="预估工时")
    actual_hours = Column(Float, nullable=True, comment="实际工时")
    progress_percent = Column(Float, default=0.0, comment="进度百分比")
    dependencies = Column(JSONB, nullable=True, default=list, comment="任务依赖关系")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="tasks")
    phase = relationship("ProjectPhase", back_populates="tasks")
    plan_tasks = relationship("ProjectPlanTask", back_populates="actual_task", foreign_keys="ProjectPlanTask.actual_task_id")


class WeeklyReport(BaseModel):
    """周报模型"""
    __tablename__ = "pm_weekly_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="周报ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    week_number = Column(Integer, nullable=True, comment="周数")
    report_date = Column(Date, nullable=False, index=True, comment="报告日期")
    content_plan = Column(Text, nullable=True, comment="计划内容")
    content_achievement = Column(Text, nullable=True, comment="成果内容")
    key_tasks_completed = Column(JSONB, nullable=True, default=list, comment="关键任务完成情况")
    issues_risks = Column(Text, nullable=True, comment="问题与风险")
    next_week_plan = Column(Text, nullable=True, comment="下周计划")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="weekly_reports")


class MonthlyReport(BaseModel):
    """月报模型（独立数据表）"""
    __tablename__ = "pm_monthly_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="月报ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    report_year = Column(Integer, nullable=False, index=True, comment="报告年份")
    report_month = Column(Integer, nullable=False, index=True, comment="报告月份（1-12）")
    summary = Column(Text, nullable=True, comment="月度总结")
    achievements = Column(Text, nullable=True, comment="月度成果")
    challenges = Column(Text, nullable=True, comment="挑战与问题")
    next_month_plan = Column(Text, nullable=True, comment="下月计划")
    progress_percent = Column(Float, default=0.0, comment="月度进度百分比")
    key_milestones = Column(JSONB, nullable=True, default=list, comment="关键里程碑完成情况")
    risk_summary = Column(Text, nullable=True, comment="风险汇总")
    resource_summary = Column(Text, nullable=True, comment="资源使用情况")
    extra_metadata = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="monthly_reports")
    
    # 唯一约束：同一项目同一月份只能有一份月报
    __table_args__ = (
        UniqueConstraint('project_id', 'report_year', 'report_month', name='uq_project_monthly_report'),
    )


class ProjectMemberRole(str, Enum):
    """项目成员角色"""
    MANAGER = "manager"      # 项目经理（所有权限）
    MEMBER = "member"        # 项目成员（创建、编辑、查看）
    VIEWER = "viewer"        # 查看者（只能查看）


class ProjectMember(BaseModel):
    """项目成员模型（项目级别权限）"""
    __tablename__ = "pm_project_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="成员ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    role = Column(
        String(20),
        default='member',
        nullable=False,
        index=True,
        comment="成员角色"
    )
    joined_at = Column(Date, nullable=True, comment="加入日期")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="members")
    
    # 唯一约束：同一用户在同一项目中只能有一个角色
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )


class Risk(BaseModel):
    """风险模型"""
    __tablename__ = "pm_risks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="风险ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    name = Column(String(200), nullable=False, comment="风险名称")
    description = Column(Text, nullable=True, comment="风险描述")
    risk_level = Column(String(20), nullable=False, default="medium", comment="风险等级")
    probability = Column(Float, nullable=True, comment="发生概率")
    impact = Column(String(20), nullable=True, comment="影响程度")
    mitigation_plan = Column(Text, nullable=True, comment="应对措施")
    status = Column(String(20), default="open", comment="风险状态")
    extra_metadata = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    project = relationship("Project", back_populates="risks")
