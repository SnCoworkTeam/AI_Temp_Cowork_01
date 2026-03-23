"""
统一意图服务
作为图谱导航器，提供增强的意图理解能力
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.enterprise_semantic_engine import EnterpriseSemanticEngine, IntentQueryResult
from services.llm_client import RobustDeepSeekClient
from services.semantic_engine_adapter import SemanticEngineAdapter
from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import ActivityCapabilityMapping, CapabilityUnit

# OS Core集成 - AI Shell功能
try:
    import sys
    from pathlib import Path
    # 添加os-core目录到路径
    os_core_path = Path(__file__).parent.parent / "os-core"
    if str(os_core_path) not in sys.path:
        sys.path.insert(0, str(os_core_path))
    
    from resource_registry import ResourceRegistry
    from resource_resolver import ResourceResolver
    OS_CORE_AVAILABLE = True
except ImportError as e:
    OS_CORE_AVAILABLE = False
    logger.warning(f"os-core模块未找到，AI Shell功能将不可用: {e}")

import logging
import json
import re
import time

logger = logging.getLogger(__name__)


@dataclass
class ExecutionSuggestion:
    """执行建议"""
    activity_id: str
    activity_name: str
    capability_id: Optional[str]
    capability_name: Optional[str]
    input_schema: Optional[Dict[str, Any]]
    estimated_time: Optional[str]
    confidence: float


@dataclass
class UnifiedIntentResult:
    """统一意图识别结果"""
    user_input: str
    base_intent: str
    intent_type: str
    confidence: float
    suggested_activities: List[Dict[str, Any]]
    related_entities: List[Dict[str, Any]]
    available_capabilities: List[Dict[str, Any]]
    execution_suggestions: List[ExecutionSuggestion]
    reasoning: str
    fallback_mode: bool
    query_time: float
    # AI Shell扩展字段（可选）
    resolved_resources: Optional[Dict[str, List[str]]] = None  # 解析后的资源
    resource_operations: Optional[List[Dict[str, Any]]] = None  # 资源操作计划


class UnifiedIntentService:
    """统一意图服务 - 图谱导航器"""
    
    def __init__(self):
        """初始化统一意图服务"""
        # 初始化数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("数据库连接失败")
        
        init_session_factory()
        
        self.semantic_engine = EnterpriseSemanticEngine()
        self.semantic_adapter = SemanticEngineAdapter(self.semantic_engine)
        self._db = None
        
        # LLM配置
        self.use_llm = os.getenv("UNIFIED_INTENT_USE_LLM", "true").lower() == "true"
        self.llm_client = None
        if self.use_llm:
            try:
                self.llm_client = RobustDeepSeekClient(
                    api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
                    model=os.getenv("LLM_MODEL", "deepseek-chat"),
                    timeout=float(os.getenv("LLM_TIMEOUT", "10.0")),
                    temperature=float(os.getenv("LLM_TEMPERATURE", "0.3"))
                )
                logger.info("LLM客户端初始化成功")
            except Exception as e:
                logger.warning(f"LLM客户端初始化失败: {e}，将降级到规则匹配")
                self.use_llm = False
                self.llm_client = None
        
        # 简单的缓存
        self.cache = {}
        self.cache_ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))
        
        # 降级配置
        self.fallback_to_rules = os.getenv("LLM_FALLBACK_TO_RULES", "true").lower() == "true"
        
        # OS Core集成 - AI Shell（命令解释器）
        self.resource_registry = None
        self.resource_resolver = None
        if OS_CORE_AVAILABLE:
            try:
                self.resource_registry = ResourceRegistry()
                self.resource_resolver = ResourceResolver(self.resource_registry)
                logger.info("AI Shell（资源解析器）初始化成功")
            except Exception as e:
                logger.warning(f"AI Shell初始化失败: {e}，将使用原有功能")
                self.resource_registry = None
                self.resource_resolver = None
        
        # 策略引擎和审计日志集成（里程碑3）
        self.policy_engine = None
        self.audit_logger = None
        if OS_CORE_AVAILABLE:
            try:
                from policy_engine import PolicyEngine
                from audit_logger import AuditLogger
                self.policy_engine = PolicyEngine()
                self.audit_logger = AuditLogger()
                logger.info("策略引擎和审计日志初始化成功")
            except Exception as e:
                logger.warning(f"策略引擎初始化失败: {e}，策略评估将跳过")
                self.policy_engine = None
                self.audit_logger = None
        
        # 行为数据收集器集成（里程碑4）
        self.behavior_collector = None
        if OS_CORE_AVAILABLE:
            try:
                from behavior_collector import BehaviorCollector
                self.behavior_collector = BehaviorCollector()
                logger.info("行为数据收集器初始化成功")
            except Exception as e:
                logger.warning(f"行为数据收集器初始化失败: {e}，行为收集将跳过")
                self.behavior_collector = None
    
    def _get_db(self):
        """获取数据库会话"""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    def _close_db(self):
        """关闭数据库会话"""
        if self._db:
            self._db.close()
            self._db = None
    
    async def understand_intent(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> UnifiedIntentResult:
        """
        理解用户意图（统一入口）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
        
        Returns:
            UnifiedIntentResult: 统一意图识别结果
        """
        import time
        import hashlib
        start_time = time.time()
        
        # 检查缓存
        cache_key = hashlib.md5(f"{user_input}:{str(context)}".encode()).hexdigest()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (time.time() - cached["timestamp"]) < self.cache_ttl:
                logger.debug("Cache hit for intent query")
                return cached["result"]
        
        try:
            # 1. LLM意图分析（优先）
            if self.use_llm and self.llm_client:
                try:
                    llm_result = await self._analyze_intent_with_llm(user_input, context)
                except Exception as e:
                    logger.warning(f"LLM分析失败: {e}，降级到规则匹配")
                    llm_result = self._analyze_intent_base(user_input)
                    llm_result["needs_semantic_search"] = True
            else:
                # 降级到规则匹配
                llm_result = self._analyze_intent_base(user_input)
                llm_result["needs_semantic_search"] = True
            
            # 2. 如果LLM建议进行语义搜索，查询企业语义引擎
            semantic_results = None
            if llm_result.get("needs_semantic_search", True):
                try:
                    semantic_results = await self.semantic_adapter.query_intent_enhanced(
                        user_input=user_input,
                        llm_result=llm_result,
                        context=context,
                        top_k=10,
                        min_score=0.5
                    )
                except Exception as e:
                    logger.warning(f"语义引擎查询失败: {e}")
                    semantic_results = None
            
            # 2.5. EA增强的语义查询（新增）
            ea_results = None
            try:
                ea_results = await self._query_enterprise_architecture(
                    user_input=user_input,
                    llm_result=llm_result
                )
            except Exception as e:
                logger.warning(f"EA查询失败: {e}")
                ea_results = None
            
            # 3. 融合LLM结果、语义引擎结果和EA结果
            fused_result = self._dynamic_fusion_strategy(
                llm_result, 
                semantic_results,
                ea_results  # 新增EA结果
            )
            
            # 4. 转换为统一结果格式
            suggested_activities = []
            if semantic_results and semantic_results.activities:
                for activity, score in zip(semantic_results.activities, semantic_results.scores):
                    suggested_activities.append({
                        "id": activity.id,
                        "name": activity.name,
                        "description": activity.description,
                        "activity_type": activity.activity_type,
                        "business_domain": activity.business_domain,
                        "similarity_score": score,
                        "vector_entity_uri": activity.vector_entity_uri
                    })
            
            # 4.5. 添加EA结果到suggested_activities（新增）
            if ea_results and fused_result.get("ea_results"):
                # 将EA业务流程转换为活动格式（简化实现）
                for process in ea_results.get("processes", [])[:3]:  # 限制数量
                    suggested_activities.append({
                        "id": f"ea:process:{process.id}",
                        "name": process.name,
                        "description": process.description or "",
                        "activity_type": "business_process",
                        "business_domain": getattr(process, "business_domain", None),
                        "similarity_score": 0.7,  # EA结果默认分数
                        "vector_entity_uri": None,
                        "source": "ea"  # 标记来源
                    })
            
            # 5. 构建执行建议（使用LLM提取的实体）
            execution_suggestions = await self._build_execution_suggestions(
                suggested_activities,
                llm_result.get("extracted_entities", {})
            )
            
            # 6. AI Shell功能：解析意图到资源（如果可用）
            resolved_resources = {}
            resource_operations = []
            if self.resource_resolver:
                try:
                    intent_dict = {
                        "user_input": user_input,
                        "base_intent": llm_result.get("intent", "simple_chat"),
                        "confidence": fused_result.get("final_confidence", 0.5),
                        "suggested_activities": suggested_activities,
                        "extracted_entities": llm_result.get("extracted_entities", {})
                    }
                    resolution_result = self.resource_resolver.resolve_intent_to_resources(intent_dict)
                    
                    # 转换为字典格式以便序列化
                    resolved_resources = {
                        "objects": [r.id for r in resolution_result.objects],
                        "systems": [r.id for r in resolution_result.systems],
                        "knowledge": [r.id for r in resolution_result.knowledge],
                        "workflows": [r.id for r in resolution_result.workflows],
                        "data_entities": [r.id for r in resolution_result.data_entities]
                    }
                    resource_operations = [op.to_dict() for op in resolution_result.operations]
                    
                    # 7. 策略评估（里程碑3）- 对每个资源操作进行策略评估
                    if self.policy_engine and resource_operations:
                        try:
                            from resource_operations import ResourceOperation, ResourceOperationType
                            from resource_model import ResourceType
                            
                            # 获取用户上下文（从context参数或默认值）
                            user_context = context or {}
                            user_id = user_context.get("user_id", "unknown")
                            user_role = user_context.get("role", "guest")
                            
                            evaluated_operations = []
                            for op_dict in resource_operations:
                                # 转换为ResourceOperation对象
                                try:
                                    op_type = ResourceOperationType(op_dict.get("operation_type", "query"))
                                    resource_type_str = op_dict.get("resource_type", "business_object")
                                    # 尝试转换为ResourceType枚举
                                    try:
                                        resource_type = ResourceType(resource_type_str)
                                    except:
                                        resource_type = resource_type_str
                                    
                                    operation = ResourceOperation(
                                        operation_type=op_type,
                                        resource_id=op_dict.get("resource_id", ""),
                                        resource_type=resource_type,
                                        action=op_dict.get("action", ""),
                                        parameters=op_dict.get("parameters", {}),
                                        context=op_dict.get("context")
                                    )
                                    
                                    # 策略评估
                                    policy_context = {
                                        "user": user_id,
                                        "role": user_role,
                                        "timestamp": datetime.now(),
                                        "metadata": user_context
                                    }
                                    
                                    evaluation = self.policy_engine.evaluate(operation, policy_context)
                                    
                                    # 记录策略评估审计日志
                                    if self.audit_logger:
                                        self.audit_logger.log_policy_evaluation(
                                            user=user_id,
                                            role=user_role,
                                            resource_id=operation.resource_id,
                                            operation=operation.operation_type.value,
                                            evaluation_result={
                                                "allowed": evaluation.allowed,
                                                "action": evaluation.action.value,
                                                "reason": evaluation.reason
                                            },
                                            allowed=evaluation.allowed
                                        )
                                    
                                    # 如果允许，应用策略（可能添加审批、限制等）
                                    if evaluation.allowed or evaluation.action.value == "require_approval":
                                        operation = self.policy_engine.apply_policy(operation, evaluation)
                                        evaluated_operations.append({
                                            **op_dict,
                                            "policy_evaluation": {
                                                "allowed": evaluation.allowed,
                                                "action": evaluation.action.value,
                                                "reason": evaluation.reason,
                                                "required_approvals": evaluation.required_approvals,
                                                "restrictions": evaluation.restrictions
                                            }
                                        })
                                    else:
                                        # 被拒绝的操作，记录但不添加到结果中
                                        logger.warning(f"操作被策略拒绝: {evaluation.reason}")
                                        
                                except Exception as e:
                                    logger.warning(f"策略评估失败: {e}，保留原始操作")
                                    evaluated_operations.append(op_dict)
                            
                            resource_operations = evaluated_operations
                            
                        except Exception as e:
                            logger.warning(f"策略评估过程失败: {e}，使用原始操作")
                    
                    logger.debug(f"AI Shell解析完成: {len(resource_operations)} 个操作")
                except Exception as e:
                    logger.warning(f"AI Shell资源解析失败: {e}")
            
            # 记录意图识别审计日志
            if self.audit_logger:
                user_context = context or {}
                user_id = user_context.get("user_id", "unknown")
                user_role = user_context.get("role", "guest")
                self.audit_logger.log_intent_recognition(
                    user=user_id,
                    role=user_role,
                    intent=user_input,
                    recognized_intent={
                        "base_intent": llm_result.get("intent", "simple_chat"),
                        "confidence": fused_result.get("final_confidence", 0.5),
                        "suggested_activities_count": len(suggested_activities)
                    },
                    success=True
                )
            
            # 收集行为数据（里程碑4）
            if self.behavior_collector:
                try:
                    user_context = context or {}
                    user_id = user_context.get("user_id", "unknown")
                    
                    # 收集意图调用数据
                    self.behavior_collector.collect_intent_call(
                        user_input=user_input,
                        recognized_intent=llm_result.get("intent", "simple_chat"),
                        confidence=fused_result.get("final_confidence", 0.5),
                        execution_time=time.time() - start_time,
                        success=True,
                        suggested_activities=[a.get("id", "") for a in suggested_activities],
                        resource_operations=[op.get("resource_id", "") for op in resource_operations] if resource_operations else [],
                        user_id=user_id,
                        context=user_context
                    )
                    
                    # 收集资源使用数据
                    if resource_operations:
                        for op in resource_operations:
                            self.behavior_collector.collect_resource_usage(
                                resource_id=op.get("resource_id", ""),
                                resource_type=op.get("resource_type", ""),
                                operation=op.get("operation", ""),
                                execution_time=0.0,  # 实际执行时间未知
                                success=True,
                                user_id=user_id
                            )
                except Exception as e:
                    logger.warning(f"行为数据收集失败: {e}")
            
            result = UnifiedIntentResult(
                user_input=user_input,
                base_intent=llm_result.get("intent", "simple_chat"),
                intent_type=llm_result.get("intent", "simple_chat"),
                confidence=fused_result.get("final_confidence", 0.5),
                suggested_activities=suggested_activities,
                related_entities=[],
                available_capabilities=[],
                execution_suggestions=execution_suggestions,
                reasoning=fused_result.get("reasoning", llm_result.get("reasoning", "")),
                fallback_mode=False,
                query_time=time.time() - start_time
            )
            
            # 添加资源解析结果到结果对象（通过扩展字段）
            if resolved_resources:
                result.resolved_resources = resolved_resources
            if resource_operations:
                result.resource_operations = resource_operations
            
            # 缓存结果
            self.cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            # 降级处理
            base_intent = self._analyze_intent_base(user_input)
            return UnifiedIntentResult(
                user_input=user_input,
                base_intent=base_intent["intent"],
                intent_type=base_intent["intent"],
                confidence=base_intent["confidence"] * 0.8,
                suggested_activities=[],
                related_entities=[],
                available_capabilities=[],
                execution_suggestions=[],
                reasoning=f"降级模式: {base_intent['reasoning']}",
                fallback_mode=True,
                query_time=time.time() - start_time
            )
    
    async def _analyze_intent_with_llm(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用DeepSeek LLM进行意图分析（批处理版本）"""
        system_prompt = self._build_llm_system_prompt(context)
        
        user_prompt = f"""
用户输入: {user_input}

请分析用户意图，返回JSON格式：
{{
    "intent": "意图类型（tool_execution/workflow_task/knowledge_search/simple_chat）",
    "confidence": 0.0-1.0,
    "business_domain": "业务领域（procurement/finance/warehouse等，如果不确定则为null）",
    "extracted_entities": {{
        "supplier": "供应商名称或代码",
        "material": "物料编号或名称",
        "quantity": "数量",
        "po_number": "采购订单号",
        "date": "日期",
        ...
    }},
    "query_keywords": ["关键词1", "关键词2", ...],
    "reasoning": "分析理由",
    "needs_semantic_search": true/false
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await asyncio.wait_for(
                self.llm_client.chat_completion(messages),
                timeout=float(os.getenv("LLM_TIMEOUT", "10.0"))
            )
            
            # 解析LLM响应
            result = self._parse_llm_response(response.get("content", ""))
            return result
            
        except asyncio.TimeoutError:
            logger.warning("LLM分析超时，降级到规则匹配")
            return self._analyze_intent_base(user_input)
        except Exception as e:
            logger.error(f"LLM分析失败: {e}，降级到规则匹配")
            return self._analyze_intent_base(user_input)
    
    async def _analyze_intent_with_llm_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        使用DeepSeek LLM进行意图分析（流式版本）- 阶段2
        
        Yields:
            Dict: 流式分析结果
        """
        if not self.use_llm or not self.llm_client:
            # 降级到批处理
            result = await self._analyze_intent_with_llm(user_input, context)
            yield {
                "stage": "complete",
                "result": result,
                "progress": 100
            }
            return
        
        system_prompt = self._build_llm_system_prompt(context)
        
        user_prompt = f"""
用户输入: {user_input}

请分析用户意图，返回JSON格式：
{{
    "intent": "意图类型（tool_execution/workflow_task/knowledge_search/simple_chat）",
    "confidence": 0.0-1.0,
    "business_domain": "业务领域（procurement/finance/warehouse等，如果不确定则为null）",
    "extracted_entities": {{
        "supplier": "供应商名称或代码",
        "material": "物料编号或名称",
        "quantity": "数量",
        "po_number": "采购订单号",
        "date": "日期",
        ...
    }},
    "query_keywords": ["关键词1", "关键词2", ...],
    "reasoning": "分析理由",
    "needs_semantic_search": true/false
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            full_content = []
            chunk_count = 0
            last_progress_update = 0
            progress_update_interval = 8  # 优化：每8个chunk更新一次（减少更新频率）
            min_chars_for_update = 80  # 优化：至少80个字符才更新（减少更新频率）
            
            # 流式调用LLM
            async for chunk in self.llm_client.chat_completion_stream(messages):
                content = chunk.get("content", "")
                if content:
                    full_content.append(content)  # 优化：使用列表而不是字符串拼接
                    chunk_count += 1
                    
                    # 优化：减少进度更新频率，提高性能
                    current_length = sum(len(c) for c in full_content)
                    should_update = (
                        chunk_count - last_progress_update >= progress_update_interval or
                        (current_length - last_progress_update * min_chars_for_update) >= min_chars_for_update
                    )
                    
                    if should_update:
                        # 优化：只在需要时构建字符串
                        accumulated_str = ''.join(full_content[:10]) if len(full_content) > 10 else ''.join(full_content)
                        if len(accumulated_str) > 200:
                            accumulated_str = accumulated_str[:200]
                        
                        yield {
                            "stage": "analyzing",
                            "content": content,
                            "accumulated": accumulated_str,
                            "progress": 20 + min(30, current_length / 10),  # 20-50%范围
                            "chunk_count": chunk_count
                        }
                        last_progress_update = chunk_count
                
                # 检查是否完成
                if chunk.get("finish_reason"):
                    # 优化：只在完成时构建完整字符串
                    full_content_str = ''.join(full_content)
                    
                    # 解析最终结果
                    try:
                        result = self._parse_llm_response(full_content_str)
                        yield {
                            "stage": "complete",
                            "result": result,
                            "progress": 50,
                            "full_content": full_content_str[:500]  # 限制长度，减少传输
                        }
                    except Exception as e:
                        logger.error(f"解析LLM流式响应失败: {e}")
                        # 降级到规则匹配
                        result = self._analyze_intent_base(user_input)
                        yield {
                            "stage": "complete",
                            "result": result,
                            "progress": 50,
                            "error": f"解析失败: {e}"
                        }
                    break
                    
        except asyncio.TimeoutError:
            logger.warning("LLM流式分析超时，降级到规则匹配")
            result = self._analyze_intent_base(user_input)
            yield {
                "stage": "complete",
                "result": result,
                "progress": 50,
                "error": "超时"
            }
        except Exception as e:
            logger.error(f"LLM流式分析失败: {e}，降级到规则匹配")
            result = self._analyze_intent_base(user_input)
            yield {
                "stage": "complete",
                "result": result,
                "progress": 50,
                "error": str(e)
            }
    
    def _build_llm_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """构建LLM系统提示词（优化版，包含少样本学习）"""
        few_shot_examples = [
            {
                "input": "我需要创建采购订单，供应商ABC，物料MAT001，数量100",
                "output": {
                    "intent": "tool_execution",
                    "confidence": 0.95,
                    "business_domain": "procurement",
                    "extracted_entities": {
                        "supplier": "ABC",
                        "material": "MAT001",
                        "quantity": "100"
                    },
                    "query_keywords": ["采购订单", "创建", "供应商", "物料"],
                    "reasoning": "明确的操作请求，涉及采购订单创建，需要调用SAP系统",
                    "needs_semantic_search": True
                }
            },
            {
                "input": "查询一下采购订单PO1001的状态",
                "output": {
                    "intent": "tool_execution",
                    "confidence": 0.90,
                    "business_domain": "procurement",
                    "extracted_entities": {
                        "po_number": "PO1001"
                    },
                    "query_keywords": ["采购订单", "查询", "状态"],
                    "reasoning": "查询操作，需要调用SAP查询接口",
                    "needs_semantic_search": True
                }
            },
            {
                "input": "什么是采购订单？",
                "output": {
                    "intent": "simple_chat",
                    "confidence": 0.85,
                    "business_domain": None,
                    "extracted_entities": {},
                    "query_keywords": ["采购订单", "概念"],
                    "reasoning": "知识性问题，不需要执行操作",
                    "needs_semantic_search": False
                }
            }
        ]
        
        base_prompt = f"""
# 角色与目标
你是企业AI助手统一意图理解层的核心分析引擎，专门将员工模糊的业务请求，精准解析为标准化的执行指令。

# 核心任务
1. **意图分类**：严格从以下4类中选择：
   - `tool_execution`: 需要调用具体系统（如SAP）执行一个原子操作
   - `workflow_task`: 涉及多个步骤或需要审批的流程
   - `knowledge_search`: 仅查询信息或文档，不修改系统数据
   - `simple_chat`: 问候、咨询等非操作类对话

2. **实体提取**：仅提取**可用于系统API调用**的明确实体（如订单号、物料编码、供应商代码）

3. **业务领域识别**：识别业务领域（procurement/finance/warehouse/sales/hr），如果不确定返回null

4. **查询增强**：为后续企业知识图谱检索生成2-4个最相关的业务关键词

# 输出格式
你必须返回一个**严格的JSON对象**，且仅包含以下字段：
- `intent`: 意图类型（字符串）
- `confidence`: 置信度（0.0-1.0）
- `business_domain`: 业务领域（字符串或null）
- `extracted_entities`: 实体字典
- `query_keywords`: 关键词列表
- `reasoning`: 分析理由（字符串）
- `needs_semantic_search`: 是否需要语义搜索（布尔值）

# 少样本示例（Few-shot Examples）
{json.dumps(few_shot_examples, ensure_ascii=False, indent=2)}

# 重要规则
- 如果用户查询SAP ERP数据（如销售订单、采购订单、物料、客户、供应商等），必须使用 `tool_execution` 类型
- 如果用户提到"SAP"、"ERP"、"查询"、"查一下"等关键词，且涉及具体业务数据，应识别为 `tool_execution`
- 如果只是询问SAP概念、使用方法等知识性问题，可以使用 `simple_chat`
- 对于SAP查询，`extracted_entities` 应包含具体的业务实体（如订单号、物料编码等）
- `confidence` 必须反映你对分析结果的确定程度，不确定时应该较低（<0.7）
"""
        
        if context:
            context_info = f"""
# 上下文信息
{json.dumps(context, ensure_ascii=False, indent=2)}

请结合上下文信息进行意图分析。
"""
            base_prompt += context_info
        
        return base_prompt
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON（可能包含markdown代码块）
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                response_content = json_match.group(1)
            else:
                # 尝试直接提取JSON对象
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
            
            result = json.loads(response_content)
            
            # 验证必需字段
            if "intent" not in result:
                result["intent"] = "simple_chat"
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "extracted_entities" not in result:
                result["extracted_entities"] = {}
            if "query_keywords" not in result:
                result["query_keywords"] = []
            if "needs_semantic_search" not in result:
                result["needs_semantic_search"] = True
            
            return result
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}，使用默认值")
            return {
                "intent": "simple_chat",
                "confidence": 0.5,
                "business_domain": None,
                "extracted_entities": {},
                "query_keywords": [],
                "reasoning": f"LLM响应解析失败: {e}",
                "needs_semantic_search": True
            }
    
    def _analyze_intent_base(self, user_input: str) -> Dict[str, Any]:
        """基础意图分析（规则匹配）"""
        user_lower = user_input.lower()
        
        if any(re.search(pattern, user_lower) for pattern in [
            r"执行|调用|运行|使用.*工具",
            r"tool|execute|run"
        ]):
            return {
                "intent": "tool_execution",
                "confidence": 0.7,
                "reasoning": "检测到工具执行意图",
                "business_domain": None,
                "extracted_entities": {},
                "query_keywords": [],
                "needs_semantic_search": True
            }
        elif any(re.search(pattern, user_lower) for pattern in [
            r"工作流|流程|workflow",
            r"创建.*流程"
        ]):
            return {
                "intent": "workflow_task",
                "confidence": 0.7,
                "reasoning": "检测到工作流任务意图",
                "business_domain": None,
                "extracted_entities": {},
                "query_keywords": [],
                "needs_semantic_search": True
            }
        elif any(re.search(pattern, user_lower) for pattern in [
            r"搜索|查找|查询",
            r"search|find"
        ]):
            return {
                "intent": "knowledge_search",
                "confidence": 0.7,
                "reasoning": "检测到搜索意图",
                "business_domain": None,
                "extracted_entities": {},
                "query_keywords": [],
                "needs_semantic_search": True
            }
        else:
            return {
                "intent": "simple_chat",
                "confidence": 0.5,
                "reasoning": "默认简单对话意图",
                "business_domain": None,
                "extracted_entities": {},
                "query_keywords": [],
                "needs_semantic_search": False
            }
    
    def _dynamic_fusion_strategy(
        self,
        llm_result: Dict[str, Any],
        semantic_results: Optional[IntentQueryResult] = None,
        ea_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """动态融合策略：根据场景智能调整权重（支持EA增强）"""
        llm_confidence = llm_result.get("confidence", 0.5)
        llm_domain = llm_result.get("business_domain")
        
        # 场景1: LLM置信度极高，但语义引擎无结果
        if llm_confidence > 0.9 and (not semantic_results or not semantic_results.activities):
            return {
                "final_confidence": llm_confidence * 0.95,
                "reasoning": "LLM高置信度但语义引擎无匹配，可能是新业务场景"
            }
        
        # 场景2: 语义引擎匹配到高相似度标准流程
        if semantic_results and semantic_results.scores and semantic_results.scores[0] > 0.85:
            semantic_score = semantic_results.scores[0]
            return {
                "final_confidence": semantic_score,
                "reasoning": "语义引擎匹配到高相似度标准流程，优先信任"
            }
        
        # 场景3: 两者结果冲突
        if semantic_results and semantic_results.activities:
            semantic_domain = semantic_results.activities[0].business_domain
            if llm_domain and semantic_domain and llm_domain != semantic_domain:
                return {
                    "final_confidence": 0.5,
                    "reasoning": f"LLM识别为{llm_domain}，但语义引擎匹配到{semantic_domain}，需要人工审核"
                }
        
        # 场景4: 加权平均
        if semantic_results and semantic_results.scores:
            semantic_score = semantic_results.scores[0]
            
            # 根据LLM置信度动态调整权重
            if llm_confidence > 0.8:
                weight_llm = 0.6
                weight_semantic = 0.4
            elif llm_confidence > 0.6:
                weight_llm = 0.5
                weight_semantic = 0.5
            else:
                weight_llm = 0.4
                weight_semantic = 0.6
            
            final_confidence = weight_llm * llm_confidence + weight_semantic * semantic_score
            
            return {
                "final_confidence": final_confidence,
                "reasoning": f"加权融合：LLM({llm_confidence:.2f}) * {weight_llm} + 语义({semantic_score:.2f}) * {weight_semantic}"
            }
        
        # 场景5: EA增强（新增）
        if ea_results:
            ea_boost = 0.0
            ea_info = []
            
            if ea_results.get("processes"):
                ea_boost += 0.1
                ea_info.append(f"找到{len(ea_results['processes'])}个相关业务流程")
            
            if ea_results.get("applications"):
                ea_boost += 0.1
                ea_info.append(f"找到{len(ea_results['applications'])}个相关应用系统")
            
            if ea_results.get("entities"):
                ea_boost += 0.05
                ea_info.append(f"找到{len(ea_results['entities'])}个相关数据实体")
            
            if ea_boost > 0:
                final_confidence = min(llm_confidence + ea_boost, 1.0)
                return {
                    "final_confidence": final_confidence,
                    "reasoning": f"EA增强：{'; '.join(ea_info)}",
                    "ea_results": ea_results  # 包含EA结果供后续使用
                }
        
        # 默认：只有LLM结果
        return {
            "final_confidence": llm_confidence * 0.8,
            "reasoning": "仅LLM结果，无语义引擎匹配"
        }
    
    async def recommend_activities(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推荐相关业务活动
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            top_k: 返回前k个推荐
        
        Returns:
            List[Dict]: 推荐的活动列表
        """
        try:
            # 查询语义引擎
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.semantic_engine.query_intent,
                user_input,
                context,
                top_k,
                0.5
            )
            
            # 转换为字典格式
            activities = []
            for activity, score in zip(result.activities, result.scores):
                activities.append({
                    "id": activity.id,
                    "name": activity.name,
                    "description": activity.description,
                    "activity_type": activity.activity_type,
                    "business_domain": activity.business_domain,
                    "similarity_score": score,
                    "vector_entity_uri": activity.vector_entity_uri
                })
            
            return activities
        
        except Exception as e:
            logger.error(f"推荐活动失败: {e}")
            return []
    
    async def get_capabilities_for_activity(
        self,
        activity_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取活动的能力单元
        
        Args:
            activity_id: 活动ID
        
        Returns:
            List[Dict]: 能力单元列表
        """
        try:
            db = self._get_db()
            
            # 查询映射
            mappings = db.query(ActivityCapabilityMapping).filter(
                ActivityCapabilityMapping.activity_id == activity_id
            ).order_by(
                ActivityCapabilityMapping.priority.desc(),
                ActivityCapabilityMapping.success_rate.desc()
            ).all()
            
            # 获取能力单元详情
            capabilities = []
            for mapping in mappings:
                capability = db.query(CapabilityUnit).filter_by(
                    id=mapping.capability_id
                ).first()
                
                if capability:
                    capabilities.append({
                        "mapping_id": mapping.id,
                        "capability_id": capability.id,
                        "capability_name": capability.name,
                        "capability_type": capability.capability_type,
                        "mapping_type": mapping.mapping_type,
                        "priority": mapping.priority,
                        "success_rate": mapping.success_rate,
                        "confidence": mapping.confidence,
                        "input_schema": capability.input_schema,
                        "output_schema": capability.output_schema,
                        "endpoint": capability.endpoint
                    })
            
            return capabilities
        
        except Exception as e:
            logger.error(f"获取活动能力失败: {e}")
            return []
    
    async def _build_execution_suggestions(
        self,
        suggested_activities: List[Dict[str, Any]],
        extracted_entities: Dict[str, Any] = None
    ) -> List[ExecutionSuggestion]:
        """
        构建执行建议
        
        Args:
            suggested_activities: 推荐的活动列表
        
        Returns:
            List[ExecutionSuggestion]: 执行建议列表
        """
        suggestions = []
        
        for activity in suggested_activities[:5]:  # 只处理前5个
            activity_id = activity.get("id")
            if not activity_id:
                continue
            
            # 获取能力单元
            try:
                capabilities = await self.get_capabilities_for_activity(activity_id)
            except Exception as e:
                logger.warning(f"获取活动 {activity_id} 的能力失败: {e}")
                capabilities = []
            
            # 选择最佳能力单元
            recommended_capability = None
            if capabilities:
                # 选择优先级最高且成功率最高的
                recommended_capability = max(
                    capabilities,
                    key=lambda c: (c.get("priority", 0), c.get("success_rate", 0))
                )
            
            # 自动填充参数（使用LLM提取的实体）
            input_schema = recommended_capability.get("input_schema") if recommended_capability else None
            auto_filled_params = self._auto_fill_parameters(input_schema, extracted_entities or {})
            
            suggestion = ExecutionSuggestion(
                activity_id=activity_id,
                activity_name=activity.get("name", ""),
                capability_id=recommended_capability.get("capability_id") if recommended_capability else None,
                capability_name=recommended_capability.get("capability_name") if recommended_capability else None,
                input_schema=input_schema,
                estimated_time=None,  # TODO: 从活动信息中获取
                confidence=recommended_capability.get("confidence", 0.7) if recommended_capability else 0.5
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _auto_fill_parameters(
        self,
        input_schema: Optional[Dict[str, Any]],
        extracted_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据LLM提取的实体，自动填充参数"""
        if not input_schema or not extracted_entities:
            return {}
        
        auto_filled = {}
        
        # 实体映射表
        entity_mapping = {
            "supplier": ["supplier_code", "supplier", "vendor_code"],
            "material": ["material_code", "material", "item_code"],
            "quantity": ["quantity", "qty", "amount"],
            "po_number": ["po_number", "purchase_order_number"],
            "customer": ["customer_code", "customer"],
            "date": ["date", "delivery_date", "order_date"],
        }
        
        for entity_key, entity_value in extracted_entities.items():
            if entity_value:
                # 查找匹配的参数名
                param_names = entity_mapping.get(entity_key, [])
                for param_name in param_names:
                    if input_schema and param_name in input_schema:
                        auto_filled[param_name] = entity_value
                        break
        
        return auto_filled
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "enabled": True,
            "total_entries": len(self.cache),
            "cache_ttl": self.cache_ttl
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._close_db()
        if self.llm_client:
            import asyncio
            try:
                asyncio.run(self.llm_client.close())
            except:
                pass


def main():
    """测试函数"""
    import asyncio
    
    print("=" * 60)
    print("统一意图服务测试")
    print("=" * 60)
    print()
    
    async def test():
        try:
            service = UnifiedIntentService()
            
            # 测试1: 意图理解
            print("[TEST] 测试意图理解...")
            result = await service.understand_intent("创建采购订单")
            print(f"  输入: {result.user_input}")
            print(f"  意图类型: {result.intent_type}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  推荐活动数: {len(result.suggested_activities)}")
            print(f"  降级模式: {result.fallback_mode}")
            print(f"  查询时间: {result.query_time:.3f}秒")
            if result.suggested_activities:
                print(f"  推荐活动:")
                for i, activity in enumerate(result.suggested_activities[:3], 1):
                    print(f"    {i}. {activity['name']}")
            print()
            
            # 测试2: 活动推荐
            print("[TEST] 测试活动推荐...")
            recommendations = await service.recommend_activities("查询订单", top_k=3)
            print(f"  推荐了 {len(recommendations)} 个活动:")
            for i, activity in enumerate(recommendations, 1):
                print(f"    {i}. {activity['name']} (相似度: {activity['similarity_score']:.2f})")
            print()
            
            # 测试3: 缓存统计
            print("[TEST] 测试缓存统计...")
            cache_stats = service.get_cache_stats()
            print(f"  缓存启用: {cache_stats.get('enabled', False)}")
            if cache_stats.get('enabled'):
                print(f"  总条目数: {cache_stats.get('total_entries', 0)}")
                print(f"  有效条目数: {cache_stats.get('valid_entries', 0)}")
            print()
            
            # 测试4: 获取活动能力
            print("[TEST] 测试获取活动能力...")
            capabilities = await service.get_capabilities_for_activity("activity:procurement:create_po")
            print(f"  找到 {len(capabilities)} 个能力单元:")
            for i, cap in enumerate(capabilities[:3], 1):
                print(f"    {i}. {cap.get('capability_name', 'N/A')} (优先级: {cap.get('priority', 0)})")
            print()
            
            print("=" * 60)
            print("[OK] 所有测试通过！")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            if 'service' in locals():
                service._close_db()
        
        return 0
    
    return asyncio.run(test())


if __name__ == "__main__":
    exit(main())

