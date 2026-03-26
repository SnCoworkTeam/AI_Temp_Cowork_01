"""
协调整个平台的自动化调试过程

功能：
1. 调试任务管理
2. 修复决策引擎
3. 人工决策接口
4. 平台集成接口
"""
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from collections import deque
import traceback

from .platform_error_analyzer import (
    ErrorAnalysis, ErrorCategory, ErrorType, get_error_analyzer, analyze_error
)
from .platform_fix_strategies import (
    FixResult, FixStrategyConfig, get_fix_strategy_manager, apply_fix
)

logger = logging.getLogger(__name__)


class DebugTaskStatus(Enum):
    """调试任务状态"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    FIXING = "fixing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DecisionType(Enum):
    """决策类型"""
    AUTO_FIX = "auto_fix"
    MANUAL_REVIEW = "manual_review"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    ROLLBACK = "rollback"


class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DebugTask:
    """调试任务"""
    task_id: str
    error_report: Dict[str, Any]
    status: DebugTaskStatus = DebugTaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_analysis: Optional[ErrorAnalysis] = None
    fix_result: Optional[FixResult] = None
    decision: Optional[Dict[str, Any]] = None
    approval_required: bool = False
    approval_status: Optional[str] = None
    approver: Optional[str] = None
    execution_plan: Optional[Dict[str, Any]] = None
    resource_allocation: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixPlan:
    """修复计划"""
    plan_id: str
    strategy: str
    steps: List[Dict[str, Any]]
    estimated_time: float
    risk_level: RiskLevel
    impact_assessment: Dict[str, Any]
    rollback_plan: Optional[Dict[str, Any]] = None
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DecisionPoint:
    """决策点"""
    decision_id: str
    task_id: str
    decision_type: DecisionType
    title: str
    description: str
    options: List[Dict[str, Any]]
    recommendation: Optional[str] = None
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_maker: Optional[str] = None


class DebugOrchestrator:
    """调试协调器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.error_analyzer = get_error_analyzer()
        self.fix_strategy_manager = get_fix_strategy_manager()
        
        # 任务管理
        self.tasks: Dict[str, DebugTask] = {}
        self.task_queue: deque = deque()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # 决策管理
        self.decision_points: Dict[str, DecisionPoint] = {}
        self.decision_history: List[Dict[str, Any]] = []
        
        # 平台集成
        self.service_urls = {
            "mcp-gateway": self.config.get("mcp_gateway_url", "http://localhost:8001"),
            "workflow-engine": self.config.get("workflow_engine_url", "http://localhost:8002"),
            "auth-service": self.config.get("auth_service_url", "http://localhost:8003"),
            "knowledge-base": self.config.get("knowledge_base_url", "http://localhost:8004"),
            "web-ui": self.config.get("web_ui_url", "http://localhost:3000"),
        }
        
        # 资源管理
        self.resource_limits = {
            "max_concurrent_tasks": self.config.get("max_concurrent_tasks", 10),
            "max_retries": self.config.get("max_retries", 3),
            "task_timeout": self.config.get("task_timeout", 300),
        }
    
    # ==================== 调试任务管理 ====================
    
    async def submit_error_report(
        self,
        error_report: Dict[str, Any],
        priority: str = "normal"
    ) -> str:
        """
        接收平台各服务的错误报告
        
        Args:
            error_report: 错误报告，包含错误消息、堆栈跟踪、上下文等
            priority: 任务优先级 (low, normal, high, critical)
        
        Returns:
            任务ID
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        task = DebugTask(
            task_id=task_id,
            error_report=error_report,
            status=DebugTaskStatus.PENDING,
            metadata={"priority": priority}
        )
        
        self.tasks[task_id] = task
        self.task_queue.append((priority, task_id))
        
        logger.info(f"Error report submitted: {task_id}, priority: {priority}")
        
        # 如果任务队列未满，立即开始处理
        if len(self.active_tasks) < self.resource_limits["max_concurrent_tasks"]:
            asyncio.create_task(self._process_task(task_id))
        
        return task_id
    
    async def _process_task(self, task_id: str):
        """处理调试任务"""
        if task_id in self.active_tasks:
            return
        
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return
        
        async def task_processor():
            try:
                # 更新状态
                task.status = DebugTaskStatus.ANALYZING
                task.updated_at = datetime.now()
                
                # 1. 错误分析
                error_analysis = await self._analyze_error(task)
                task.error_analysis = error_analysis
                
                # 2. 修复决策
                task.status = DebugTaskStatus.DECIDING
                decision, fix_plan = await self._make_fix_decision(error_analysis, task)
                task.decision = decision
                task.execution_plan = asdict(fix_plan) if fix_plan else None
                
                # 3. 检查是否需要人工审批
                if decision.get("requires_approval", False):
                    task.status = DebugTaskStatus.WAITING_APPROVAL
                    task.approval_required = True
                    await self._create_decision_point(task_id, decision, fix_plan)
                    return
                
                # 4. 执行修复
                task.status = DebugTaskStatus.FIXING
                fix_result = await self._execute_fix(error_analysis, fix_plan, task)
                task.fix_result = fix_result
                
                # 5. 更新状态
                if fix_result.success:
                    task.status = DebugTaskStatus.COMPLETED
                else:
                    task.status = DebugTaskStatus.FAILED
                
                task.updated_at = datetime.now()
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {str(e)}", exc_info=True)
                task.status = DebugTaskStatus.FAILED
                task.metadata["error"] = str(e)
                task.updated_at = datetime.now()
            finally:
                # 从活动任务中移除
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                # 处理下一个任务
                if self.task_queue:
                    _, next_task_id = self.task_queue.popleft()
                    if next_task_id in self.tasks:
                        asyncio.create_task(self._process_task(next_task_id))
        
        self.active_tasks[task_id] = asyncio.create_task(task_processor())
    
    async def _analyze_error(self, task: DebugTask) -> ErrorAnalysis:
        """分配调试任务给相应分析器"""
        error_report = task.error_report
        
        error_message = error_report.get("error_message", "")
        error_traceback = error_report.get("error_traceback")
        context = error_report.get("context", {})
        metadata = error_report.get("metadata", {})
        
        # 使用错误分析器分析
        analysis = analyze_error(
            error_message=error_message,
            error_traceback=error_traceback,
            context=context,
            metadata=metadata
        )
        
        return analysis
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "error_analysis": self.error_analyzer.to_dict(task.error_analysis) if task.error_analysis else None,
            "fix_result": asdict(task.fix_result) if task.fix_result else None,
            "decision": task.decision,
            "approval_required": task.approval_required,
            "approval_status": task.approval_status,
            "execution_plan": task.execution_plan,
            "metadata": task.metadata
        }
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        tasks = tasks[:limit]
        
        return [self.get_task_status(t.task_id) for t in tasks]
    
    # ==================== 修复决策引擎 ====================
    
    async def _make_fix_decision(
        self,
        error_analysis: ErrorAnalysis,
        task: DebugTask
    ) -> Tuple[Dict[str, Any], Optional[FixPlan]]:
        """
        评估修复方案的可行性、计算风险和影响、选择最优修复策略
        """
        # 1. 评估修复可行性
        feasibility = await self._assess_fix_feasibility(error_analysis)
        
        # 2. 计算修复风险和影响
        risk_assessment = self._calculate_fix_risk(error_analysis)
        impact_assessment = self._assess_fix_impact(error_analysis)
        
        # 3. 选择修复策略
        strategy_config = self._select_fix_strategy(error_analysis, risk_assessment)
        
        # 4. 生成修复计划
        fix_plan = await self._generate_fix_plan(
            error_analysis, strategy_config, risk_assessment, impact_assessment
        )
        
        # 5. 决定是否需要人工审批
        requires_approval = self._requires_approval(risk_assessment, impact_assessment)
        
        decision = {
            "feasibility": feasibility,
            "risk_level": risk_assessment["level"],
            "impact_level": impact_assessment["level"],
            "strategy": strategy_config.get("strategy_name"),
            "requires_approval": requires_approval,
            "auto_fix_enabled": not requires_approval,
            "decision_time": datetime.now().isoformat()
        }
        
        return decision, fix_plan
    
    async def _assess_fix_feasibility(
        self,
        error_analysis: ErrorAnalysis
    ) -> Dict[str, Any]:
        """评估修复方案的可行性"""
        feasibility_score = 0.0
        factors = []
        
        # 基于错误类别
        category_scores = {
            ErrorCategory.MCP_TOOL: 0.8,
            ErrorCategory.WORKFLOW_ENGINE: 0.7,
            ErrorCategory.KNOWLEDGE_BASE: 0.6,
            ErrorCategory.AUTH_AUTHORIZATION: 0.5,
            ErrorCategory.FRONTEND_UI: 0.7,
        }
        category_score = category_scores.get(error_analysis.category, 0.5)
        feasibility_score += category_score * 0.3
        factors.append(f"Category: {category_score:.2f}")
        
        # 基于错误类型
        type_scores = {
            ErrorType.CONFIG_ERROR: 0.9,
            ErrorType.DATA_ERROR: 0.8,
            ErrorType.ENVIRONMENT_ERROR: 0.7,
            ErrorType.CODE_ERROR: 0.4,
            ErrorType.INTERACTION_ERROR: 0.6,
        }
        type_score = type_scores.get(error_analysis.error_type, 0.5)
        feasibility_score += type_score * 0.3
        factors.append(f"Type: {type_score:.2f}")
        
        # 基于分析置信度
        confidence_score = error_analysis.confidence
        feasibility_score += confidence_score * 0.4
        factors.append(f"Confidence: {confidence_score:.2f}")
        
        # 归一化
        feasibility_score = min(feasibility_score, 1.0)
        
        return {
            "score": feasibility_score,
            "factors": factors,
            "feasible": feasibility_score >= 0.6
        }
    
    def _calculate_fix_risk(
        self,
        error_analysis: ErrorAnalysis
    ) -> Dict[str, Any]:
        """计算修复风险"""
        risk_score = 0.0
        risk_factors = []
        
        # 基于影响级别
        impact_scores = {
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }
        impact_score = impact_scores.get(error_analysis.impact_level, 0.5)
        risk_score += impact_score * 0.4
        risk_factors.append(f"Impact: {error_analysis.impact_level}")
        
        # 基于相关组件数量
        component_count = len(error_analysis.related_components)
        component_risk = min(component_count / 5.0, 1.0)
        risk_score += component_risk * 0.3
        risk_factors.append(f"Components: {component_count}")
        
        # 基于服务调用链长度
        call_chain_length = len(error_analysis.service_call_chain)
        chain_risk = min(call_chain_length / 3.0, 1.0)
        risk_score += chain_risk * 0.3
        risk_factors.append(f"Call chain: {call_chain_length}")
        
        # 归一化
        risk_score = min(risk_score, 1.0)
        
        # 确定风险级别
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "score": risk_score,
            "level": risk_level.value,
            "factors": risk_factors
        }
    
    def _assess_fix_impact(
        self,
        error_analysis: ErrorAnalysis
    ) -> Dict[str, Any]:
        """评估修复影响"""
        impact_score = 0.0
        impact_areas = []
        
        # 基于业务场景
        critical_scenarios = [
            "sales_analysis", "inventory_monitoring", "user_authentication"
        ]
        scenario_impact = 0.7 if error_analysis.business_scenario.value in critical_scenarios else 0.4
        impact_score += scenario_impact * 0.3
        impact_areas.append(f"Scenario: {error_analysis.business_scenario.value}")
        
        # 基于影响级别
        impact_levels = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        }
        level_impact = impact_levels.get(error_analysis.impact_level, 0.5)
        impact_score += level_impact * 0.4
        impact_areas.append(f"Level: {error_analysis.impact_level}")
        
        # 基于数据流
        data_flow_impact = min(len(error_analysis.data_flow) / 3.0, 1.0) * 0.3
        impact_score += data_flow_impact
        impact_areas.append(f"Data flow: {len(error_analysis.data_flow)}")
        
        # 归一化
        impact_score = min(impact_score, 1.0)
        
        # 确定影响级别
        if impact_score >= 0.8:
            impact_level = "high"
        elif impact_score >= 0.5:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        return {
            "score": impact_score,
            "level": impact_level,
            "areas": impact_areas
        }
    
    def _select_fix_strategy(
        self,
        error_analysis: ErrorAnalysis,
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """选择最优修复策略"""
        strategy_name = "auto_retry"
        
        # 基于错误类别选择策略
        if error_analysis.category == ErrorCategory.MCP_TOOL:
            strategy_name = "mcp_tool_fix"
        elif error_analysis.category == ErrorCategory.WORKFLOW_ENGINE:
            strategy_name = "workflow_fix"
        elif error_analysis.category == ErrorCategory.KNOWLEDGE_BASE:
            strategy_name = "knowledge_base_fix"
        elif error_analysis.category == ErrorCategory.FRONTEND_UI:
            strategy_name = "frontend_fix"
        
        # 基于风险级别调整策略
        if risk_assessment["level"] == "critical":
            strategy_name += "_with_rollback"
        
        return {
            "strategy_name": strategy_name,
            "max_retries": 3 if risk_assessment["level"] != "critical" else 1,
            "timeout": 60 if risk_assessment["level"] != "critical" else 30
        }
    
    async def _generate_fix_plan(
        self,
        error_analysis: ErrorAnalysis,
        strategy_config: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        impact_assessment: Dict[str, Any]
    ) -> FixPlan:
        """生成修复执行计划"""
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        
        # 生成修复步骤
        steps = []
        
        # 步骤1: 验证环境
        steps.append({
            "step": 1,
            "action": "validate_environment",
            "description": "验证相关服务环境状态",
            "estimated_time": 5.0
        })
        
        # 步骤2: 执行修复策略
        steps.append({
            "step": 2,
            "action": strategy_config["strategy_name"],
            "description": f"执行{strategy_config['strategy_name']}修复策略",
            "estimated_time": 30.0
        })
        
        # 步骤3: 验证修复结果
        steps.append({
            "step": 3,
            "action": "verify_fix",
            "description": "验证修复是否成功",
            "estimated_time": 10.0
        })
        
        # 计算总时间
        estimated_time = sum(step["estimated_time"] for step in steps)
        
        # 确定风险级别
        risk_level = RiskLevel(risk_assessment["level"])
        
        # 生成回滚计划
        rollback_plan = None
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            rollback_plan = {
                "steps": [
                    {"action": "restore_state", "description": "恢复原始状态"},
                    {"action": "notify_team", "description": "通知团队"}
                ]
            }
        
        return FixPlan(
            plan_id=plan_id,
            strategy=strategy_config["strategy_name"],
            steps=steps,
            estimated_time=estimated_time,
            risk_level=risk_level,
            impact_assessment=impact_assessment,
            rollback_plan=rollback_plan,
            prerequisites=["service_health_check"],
            dependencies=error_analysis.related_components
        )
    
    def _requires_approval(
        self,
        risk_assessment: Dict[str, Any],
        impact_assessment: Dict[str, Any]
    ) -> bool:
        """判断是否需要人工审批"""
        # 高风险或高影响需要审批
        if risk_assessment["level"] in ["high", "critical"]:
            return True
        
        if impact_assessment["level"] == "high":
            return True
        
        # 影响多个服务需要审批
        if risk_assessment.get("component_count", 0) > 3:
            return True
        
        return False
    
    # ==================== 人工决策接口 ====================
    
    async def _create_decision_point(
        self,
        task_id: str,
        decision: Dict[str, Any],
        fix_plan: Optional[FixPlan]
    ):
        """创建决策点"""
        decision_id = f"decision_{uuid.uuid4().hex[:12]}"
        
        # 生成选项
        options = [
            {
                "id": "approve_auto_fix",
                "label": "批准自动修复",
                "description": "批准系统自动执行修复计划",
                "risk": "low"
            },
            {
                "id": "manual_review",
                "label": "人工审查",
                "description": "需要人工审查后再决定",
                "risk": "medium"
            },
            {
                "id": "reject",
                "label": "拒绝修复",
                "description": "拒绝执行修复，保持现状",
                "risk": "low"
            }
        ]
        
        # 推荐选项
        recommendation = "approve_auto_fix"
        if decision["risk_level"] == "critical":
            recommendation = "manual_review"
        
        decision_point = DecisionPoint(
            decision_id=decision_id,
            task_id=task_id,
            decision_type=DecisionType.MANUAL_REVIEW,
            title=f"修复审批: {decision.get('strategy', 'Unknown')}",
            description=f"风险级别: {decision['risk_level']}, 影响级别: {decision['impact_level']}",
            options=options,
            recommendation=recommendation,
            risk_assessment=decision,
            impact_analysis=decision
        )
        
        self.decision_points[decision_id] = decision_point
        
        # 更新任务
        task = self.tasks.get(task_id)
        if task:
            task.metadata["decision_point_id"] = decision_id
        
        return decision_id
    
    async def resolve_decision(
        self,
        decision_id: str,
        decision: str,
        decision_maker: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        解决决策点
        
        Args:
            decision_id: 决策点ID
            decision: 决策选项ID
            decision_maker: 决策者
            reason: 决策原因
        
        Returns:
            是否成功
        """
        decision_point = self.decision_points.get(decision_id)
        if not decision_point:
            logger.error(f"Decision point not found: {decision_id}")
            return False
        
        if decision_point.resolved_at:
            logger.warning(f"Decision point already resolved: {decision_id}")
            return False
        
        # 更新决策点
        decision_point.resolved_at = datetime.now()
        decision_point.decision = decision
        decision_point.decision_reason = reason
        decision_point.decision_maker = decision_maker
        
        # 记录决策历史
        self.decision_history.append({
            "decision_id": decision_id,
            "task_id": decision_point.task_id,
            "decision": decision,
            "decision_maker": decision_maker,
            "reason": reason,
            "timestamp": decision_point.resolved_at.isoformat()
        })
        
        # 更新任务
        task = self.tasks.get(decision_point.task_id)
        if task:
            task.approval_status = decision
            task.approver = decision_maker
            task.metadata["approval_reason"] = reason
            
            # 如果批准，继续执行修复
            if decision == "approve_auto_fix":
                task.status = DebugTaskStatus.FIXING
                asyncio.create_task(self._execute_fix_after_approval(task))
            elif decision == "reject":
                task.status = DebugTaskStatus.CANCELLED
        
        logger.info(
            f"Decision resolved: {decision_id}, decision: {decision}, "
            f"maker: {decision_maker}"
        )
        
        return True
    
    async def _execute_fix_after_approval(self, task: DebugTask):
        """批准后执行修复"""
        if not task.error_analysis or not task.execution_plan:
            logger.error(f"Cannot execute fix: missing analysis or plan")
            return
        
        try:
            fix_result = await self._execute_fix(
                task.error_analysis,
                FixPlan(**task.execution_plan),
                task
            )
            task.fix_result = fix_result
            
            if fix_result.success:
                task.status = DebugTaskStatus.COMPLETED
            else:
                task.status = DebugTaskStatus.FAILED
            
            task.updated_at = datetime.now()
        
        except Exception as e:
            logger.error(f"Error executing fix after approval: {str(e)}", exc_info=True)
            task.status = DebugTaskStatus.FAILED
            task.metadata["error"] = str(e)
    
    def get_pending_decisions(self) -> List[Dict[str, Any]]:
        """获取待处理的决策点"""
        pending = [
            dp for dp in self.decision_points.values()
            if dp.resolved_at is None
        ]
        
        return [asdict(dp) for dp in pending]
    
    def get_decision_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history[-limit:]
    
    # ==================== 修复执行 ====================
    
    async def _execute_fix(
        self,
        error_analysis: ErrorAnalysis,
        fix_plan: FixPlan,
        task: DebugTask
    ) -> FixResult:
        """执行修复"""
        try:
            # 创建修复策略配置
            config = FixStrategyConfig(
                max_retries=3,
                retry_delay=1.0,
                timeout=fix_plan.estimated_time
            )
            
            # 准备上下文
            context = {
                **task.error_report.get("context", {}),
                **{k: v for k, v in self.service_urls.items()}
            }
            
            # 执行修复
            fix_result = await apply_fix(
                error_analysis=error_analysis,
                context=context,
                config=config
            )
            
            return fix_result
        
        except Exception as e:
            logger.error(f"Error executing fix: {str(e)}", exc_info=True)
            return FixResult(
                success=False,
                strategy_used="unknown",
                message=f"Fix execution failed: {str(e)}",
                error=str(e)
            )
    
    # ==================== 平台集成接口 ====================
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """获取服务健康状态"""
        try:
            from shared_libs.common.http_client import HTTPClient
            service_url = self.service_urls.get(service_name)
            
            if not service_url:
                return {"status": "unknown", "error": "Service not configured"}
            
            async with HTTPClient(service_url) as client:
                health_data = await client.get("/api/health")
                monitoring_data = await client.get("/api/monitoring")
                
                return {
                    "service_name": service_name,
                    "health": health_data,
                    "monitoring": monitoring_data,
                    "status": health_data.get("status", "unknown")
                }
        
        except Exception as e:
            logger.error(f"Error getting service health: {str(e)}")
            return {
                "service_name": service_name,
                "status": "error",
                "error": str(e)
            }
    
    async def get_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务健康状态"""
        services = {}
        
        for service_name in self.service_urls.keys():
            services[service_name] = await self.get_service_health(service_name)
        
        return services
    
    async def get_service_logs(
        self,
        service_name: str,
        limit: int = 100,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取服务日志"""
        try:
            from shared_libs.common.http_client import HTTPClient
            service_url = self.service_urls.get(service_name)
            
            if not service_url:
                return []
            
            async with HTTPClient(service_url) as client:
                params = {"limit": limit}
                if level:
                    params["level"] = level
                
                logs = await client.get("/api/logs", params=params)
                return logs if isinstance(logs, list) else []
        
        except Exception as e:
            logger.error(f"Error getting service logs: {str(e)}")
            return []
    
    async def get_service_metrics(
        self,
        service_name: str,
        metric_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取服务指标"""
        try:
            from shared_libs.common.http_client import HTTPClient
            service_url = self.service_urls.get(service_name)
            
            if not service_url:
                return {}
            
            async with HTTPClient(service_url) as client:
                if metric_name:
                    metrics = await client.get(f"/api/metrics/{metric_name}")
                else:
                    metrics = await client.get("/api/metrics")
                
                return metrics if isinstance(metrics, dict) else {}
        
        except Exception as e:
            logger.error(f"Error getting service metrics: {str(e)}")
            return {}
    
    async def update_service_config(
        self,
        service_name: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """更新服务配置"""
        try:
            from shared_libs.common.http_client import HTTPClient
            service_url = self.service_urls.get(service_name)
            
            if not service_url:
                return False
            
            async with HTTPClient(service_url) as client:
                response = await client.post(
                    "/api/config/update",
                    data={"config": config_updates}
                )
                
                return response.get("success", False)
        
        except Exception as e:
            logger.error(f"Error updating service config: {str(e)}")
            return False


# 全局协调器实例
_orchestrator_instance: Optional[DebugOrchestrator] = None


def get_debug_orchestrator(
    config: Optional[Dict[str, Any]] = None
) -> DebugOrchestrator:
    """获取调试协调器实例（单例模式）"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DebugOrchestrator(config)
    return _orchestrator_instance


# 便捷函数
async def submit_error_for_debugging(
    error_report: Dict[str, Any],
    priority: str = "normal"
) -> str:
    """
    提交错误报告进行调试的便捷函数
    
    Args:
        error_report: 错误报告
        priority: 优先级
    
    Returns:
        任务ID
    """
    orchestrator = get_debug_orchestrator()
    return await orchestrator.submit_error_report(error_report, priority)

