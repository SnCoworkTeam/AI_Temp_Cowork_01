"""
企业级AIOS内核模块 (os-core)
提供统一资源抽象层，作为AIOS的基础设施
"""

from .resource_model import (
    ResourceType,
    Resource,
    BusinessResource,
    SystemEndpointResource,
    KnowledgeItemResource,
    WorkflowResource,
    DataEntityResource
)
from .resource_registry import ResourceRegistry
from .resource_resolver import ResourceResolver, IntentResolutionResult
from .resource_operations import ResourceOperation, ResourceOperationType
from .resource_metadata import ResourceMetadataManager

# 适配器
from .adapters import (
    BusinessObjectAdapter,
    SystemEndpointAdapter,
    KnowledgeAdapter,
    WorkflowAdapter
)

# 策略与治理模块
try:
    from .policy_engine import (
        PolicyEngine, PolicyLanguage, PolicyRule, PolicyAction,
        PolicyContext, PolicyEvaluationResult
    )
    from .audit_logger import (
        AuditLogger, AuditEvent, AuditEventType, AuditEventSeverity
    )
    from .governance_dashboard import (
        GovernanceDashboard, DashboardRole, GovernanceMetric, DashboardView
    )
except ImportError:
    # 如果导入失败，可能是路径问题，继续执行
    PolicyEngine = None
    AuditLogger = None
    GovernanceDashboard = None

# 自演进模块（里程碑4）
try:
    from .behavior_collector import (
        BehaviorCollector, IntentCallData, WorkflowExecutionData,
        ResourceUsageData, BehaviorEventType
    )
    from .optimization_engine import (
        OptimizationEngine, OptimizationRecommendation, OptimizationType,
        AutomationScenario
    )
    from .evolution_manager import (
        EvolutionManager, EvolutionVersion, EvolutionStatus, ABTestResult
    )
    from .scenario_recommender import (
        ScenarioRecommender, ScenarioRecommendation
    )
except ImportError:
    # 如果导入失败，可能是路径问题，继续执行
    BehaviorCollector = None
    OptimizationEngine = None
    EvolutionManager = None
    ScenarioRecommender = None

__all__ = [
    # 资源模型
    "ResourceType",
    "Resource",
    "BusinessResource",
    "SystemEndpointResource",
    "KnowledgeItemResource",
    "WorkflowResource",
    "DataEntityResource",
    # 核心服务
    "ResourceRegistry",
    "ResourceResolver",
    "IntentResolutionResult",
    "ResourceMetadataManager",
    # 操作
    "ResourceOperation",
    "ResourceOperationType",
    # 适配器
    "BusinessObjectAdapter",
    "SystemEndpointAdapter",
    "KnowledgeAdapter",
    "WorkflowAdapter",
    # 策略与治理
    "PolicyEngine",
    "PolicyLanguage",
    "PolicyRule",
    "PolicyAction",
    "PolicyContext",
    "PolicyEvaluationResult",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "GovernanceDashboard",
    "DashboardRole",
    "GovernanceMetric",
    "DashboardView",
    # 自演进（里程碑4）
    "BehaviorCollector",
    "IntentCallData",
    "WorkflowExecutionData",
    "ResourceUsageData",
    "BehaviorEventType",
    "OptimizationEngine",
    "OptimizationRecommendation",
    "OptimizationType",
    "AutomationScenario",
    "EvolutionManager",
    "EvolutionVersion",
    "EvolutionStatus",
    "ABTestResult",
    "ScenarioRecommender",
    "ScenarioRecommendation",
]

# 监控模块（技术债务优化）
try:
    from .monitoring import (
        MetricsCollector, PerformanceMonitor, Metric, PerformanceMetric,
        get_metrics_collector, monitor_performance
    )
    __all__.extend([
        "MetricsCollector",
        "PerformanceMonitor",
        "Metric",
        "PerformanceMetric",
        "get_metrics_collector",
        "monitor_performance"
    ])
except ImportError:
    pass

__version__ = "1.0.0"
