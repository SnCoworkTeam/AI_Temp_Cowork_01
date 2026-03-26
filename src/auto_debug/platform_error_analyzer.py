"""
专门分析企业AI平台特有错误的智能分析器

功能：
1. 平台特有错误模式识别
2. 上下文感知分析
3. 智能根因定位
"""
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime
import re
import logging
import json
import traceback
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误类别"""
    MCP_TOOL = "mcp_tool"
    WORKFLOW_ENGINE = "workflow_engine"
    AUTH_AUTHORIZATION = "auth_authorization"
    KNOWLEDGE_BASE = "knowledge_base"
    FRONTEND_UI = "frontend_ui"
    UNKNOWN = "unknown"


class ErrorType(Enum):
    """错误类型"""
    CODE_ERROR = "code_error"
    CONFIG_ERROR = "config_error"
    DATA_ERROR = "data_error"
    ENVIRONMENT_ERROR = "environment_error"
    INTERACTION_ERROR = "interaction_error"


class BusinessScenario(Enum):
    """业务场景"""
    SALES_ANALYSIS = "sales_analysis"
    INVENTORY_MONITORING = "inventory_monitoring"
    DOCUMENT_PROCESSING = "document_processing"
    DATA_QUERY = "data_query"
    WORKFLOW_EXECUTION = "workflow_execution"
    USER_AUTHENTICATION = "user_authentication"
    UNKNOWN = "unknown"


@dataclass
class ErrorPattern:
    """错误模式"""
    pattern: str
    category: ErrorCategory
    error_type: ErrorType
    description: str
    keywords: List[str]
    severity: str = "medium"


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    error_type: ErrorType
    business_scenario: BusinessScenario
    root_cause: str
    error_message: str
    context: Dict[str, Any]
    related_components: List[str]
    data_flow: List[str]
    service_call_chain: List[str]
    impact_level: str
    recommendations: List[str]
    confidence: float


class PlatformErrorAnalyzer:
    """企业AI平台错误分析器"""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.business_scenario_patterns = self._initialize_business_scenario_patterns()
        self.service_components = {
            "mcp-gateway": ["tool_registry", "tool_service", "tool_execution"],
            "workflow-engine": ["workflow_manager", "node_execution", "state_management"],
            "auth-service": ["jwt_manager", "sso_client", "auth_middleware"],
            "knowledge-base": ["document_service", "vector_store", "embedding_manager"],
            "web-ui": ["api_client", "state_sync", "component_render"]
        }
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """初始化错误模式"""
        patterns = [
            # MCP工具执行错误
            ErrorPattern(
                pattern=r"Tool execution (failed|timed out|error)",
                category=ErrorCategory.MCP_TOOL,
                error_type=ErrorType.CODE_ERROR,
                description="MCP工具执行失败",
                keywords=["tool", "execution", "failed", "timeout", "mcp"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"(Tool|tool) '(.*?)' (not found|not registered)",
                category=ErrorCategory.MCP_TOOL,
                error_type=ErrorType.CONFIG_ERROR,
                description="MCP工具未找到或未注册",
                keywords=["tool", "not found", "not registered"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"(Invalid|invalid) (parameters|parameter)",
                category=ErrorCategory.MCP_TOOL,
                error_type=ErrorType.DATA_ERROR,
                description="MCP工具参数错误",
                keywords=["invalid", "parameter", "parameters"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"Connection (timeout|failed|refused)",
                category=ErrorCategory.MCP_TOOL,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="MCP工具连接超时或失败",
                keywords=["connection", "timeout", "failed", "refused"],
                severity="high"
            ),
            
            # 工作流引擎错误
            ErrorPattern(
                pattern=r"Node '(.*?)' execution (failed|error)",
                category=ErrorCategory.WORKFLOW_ENGINE,
                error_type=ErrorType.CODE_ERROR,
                description="工作流节点执行失败",
                keywords=["node", "execution", "failed"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"(State|state) (inconsistent|validation failed)",
                category=ErrorCategory.WORKFLOW_ENGINE,
                error_type=ErrorType.INTERACTION_ERROR,
                description="工作流状态不一致",
                keywords=["state", "inconsistent", "validation"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"(Circular|circular) (dependency|reference)",
                category=ErrorCategory.WORKFLOW_ENGINE,
                error_type=ErrorType.CONFIG_ERROR,
                description="工作流循环依赖",
                keywords=["circular", "dependency", "reference"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"Workflow execution (timeout|timed out)",
                category=ErrorCategory.WORKFLOW_ENGINE,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="工作流执行超时",
                keywords=["workflow", "execution", "timeout"],
                severity="high"
            ),
            
            # 认证授权错误
            ErrorPattern(
                pattern=r"(Token|token) (expired|invalid|not found)",
                category=ErrorCategory.AUTH_AUTHORIZATION,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="Token失效或无效",
                keywords=["token", "expired", "invalid"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"(Permission|permission) (denied|insufficient)",
                category=ErrorCategory.AUTH_AUTHORIZATION,
                error_type=ErrorType.CONFIG_ERROR,
                description="权限不足",
                keywords=["permission", "denied", "insufficient"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"SSO (integration|authentication) (failed|error)",
                category=ErrorCategory.AUTH_AUTHORIZATION,
                error_type=ErrorType.INTERACTION_ERROR,
                description="SSO集成问题",
                keywords=["sso", "integration", "authentication"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"(Not authenticated|Unauthorized)",
                category=ErrorCategory.AUTH_AUTHORIZATION,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="未认证或未授权",
                keywords=["not authenticated", "unauthorized"],
                severity="high"
            ),
            
            # 知识库错误
            ErrorPattern(
                pattern=r"Vector (index|store) (failed|error)",
                category=ErrorCategory.KNOWLEDGE_BASE,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="向量索引失败",
                keywords=["vector", "index", "store", "failed"],
                severity="high"
            ),
            ErrorPattern(
                pattern=r"Document (parsing|parse) (failed|error)",
                category=ErrorCategory.KNOWLEDGE_BASE,
                error_type=ErrorType.DATA_ERROR,
                description="文档解析错误",
                keywords=["document", "parsing", "parse", "failed"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"Search (timeout|failed|error)",
                category=ErrorCategory.KNOWLEDGE_BASE,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="搜索超时或失败",
                keywords=["search", "timeout", "failed"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"Embedding (generation|generated) (failed|error)",
                category=ErrorCategory.KNOWLEDGE_BASE,
                error_type=ErrorType.ENVIRONMENT_ERROR,
                description="嵌入向量生成失败",
                keywords=["embedding", "generation", "failed"],
                severity="high"
            ),
            
            # 前端界面错误
            ErrorPattern(
                pattern=r"API (call|request) (failed|error|timeout)",
                category=ErrorCategory.FRONTEND_UI,
                error_type=ErrorType.INTERACTION_ERROR,
                description="API调用失败",
                keywords=["api", "call", "request", "failed"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"(State|state) (synchronization|sync) (failed|error)",
                category=ErrorCategory.FRONTEND_UI,
                error_type=ErrorType.INTERACTION_ERROR,
                description="状态同步问题",
                keywords=["state", "synchronization", "sync", "failed"],
                severity="medium"
            ),
            ErrorPattern(
                pattern=r"Component (render|rendering) (failed|error)",
                category=ErrorCategory.FRONTEND_UI,
                error_type=ErrorType.CODE_ERROR,
                description="组件渲染错误",
                keywords=["component", "render", "rendering", "failed"],
                severity="low"
            ),
        ]
        return patterns
    
    def _initialize_business_scenario_patterns(self) -> Dict[BusinessScenario, List[str]]:
        """初始化业务场景模式"""
        return {
            BusinessScenario.SALES_ANALYSIS: [
                "sales", "revenue", "订单", "销售", "客户", "订单分析"
            ],
            BusinessScenario.INVENTORY_MONITORING: [
                "inventory", "stock", "库存", "物料", "库存监控"
            ],
            BusinessScenario.DOCUMENT_PROCESSING: [
                "document", "upload", "parse", "文档", "上传", "解析"
            ],
            BusinessScenario.DATA_QUERY: [
                "query", "sap_query", "data", "查询", "数据查询"
            ],
            BusinessScenario.WORKFLOW_EXECUTION: [
                "workflow", "execution", "工作流", "执行"
            ],
            BusinessScenario.USER_AUTHENTICATION: [
                "login", "auth", "sso", "token", "登录", "认证"
            ],
        }
    
    def analyze_error(
        self,
        error_message: str,
        error_traceback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorAnalysis:
        """
        分析错误
        
        Args:
            error_message: 错误消息
            error_traceback: 错误堆栈跟踪
            context: 错误上下文信息
            metadata: 元数据（如请求信息、用户信息等）
        
        Returns:
            错误分析结果
        """
        context = context or {}
        metadata = metadata or {}
        
        # 识别错误类别和类型
        category, error_type, pattern = self._identify_error_category(error_message, error_traceback)
        
        # 识别业务场景
        business_scenario = self._identify_business_scenario(error_message, context, metadata)
        
        # 分析根因
        root_cause = self._analyze_root_cause(
            error_message, error_traceback, category, error_type, context
        )
        
        # 提取相关组件
        related_components = self._extract_related_components(error_message, error_traceback, context)
        
        # 分析数据流
        data_flow = self._analyze_data_flow(context, metadata)
        
        # 分析服务调用链
        service_call_chain = self._analyze_service_call_chain(error_traceback, context, metadata)
        
        # 评估影响程度
        impact_level = self._assess_impact_level(category, error_type, related_components)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            category, error_type, root_cause, related_components
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(
            pattern, error_traceback, context, related_components
        )
        
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(error_message) % 10000}"
        
        return ErrorAnalysis(
            error_id=error_id,
            timestamp=datetime.now(),
            category=category,
            error_type=error_type,
            business_scenario=business_scenario,
            root_cause=root_cause,
            error_message=error_message,
            context=context,
            related_components=related_components,
            data_flow=data_flow,
            service_call_chain=service_call_chain,
            impact_level=impact_level,
            recommendations=recommendations,
            confidence=confidence
        )
    
    def _identify_error_category(
        self,
        error_message: str,
        error_traceback: Optional[str]
    ) -> Tuple[ErrorCategory, ErrorType, Optional[ErrorPattern]]:
        """识别错误类别和类型"""
        error_text = f"{error_message} {error_traceback or ''}".lower()
        
        matched_pattern = None
        best_match_score = 0
        
        for pattern in self.error_patterns:
            if re.search(pattern.pattern, error_text, re.IGNORECASE):
                # 计算匹配分数（基于关键词匹配）
                score = sum(1 for keyword in pattern.keywords if keyword.lower() in error_text)
                if score > best_match_score:
                    best_match_score = score
                    matched_pattern = pattern
        
        if matched_pattern:
            return matched_pattern.category, matched_pattern.error_type, matched_pattern
        
        # 如果没有匹配的模式，尝试基于堆栈跟踪推断
        if error_traceback:
            if "mcp" in error_traceback.lower() or "tool" in error_traceback.lower():
                return ErrorCategory.MCP_TOOL, ErrorType.CODE_ERROR, None
            elif "workflow" in error_traceback.lower() or "node" in error_traceback.lower():
                return ErrorCategory.WORKFLOW_ENGINE, ErrorType.CODE_ERROR, None
            elif "auth" in error_traceback.lower() or "token" in error_traceback.lower():
                return ErrorCategory.AUTH_AUTHORIZATION, ErrorType.ENVIRONMENT_ERROR, None
            elif "vector" in error_traceback.lower() or "document" in error_traceback.lower():
                return ErrorCategory.KNOWLEDGE_BASE, ErrorType.ENVIRONMENT_ERROR, None
        
        return ErrorCategory.UNKNOWN, ErrorType.CODE_ERROR, None
    
    def _identify_business_scenario(
        self,
        error_message: str,
        context: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> BusinessScenario:
        """识别业务场景"""
        error_text = error_message.lower()
        context_text = json.dumps(context, default=str).lower()
        metadata_text = json.dumps(metadata, default=str).lower()
        combined_text = f"{error_text} {context_text} {metadata_text}"
        
        best_match = BusinessScenario.UNKNOWN
        best_score = 0
        
        for scenario, keywords in self.business_scenario_patterns.items():
            score = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if score > best_score:
                best_score = score
                best_match = scenario
        
        return best_match
    
    def _analyze_root_cause(
        self,
        error_message: str,
        error_traceback: Optional[str],
        category: ErrorCategory,
        error_type: ErrorType,
        context: Dict[str, Any]
    ) -> str:
        """分析根因"""
        root_causes = []
        
        # 基于错误类型推断根因
        if error_type == ErrorType.CODE_ERROR:
            if error_traceback:
                # 从堆栈跟踪中提取关键信息
                if "File" in error_traceback and "line" in error_traceback.lower():
                    root_causes.append("代码逻辑错误，需要检查相关代码文件")
                else:
                    root_causes.append("代码执行错误，可能是逻辑问题或异常处理不当")
            else:
                root_causes.append("代码执行错误")
        
        elif error_type == ErrorType.CONFIG_ERROR:
            root_causes.append("配置错误，检查相关配置文件或参数设置")
            if "tool" in error_message.lower():
                root_causes.append("工具配置可能不正确或工具未正确注册")
            elif "workflow" in error_message.lower():
                root_causes.append("工作流配置可能存在问题")
        
        elif error_type == ErrorType.DATA_ERROR:
            root_causes.append("数据错误，检查输入数据的格式和内容")
            if "parameter" in error_message.lower():
                root_causes.append("参数验证失败，可能缺少必需参数或参数格式不正确")
        
        elif error_type == ErrorType.ENVIRONMENT_ERROR:
            root_causes.append("环境错误，检查服务连接、网络状态或资源可用性")
            if "timeout" in error_message.lower():
                root_causes.append("超时错误，可能是服务响应慢或网络问题")
            elif "connection" in error_message.lower():
                root_causes.append("连接错误，检查服务是否正常运行")
        
        elif error_type == ErrorType.INTERACTION_ERROR:
            root_causes.append("组件交互错误，检查服务间的调用和通信")
            if "sso" in error_message.lower():
                root_causes.append("SSO集成问题，检查SSO配置和连接")
            elif "api" in error_message.lower():
                root_causes.append("API调用失败，检查服务可用性和接口定义")
        
        # 基于类别细化根因
        if category == ErrorCategory.MCP_TOOL:
            if "timeout" in error_message.lower():
                root_causes.append("MCP工具执行超时，可能需要增加超时时间或优化工具性能")
            elif "not found" in error_message.lower():
                root_causes.append("MCP工具未找到，检查工具注册状态")
        
        elif category == ErrorCategory.WORKFLOW_ENGINE:
            if "circular" in error_message.lower():
                root_causes.append("工作流存在循环依赖，需要检查节点连接关系")
            elif "state" in error_message.lower():
                root_causes.append("工作流状态不一致，检查状态转换逻辑")
        
        elif category == ErrorCategory.KNOWLEDGE_BASE:
            if "vector" in error_message.lower():
                root_causes.append("向量索引问题，检查向量数据库连接和索引状态")
            elif "document" in error_message.lower():
                root_causes.append("文档处理问题，检查文档格式和解析器配置")
        
        return " | ".join(root_causes) if root_causes else "未知根因，需要进一步分析"
    
    def _extract_related_components(
        self,
        error_message: str,
        error_traceback: Optional[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """提取相关组件"""
        components = set()
        
        # 从错误消息中提取
        error_text = f"{error_message} {error_traceback or ''}".lower()
        
        # 检查服务组件
        for service, component_list in self.service_components.items():
            for component in component_list:
                if component in error_text:
                    components.add(f"{service}:{component}")
        
        # 从上下文中提取
        if "service" in context:
            components.add(context["service"])
        if "component" in context:
            components.add(context["component"])
        if "tool_name" in context:
            components.add(f"mcp-gateway:tool:{context['tool_name']}")
        if "workflow_id" in context:
            components.add(f"workflow-engine:workflow:{context['workflow_id']}")
        if "node_name" in context:
            components.add(f"workflow-engine:node:{context['node_name']}")
        
        return sorted(list(components))
    
    def _analyze_data_flow(
        self,
        context: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """分析数据流"""
        data_flow = []
        
        # 从上下文和元数据中提取数据流信息
        if "input_data" in context:
            data_flow.append("用户输入数据")
        if "sap_data" in context or "sap_query" in str(context).lower():
            data_flow.append("SAP系统数据")
        if "document_data" in context or "document" in str(context).lower():
            data_flow.append("文档数据")
        if "workflow_state" in context:
            data_flow.append("工作流状态数据")
        if "tool_result" in context:
            data_flow.append("工具执行结果")
        if "api_response" in context:
            data_flow.append("API响应数据")
        
        # 从元数据中提取
        if "request_path" in metadata:
            data_flow.append(f"API请求: {metadata['request_path']}")
        if "user_id" in metadata:
            data_flow.append(f"用户数据: {metadata['user_id']}")
        
        return data_flow if data_flow else ["未知数据流"]
    
    def _analyze_service_call_chain(
        self,
        error_traceback: Optional[str],
        context: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """分析服务调用链"""
        call_chain = []
        
        # 从堆栈跟踪中提取调用链
        if error_traceback:
            lines = error_traceback.split('\n')
            for line in lines:
                if 'File "' in line and '/src/' in line:
                    # 提取服务名称
                    if '/mcp-gateway/' in line:
                        call_chain.append("mcp-gateway")
                    elif '/workflow-engine/' in line:
                        call_chain.append("workflow-engine")
                    elif '/auth-service/' in line:
                        call_chain.append("auth-service")
                    elif '/knowledge-base/' in line:
                        call_chain.append("knowledge-base")
                    elif '/web-ui/' in line:
                        call_chain.append("web-ui")
        
        # 从上下文中提取
        if "service_call_chain" in context:
            call_chain.extend(context["service_call_chain"])
        
        # 从元数据中提取
        if "referer" in metadata:
            if "web-ui" in metadata["referer"]:
                call_chain.insert(0, "web-ui")
        
        # 去重并保持顺序
        seen = set()
        unique_chain = []
        for service in call_chain:
            if service not in seen:
                seen.add(service)
                unique_chain.append(service)
        
        return unique_chain if unique_chain else ["未知调用链"]
    
    def _assess_impact_level(
        self,
        category: ErrorCategory,
        error_type: ErrorType,
        related_components: List[str]
    ) -> str:
        """评估影响程度"""
        # 基于错误类别
        if category in [ErrorCategory.AUTH_AUTHORIZATION, ErrorCategory.MCP_TOOL]:
            base_impact = "high"
        elif category in [ErrorCategory.WORKFLOW_ENGINE, ErrorCategory.KNOWLEDGE_BASE]:
            base_impact = "medium"
        else:
            base_impact = "low"
        
        # 基于错误类型
        if error_type == ErrorType.ENVIRONMENT_ERROR:
            impact = "high"
        elif error_type == ErrorType.CODE_ERROR:
            impact = "medium"
        else:
            impact = base_impact
        
        # 基于相关组件数量
        if len(related_components) > 3:
            if impact == "low":
                impact = "medium"
            elif impact == "medium":
                impact = "high"
        
        return impact
    
    def _generate_recommendations(
        self,
        category: ErrorCategory,
        error_type: ErrorType,
        root_cause: str,
        related_components: List[str]
    ) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 基于错误类别
        if category == ErrorCategory.MCP_TOOL:
            recommendations.append("检查MCP工具注册状态和配置")
            recommendations.append("验证工具参数格式和必需参数")
            recommendations.append("检查工具执行超时设置")
            if "connection" in root_cause.lower():
                recommendations.append("检查MCP Gateway服务连接状态")
        
        elif category == ErrorCategory.WORKFLOW_ENGINE:
            recommendations.append("检查工作流配置和节点定义")
            recommendations.append("验证工作流状态转换逻辑")
            if "circular" in root_cause.lower():
                recommendations.append("检查工作流图是否存在循环依赖")
            recommendations.append("检查节点执行顺序和依赖关系")
        
        elif category == ErrorCategory.AUTH_AUTHORIZATION:
            recommendations.append("检查Token有效性和过期时间")
            recommendations.append("验证用户权限配置")
            if "sso" in root_cause.lower():
                recommendations.append("检查SSO配置和连接状态")
                recommendations.append("验证SSO提供者响应")
            recommendations.append("检查认证中间件配置")
        
        elif category == ErrorCategory.KNOWLEDGE_BASE:
            recommendations.append("检查向量数据库连接和索引状态")
            recommendations.append("验证文档格式和解析器支持")
            if "vector" in root_cause.lower():
                recommendations.append("检查向量索引是否正常构建")
                recommendations.append("验证嵌入模型是否正常工作")
            recommendations.append("检查文档存储路径和权限")
        
        elif category == ErrorCategory.FRONTEND_UI:
            recommendations.append("检查API端点是否可访问")
            recommendations.append("验证前端状态管理逻辑")
            recommendations.append("检查网络连接和CORS配置")
        
        # 基于错误类型
        if error_type == ErrorType.CODE_ERROR:
            recommendations.append("检查相关代码文件的错误处理逻辑")
            recommendations.append("添加更详细的错误日志")
        
        elif error_type == ErrorType.CONFIG_ERROR:
            recommendations.append("验证配置文件格式和内容")
            recommendations.append("检查环境变量和配置参数")
        
        elif error_type == ErrorType.DATA_ERROR:
            recommendations.append("验证输入数据的格式和完整性")
            recommendations.append("添加数据验证和清理逻辑")
        
        elif error_type == ErrorType.ENVIRONMENT_ERROR:
            recommendations.append("检查服务运行状态和资源使用情况")
            recommendations.append("验证网络连接和防火墙设置")
            recommendations.append("检查日志以获取更多环境信息")
        
        elif error_type == ErrorType.INTERACTION_ERROR:
            recommendations.append("检查服务间通信配置")
            recommendations.append("验证API接口定义和版本兼容性")
            recommendations.append("检查服务依赖和启动顺序")
        
        # 通用建议
        recommendations.append("查看详细错误日志和堆栈跟踪")
        recommendations.append("检查相关服务的健康状态")
        
        return recommendations[:10]  # 限制建议数量
    
    def _calculate_confidence(
        self,
        pattern: Optional[ErrorPattern],
        error_traceback: Optional[str],
        context: Dict[str, Any],
        related_components: List[str]
    ) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 如果有匹配的模式，增加置信度
        if pattern:
            confidence += 0.2
        
        # 如果有堆栈跟踪，增加置信度
        if error_traceback:
            confidence += 0.15
        
        # 如果有上下文信息，增加置信度
        if context:
            confidence += 0.1
        
        # 如果能识别相关组件，增加置信度
        if related_components:
            confidence += 0.05 * min(len(related_components), 3)
        
        return min(confidence, 1.0)
    
    def analyze_langgraph_workflow_path(
        self,
        workflow_state: Dict[str, Any],
        execution_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析LangGraph工作流执行路径
        
        Args:
            workflow_state: 工作流状态
            execution_log: 执行日志
        
        Returns:
            执行路径分析结果
        """
        analysis = {
            "executed_nodes": [],
            "failed_nodes": [],
            "execution_order": [],
            "state_transitions": [],
            "issues": []
        }
        
        # 分析执行日志
        for log_entry in execution_log:
            if "node_id" in log_entry:
                analysis["executed_nodes"].append(log_entry["node_id"])
                analysis["execution_order"].append({
                    "node_id": log_entry["node_id"],
                    "timestamp": log_entry.get("timestamp"),
                    "status": log_entry.get("status", "unknown")
                })
                
                if log_entry.get("status") == "failed":
                    analysis["failed_nodes"].append(log_entry["node_id"])
                    analysis["issues"].append({
                        "node": log_entry["node_id"],
                        "error": log_entry.get("error"),
                        "timestamp": log_entry.get("timestamp")
                    })
            
            if "state_before" in log_entry and "state_after" in log_entry:
                analysis["state_transitions"].append({
                    "node": log_entry.get("node_id"),
                    "changed_keys": self._get_state_changes(
                        log_entry["state_before"],
                        log_entry["state_after"]
                    )
                })
        
        return analysis
    
    def _get_state_changes(
        self,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any]
    ) -> List[str]:
        """获取状态变化"""
        changes = []
        
        # 检查新增的键
        for key in state_after:
            if key not in state_before:
                changes.append(f"+{key}")
            elif state_before[key] != state_after[key]:
                changes.append(f"~{key}")
        
        # 检查删除的键
        for key in state_before:
            if key not in state_after:
                changes.append(f"-{key}")
        
        return changes
    
    def check_mcp_tool_health(
        self,
        tool_name: str,
        tool_registry_status: Dict[str, Any],
        recent_executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        检测MCP工具的健康状态
        
        Args:
            tool_name: 工具名称
            tool_registry_status: 工具注册状态
            recent_executions: 最近的执行记录
        
        Returns:
            健康状态报告
        """
        health_report = {
            "tool_name": tool_name,
            "is_registered": tool_registry_status.get("is_registered", False),
            "is_active": tool_registry_status.get("is_active", False),
            "success_rate": 0.0,
            "average_execution_time": 0.0,
            "recent_errors": [],
            "health_status": "unknown",
            "recommendations": []
        }
        
        if not health_report["is_registered"]:
            health_report["health_status"] = "not_registered"
            health_report["recommendations"].append("工具未注册，需要先注册工具")
            return health_report
        
        if not health_report["is_active"]:
            health_report["health_status"] = "inactive"
            health_report["recommendations"].append("工具已注册但未激活")
            return health_report
        
        # 分析最近的执行记录
        if recent_executions:
            successful = sum(1 for exe in recent_executions if exe.get("success", False))
            total = len(recent_executions)
            health_report["success_rate"] = successful / total if total > 0 else 0.0
            
            execution_times = [
                exe.get("execution_time", 0) for exe in recent_executions
                if exe.get("execution_time")
            ]
            if execution_times:
                health_report["average_execution_time"] = sum(execution_times) / len(execution_times)
            
            # 收集最近的错误
            for exe in recent_executions:
                if not exe.get("success", False):
                    health_report["recent_errors"].append({
                        "timestamp": exe.get("timestamp"),
                        "error": exe.get("error_message"),
                        "parameters": exe.get("parameters")
                    })
            
            # 确定健康状态
            if health_report["success_rate"] >= 0.95:
                health_report["health_status"] = "healthy"
            elif health_report["success_rate"] >= 0.80:
                health_report["health_status"] = "degraded"
            else:
                health_report["health_status"] = "unhealthy"
                health_report["recommendations"].append("工具成功率较低，需要检查工具实现")
            
            if health_report["average_execution_time"] > 10.0:
                health_report["recommendations"].append("工具执行时间较长，可能需要优化性能")
        else:
            health_report["health_status"] = "no_data"
            health_report["recommendations"].append("没有执行记录，无法评估健康状态")
        
        return health_report
    
    def to_dict(self, analysis: ErrorAnalysis) -> Dict[str, Any]:
        """将分析结果转换为字典"""
        result = asdict(analysis)
        result["timestamp"] = analysis.timestamp.isoformat()
        result["category"] = analysis.category.value
        result["error_type"] = analysis.error_type.value
        result["business_scenario"] = analysis.business_scenario.value
        return result


# 全局分析器实例
_analyzer_instance: Optional[PlatformErrorAnalyzer] = None


def get_error_analyzer() -> PlatformErrorAnalyzer:
    """获取错误分析器实例（单例模式）"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PlatformErrorAnalyzer()
    return _analyzer_instance


# 便捷函数
def analyze_error(
    error_message: str,
    error_traceback: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    分析错误的便捷函数
    
    Args:
        error_message: 错误消息
        error_traceback: 错误堆栈跟踪
        context: 错误上下文信息
        metadata: 元数据
    
    Returns:
        错误分析结果（字典格式）
    """
    analyzer = get_error_analyzer()
    analysis = analyzer.analyze_error(error_message, error_traceback, context, metadata)
    return analyzer.to_dict(analysis)

