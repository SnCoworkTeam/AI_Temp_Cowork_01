"""
智能体模块
"""

# 延迟导入，避免启动时错误
try:
    from .mcp_tool_agent import MCPToolAgent
except ImportError:
    MCPToolAgent = None

try:
    from .workflow_agent import WorkflowAgent
except ImportError:
    WorkflowAgent = None

try:
    from .metadata_agent import MetadataAgent
except ImportError:
    MetadataAgent = None

try:
    from .knowledge_base_agent import KnowledgeBaseAgent
except ImportError:
    KnowledgeBaseAgent = None

try:
    from .data_query_agent import DataQueryAgent
except ImportError:
    DataQueryAgent = None

try:
    from .data_clean_agent import DataCleanAgent
except ImportError:
    DataCleanAgent = None

try:
    from .data_validation_agent import DataValidationAgent
except ImportError:
    DataValidationAgent = None

try:
    from .data_enrich_agent import DataEnrichAgent
except ImportError:
    DataEnrichAgent = None

try:
    from .analysis_agent import AnalysisAgent
except ImportError:
    AnalysisAgent = None

try:
    from .insight_agent import InsightAgent
except ImportError:
    InsightAgent = None

try:
    from .quality_check_agent import QualityCheckAgent
except ImportError:
    QualityCheckAgent = None

try:
    from .content_agent import ContentAgent
except ImportError:
    ContentAgent = None

try:
    from .format_agent import FormatAgent
except ImportError:
    FormatAgent = None

try:
    from .result_synthesis_agent import ResultSynthesisAgent
except ImportError:
    ResultSynthesisAgent = None

try:
    from .sap_odata_agent import SAPODataAgent
except ImportError:
    SAPODataAgent = None

from .server_operation_agent import ServerOperationAgent

# 从统一基类导入
from .unified_base_agent import (
    BaseAgent,
    ExecutionPlan,
    ExecutionResult,
    Reflection,
    AgentState
)

__all__ = [
    'MCPToolAgent',
    'WorkflowAgent',
    'MetadataAgent',
    'KnowledgeBaseAgent',
    'DataQueryAgent',
    'DataCleanAgent',
    'DataValidationAgent',
    'DataEnrichAgent',
    'AnalysisAgent',
    'InsightAgent',
    'QualityCheckAgent',
    'ContentAgent',
    'FormatAgent',
    'ResultSynthesisAgent',
    'SAPODataAgent',
    'ServerOperationAgent',
    'BaseAgent',
    'ExecutionPlan',
    'ExecutionResult',
    'Reflection',
    'AgentState',
    'ReActEngine',
    'ToolRegistry',
    'Tool',
    'get_tool_registry',
    'AgentAdapter'
]
