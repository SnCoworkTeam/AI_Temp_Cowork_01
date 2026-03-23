"""
自动调试模块
提供平台错误分析和调试功能
"""
from .platform_error_analyzer import (
    PlatformErrorAnalyzer,
    ErrorCategory,
    ErrorType,
    BusinessScenario,
    ErrorAnalysis,
    get_error_analyzer,
    analyze_error
)
from .platform_fix_strategies import (
    PlatformFixStrategyManager,
    FixStrategyConfig,
    FixResult,
    FixStrategyType,
    BaseFixStrategy,
    MCPToolFixStrategy,
    WorkflowEngineFixStrategy,
    KnowledgeBaseFixStrategy,
    FrontendUIFixStrategy,
    get_fix_strategy_manager,
    apply_fix
)
from .debug_orchestrator import (
    DebugOrchestrator,
    DebugTask,
    DebugTaskStatus,
    DecisionType,
    RiskLevel,
    FixPlan,
    DecisionPoint,
    get_debug_orchestrator,
    submit_error_for_debugging
)
from .platform_test_validator import (
    PlatformTestValidator,
    TestResult,
    TestSuiteResult,
    TestStatus,
    TestType,
    get_test_validator
)
from .platform_deployment import (
    PlatformDeploymentManager,
    DeploymentPlan,
    DeploymentStatus,
    ServicePriority,
    ServiceDeployment,
    DeploymentConfig,
    RollbackTrigger,
    get_deployment_manager
)
from .platform_monitor import (
    PlatformMonitor,
    Alert,
    AlertSeverity,
    AlertCategory,
    PerformanceBaseline,
    UserExperienceMetric,
    MetricType,
    get_platform_monitor
)

__all__ = [
    # 错误分析
    "PlatformErrorAnalyzer",
    "ErrorCategory",
    "ErrorType",
    "BusinessScenario",
    "ErrorAnalysis",
    "get_error_analyzer",
    "analyze_error",
    # 修复策略
    "PlatformFixStrategyManager",
    "FixStrategyConfig",
    "FixResult",
    "FixStrategyType",
    "BaseFixStrategy",
    "MCPToolFixStrategy",
    "WorkflowEngineFixStrategy",
    "KnowledgeBaseFixStrategy",
    "FrontendUIFixStrategy",
    "get_fix_strategy_manager",
    "apply_fix",
    # 调试协调器
    "DebugOrchestrator",
    "DebugTask",
    "DebugTaskStatus",
    "DecisionType",
    "RiskLevel",
    "FixPlan",
    "DecisionPoint",
    "get_debug_orchestrator",
    "submit_error_for_debugging",
    # 测试验证器
    "PlatformTestValidator",
    "TestResult",
    "TestSuiteResult",
    "TestStatus",
    "TestType",
    "get_test_validator",
    # 部署管理器
    "PlatformDeploymentManager",
    "DeploymentPlan",
    "DeploymentStatus",
    "ServicePriority",
    "ServiceDeployment",
    "DeploymentConfig",
    "RollbackTrigger",
    "get_deployment_manager",
    # 平台监控器
    "PlatformMonitor",
    "Alert",
    "AlertSeverity",
    "AlertCategory",
    "PerformanceBaseline",
    "UserExperienceMetric",
    "MetricType",
    "get_platform_monitor",
]

