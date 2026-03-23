"""
动态工作流设计器
为每个请求动态设计最优的智能体执行路径
"""
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncIterator
from collections import defaultdict, deque

from .llm_integration import deepseek_llm

logger = logging.getLogger(__name__)

# OS Core集成 - AI Shell功能
OS_CORE_AVAILABLE = False
ResourceRegistry = None
ResourceResolver = None

try:
    # 添加os-core目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    os_core_path = project_root / "os-core"
    if str(os_core_path) not in sys.path:
        sys.path.insert(0, str(os_core_path))
    
    from resource_registry import ResourceRegistry
    from resource_resolver import ResourceResolver
    OS_CORE_AVAILABLE = True
    logger.info("AI Shell（资源解析器）模块加载成功")
except ImportError as e:
    OS_CORE_AVAILABLE = False
    logger.warning(f"os-core模块未找到，AI Shell功能将不可用: {e}")


class DynamicWorkflowDesigner:
    """动态工作流设计器 - 为每个请求定制执行路径"""
    
    def __init__(self):
        self.llm = deepseek_llm
        self.agent_pool = self._initialize_agent_pool()
        
        # AI Shell集成 - 资源解析器
        self.resource_registry = None
        self.resource_resolver = None
        if OS_CORE_AVAILABLE and ResourceRegistry and ResourceResolver:
            try:
                self.resource_registry = ResourceRegistry()
                self.resource_resolver = ResourceResolver(self.resource_registry)
                logger.info("AI Shell（资源解析器）初始化成功")
            except Exception as e:
                logger.warning(f"AI Shell初始化失败: {e}，将使用原有功能")
                self.resource_registry = None
                self.resource_resolver = None
    
    def _initialize_agent_pool(self) -> Dict[str, Dict[str, Any]]:
        """初始化智能体池描述"""
        return {
            "metadata_agent": {
                    "name": "元数据智能体",
                    "description": "业务语义理解、实体映射、上下文增强、约束分析",
                    "capabilities": ["business_semantics", "entity_mapping", "context_enrichment", "constraint_analysis"]
                },
                "mcp_tool_agent": {
                    "name": "MCP工具智能体",
                    "description": "MCP工具执行、参数优化、错误处理（不包括SAP OData工具）",
                    "capabilities": ["tool_execution", "tool_selection", "parameter_optimization", "error_handling"]
                },
            "sap_odata_agent": {
                "name": "SAP OData智能体",
                "description": "SAP数据查询、业务操作和数据分析，基于SAP OData MCP服务动态执行",
                "capabilities": ["sap_data_query", "sap_business_operations", "sap_analytics", "dynamic_service_discovery", "intelligent_parameter_mapping"]
            },
                "workflow_agent": {
                    "name": "工作流智能体",
                    "description": "工作流编排、执行监控、状态管理、故障恢复",
                    "capabilities": ["workflow_orchestration", "execution_monitoring", "state_management", "recovery_handling"]
                },
            "knowledge_base_agent": {
                "name": "知识库智能体",
                "description": "知识库查询、语义搜索、知识图谱操作、相关概念查找",
                "capabilities": ["semantic_search", "keyword_search", "hybrid_search", "knowledge_graph_query", "related_concepts", "document_retrieval"]
            },
            "data_query_agent": {
                "name": "数据查询智能体",
                "description": "数据获取、查询优化、结果格式化",
                "capabilities": ["data_acquisition", "query_optimization", "result_formatting"]
            },
            "data_clean_agent": {
                "name": "数据清洗智能体",
                "description": "数据清洗、质量检查、数据标准化",
                "capabilities": ["data_cleaning", "quality_check", "data_standardization"]
            },
            "data_validation_agent": {
                "name": "数据验证智能体",
                "description": "数据验证、质量保证、完整性检查",
                "capabilities": ["data_validation", "quality_assurance", "integrity_check"]
            },
            "data_enrich_agent": {
                "name": "数据增强智能体",
                "description": "数据增强、特征工程、数据补充",
                "capabilities": ["data_enhancement", "feature_engineering", "data_enrichment"]
            },
            "analysis_agent": {
                "name": "分析智能体",
                "description": "数据分析、模式识别、统计分析",
                "capabilities": ["data_analysis", "pattern_recognition", "statistical_analysis"]
            },
            "insight_agent": {
                "name": "洞察生成智能体",
                "description": "洞察生成、业务解读、行动建议",
                "capabilities": ["insight_generation", "business_interpretation", "action_recommendation"]
            },
            "quality_check_agent": {
                "name": "质量检查智能体",
                "description": "质量检查、内容验证、一致性检查",
                "capabilities": ["quality_check", "content_validation", "consistency_check"]
            },
            "content_agent": {
                "name": "内容生成智能体",
                "description": "内容生成、结构化、报告撰写",
                "capabilities": ["content_generation", "structuring", "report_writing"]
            },
            "format_agent": {
                "name": "格式优化智能体",
                "description": "格式优化、模板应用、样式增强",
                "capabilities": ["format_optimization", "template_application", "style_enhancement"]
            },
            "result_synthesis_agent": {
                "name": "结果合成智能体",
                "description": "结果合成、冲突解决、优先级排序",
                "capabilities": ["result_synthesis", "conflict_resolution", "priority_ranking"]
            }
        }
    
    async def design_for_request(
        self,
        user_input: str,
        context: Dict[str, Any],
        stream: bool = False
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        为每个请求动态设计最优执行路径（支持流式输出）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            stream: 是否流式输出
            
        Yields:
            设计过程的流式输出
        """
        if stream:
            async for chunk in self._design_with_streaming(user_input, context):
                yield chunk
        else:
            design = await self._design_network(user_input, context)
            yield {
                "type": "design_complete",
                "design": design
            }
    
    async def _design_with_streaming(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式设计过程"""
        try:
            # 步骤1：生成思考描述（DeepSeek风格：包含意图分析、识别和依据说明）
            try:
                # 获取可用资源信息
                agent_pool_desc = self._get_agent_pool_description()
                
                thinking_prompt = f"""
用户请求: "{user_input}"
用户上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

可用资源：
{agent_pool_desc}

请用自然、流畅的长文本描述你对这个请求的完整思考过程，要求如下：

**第一部分：意图分析**
仔细分析用户想要什么，理解用户的真实意图，思考用户可能的业务场景和需求背景。

**第二部分：意图识别**
识别这个请求属于什么类型的任务（数据查询、数据分析、报告生成、内容创作、工具执行、知识检索等），分析这个请求涉及哪些业务领域和实体。

**第三部分：思考依据**
基于上述可用资源，说明你的思考依据：
- 我会基于哪些智能体和资源来处理这个请求
- 为什么选择这些资源
- 如何组织执行流程
- 预期的处理结果

**要求**：
- 使用自然、流畅的长文本描述，就像在深入思考一样
- 不要使用步骤编号、分类标签、复杂度等级等结构化信息
- 不要包含"复杂度"、"类型"、"预计时间"、"智能体数量"等分类信息
- 直接描述你的理解、识别和计划，形成连贯的思考过程
- 思考过程应该详细、深入，体现对用户意图的深入理解和对执行方案的思考
- 将意图分析、意图识别和思考依据自然地融合在一起，形成一段连贯的长文本思考过程

只返回思考描述文字，不要返回JSON或其他格式。
"""
                # 流式生成思考内容，实时显示
                thinking_text = ""
                
                # 构建LangChain消息格式
                # 从提示词模板获取系统提示词
                from .prompt_utils import get_system_prompt
                thinking_system_prompt = get_system_prompt(
                    "workflow_thinking",
                    fallback="你是一个AI助手，能够深入分析用户意图，识别任务类型，并基于可用资源制定执行方案。用自然、流畅的长文本描述你的完整思考过程。"
                )
                
                from langchain_core.messages import SystemMessage, HumanMessage
                langchain_messages = [
                    SystemMessage(content=thinking_system_prompt),
                    HumanMessage(content=thinking_prompt)
                ]
                
                # 使用LLM的流式接口
                if self.llm.llm and hasattr(self.llm.llm, 'astream'):
                    # LangChain流式接口
                    import asyncio
                    last_yield_time = asyncio.get_event_loop().time()
                    last_yield_length = 0
                    min_chars_between_yields = 30  # 至少累积30个字符才发送一次
                    min_time_between_yields = 0.3  # 至少间隔0.3秒才发送一次
                    
                    async for chunk in self.llm.llm.astream(langchain_messages):
                        chunk_text = ""
                        if hasattr(chunk, 'content'):
                            chunk_text = chunk.content
                        elif isinstance(chunk, dict):
                            chunk_text = chunk.get('content', chunk.get('text', ''))
                        else:
                            chunk_text = str(chunk)
                        
                        if chunk_text:
                            thinking_text += chunk_text
                            
                            # 节流：只在累积足够字符或经过足够时间时才yield
                            current_time = asyncio.get_event_loop().time()
                            chars_since_last_yield = len(thinking_text) - last_yield_length
                            time_since_last_yield = current_time - last_yield_time
                            
                            should_yield = (
                                chars_since_last_yield >= min_chars_between_yields or
                                time_since_last_yield >= min_time_between_yields
                            )
                            
                            if should_yield:
                                # 实时yield思考内容片段
                                yield {
                                    "type": "thinking",
                                    "stage": "analyzing_request",
                                    "message": thinking_text[:2000] if len(thinking_text) > 2000 else thinking_text,
                                    "progress": 30,
                                    "is_streaming": True  # 标记为流式输出
                                }
                                last_yield_time = current_time
                                last_yield_length = len(thinking_text)
                else:
                    # 降级：非流式，但先yield一个开始提示
                    yield {
                        "type": "thinking",
                        "stage": "analyzing_request",
                        "message": "正在思考...",
                        "progress": 30,
                        "is_streaming": True
                    }
                    # 然后获取完整响应
                    # 从提示词模板获取系统提示词
                    from .prompt_utils import get_system_prompt
                    thinking_system_prompt = get_system_prompt(
                        "workflow_thinking",
                        fallback="你是一个AI助手，能够深入分析用户意图，识别任务类型，并基于可用资源制定执行方案。用自然、流畅的长文本描述你的完整思考过程。"
                    )
                    
                    thinking_response = await self.llm.chat([
                        {"role": "system", "content": thinking_system_prompt},
                        {"role": "user", "content": thinking_prompt}
                    ])
                    thinking_text = thinking_response if isinstance(thinking_response, str) else thinking_response.get('content', '') if hasattr(thinking_response, 'get') else str(thinking_response)
                
                # 最终yield完整的思考内容（清理格式）
                thinking_text = thinking_text.strip()
                if thinking_text.startswith('```'):
                    # 移除代码块标记
                    lines = thinking_text.split('\n')
                    thinking_text = '\n'.join([line for line in lines if not line.strip().startswith('```')])
                
                # 移除2000字符限制，显示完整思考内容
                yield {
                    "type": "thinking",
                    "stage": "analyzing_request",
                    "message": thinking_text,  # 不再截断，显示完整内容
                    "progress": 30,
                    "is_streaming": False  # 标记为完成
                }
            except Exception as e:
                logger.error(f"Thinking generation failed: {e}", exc_info=True)
                # 降级：使用简单描述
                yield {
                    "type": "thinking",
                    "stage": "analyzing_request",
                    "message": f"理解用户想要{user_input}，需要分析相关数据并生成结果。",
                    "progress": 30
                }
            
            # 步骤2：分析请求（内部使用，不返回给前端）
            try:
                analysis = await self._analyze_request(user_input, context)
            except Exception as e:
                logger.error(f"Request analysis failed: {e}", exc_info=True)
                analysis = {
                    "complexity": "medium",
                    "request_type": "other",
                    "data_requirements": [],
                    "processing_type": "real_time"
                }
            
            # 步骤3：设计智能体网络（现在返回给前端，提升透明度）
            
            try:
                network_design = await self._design_network(user_input, context, analysis)
                # 返回设计结果给前端
                yield {
                    "type": "design",
                    "stage": "designing_network",
                    "network_design": network_design,
                    "progress": 60,
                    "message": f"智能体网络设计完成：{len(network_design.get('agents', []))}个智能体，{len(network_design.get('execution_layers', []))}个执行层"
                }
            except Exception as e:
                logger.error(f"Network design failed: {e}", exc_info=True)
                error_msg = str(e) if e and str(e) else "智能体网络设计过程中发生未知错误"
                error_type = type(e).__name__ if e else "UnknownError"
                yield {
                    "type": "error",
                    "stage": "designing_network",
                    "message": f"智能体网络设计失败：{error_msg}",
                    "error": error_msg,
                    "error_type": error_type
                }
                return
            
            if not network_design or not network_design.get("agents"):
                logger.warning("Network design is empty or invalid, using fallback")
                network_design = self._create_fallback_design(user_input, analysis)
                # 通知前端使用了fallback设计
                yield {
                    "type": "design",
                    "stage": "designing_network",
                    "network_design": network_design,
                    "progress": 60,
                    "message": "智能体网络设计完成（使用fallback设计）",
                    "warning": "原始设计为空，已使用fallback设计"
                }
            
            # 步骤4：验证和优化（现在返回给前端）
            try:
                validated_design = await self._validate_and_optimize(network_design, context)
                # 返回验证结果给前端
                yield {
                    "type": "design",
                    "stage": "validating_design",
                    "network_design": validated_design,
                    "progress": 80,
                    "message": "智能体网络验证和优化完成"
                }
            except Exception as e:
                logger.error(f"Design validation failed: {e}", exc_info=True)
                # 即使验证失败，也使用原始设计
                validated_design = network_design
                yield {
                    "type": "design",
                    "stage": "validating_design",
                    "network_design": validated_design,
                    "progress": 80,
                    "message": "智能体网络验证完成（验证过程出现错误，使用原始设计）",
                    "warning": f"验证过程出现错误：{str(e)}"
                }
            
            # 步骤4：完成
            yield {
                "type": "design_complete",
                "design": validated_design,
                "progress": 100
            }
        except Exception as e:
            logger.error(f"Design streaming failed: {e}", exc_info=True)
            error_msg = str(e) if e and str(e) else "工作流设计过程中发生未知错误"
            error_type = type(e).__name__ if e else "UnknownError"
            yield {
                "type": "error",
                "stage": "design",
                "message": f"工作流设计失败：{error_msg}",
                "error": error_msg,
                "error_type": error_type
            }
    
    async def _analyze_request(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析请求特征（增强版：集成AI Shell资源解析和对话历史）"""
        
        # 提取对话历史（如果存在）
        conversation_history = context.get('conversation_history', [])
        if conversation_history and len(conversation_history) > 0:
            logger.info(f"使用对话历史：{len(conversation_history)}条消息")
        
        # AI Shell集成：先进行资源解析，获取资源上下文
        resource_context = {}
        if self.resource_resolver:
            try:
                # 构建基础意图结果（用于资源解析）
                intent_dict = {
                    "intent": context.get("intent", "unknown"),
                    "user_input": user_input,
                    "suggested_activities": context.get("suggested_activities", []),
                    "extracted_entities": context.get("extracted_entities", {}),
                    "query_keywords": context.get("query_keywords", [])
                }
                
                # 使用AI Shell解析资源
                resolution_result = self.resource_resolver.resolve_intent_to_resources(intent_dict)
                
                # 将资源解析结果添加到上下文
                resource_context = {
                    "resolved_resources": {
                        "objects": [r.id for r in resolution_result.objects],
                        "systems": [r.id for r in resolution_result.systems],
                        "knowledge": [r.id for r in resolution_result.knowledge],
                        "workflows": [r.id for r in resolution_result.workflows],
                        "data_entities": [r.id for r in resolution_result.data_entities]
                    },
                    "resource_operations": [op.to_dict() for op in resolution_result.operations],
                    "resource_confidence": resolution_result.confidence
                }
                logger.info(f"AI Shell资源解析完成：{len(resolution_result.operations)}个操作，置信度={resolution_result.confidence:.2f}")
            except Exception as e:
                logger.warning(f"AI Shell资源解析失败: {e}，继续使用原有分析")
                resource_context = {}
        
        prompt = f"""
分析以下用户请求的特征：

用户请求: "{user_input}"
用户上下文: {json.dumps(context, ensure_ascii=False, indent=2)}
{f"资源上下文: {json.dumps(resource_context, ensure_ascii=False, indent=2)}" if resource_context else ""}

请分析：
1. **请求复杂度**：simple|medium|complex|instant
2. **请求类型**：data_query|analysis|report|content|tool_execution|knowledge|other
3. **数据需求**：需要什么数据？从哪里获取？
4. **处理类型**：real_time|batch|interactive
5. **输出要求**：格式、详细程度、交付方式
{f"6. **资源信息**：基于资源上下文，识别涉及的业务对象、系统端点、知识项、工作流和数据实体" if resource_context else ""}

返回JSON格式：
{{
    "complexity": "simple|medium|complex|instant",
    "request_type": "请求类型",
    "data_requirements": ["需求1", "需求2"],
    "processing_type": "real_time|batch|interactive",
    "output_requirements": {{
        "format": "格式要求",
        "detail_level": "详细程度",
        "delivery_method": "交付方式"
    }},
    "estimated_duration": "预计时间",
    "key_insights": ["洞察1", "洞察2"],
    {f'"resource_context": {json.dumps(resource_context, ensure_ascii=False)}' if resource_context else ''}
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from .prompt_utils import get_system_prompt
            analysis_system_prompt = get_system_prompt(
                "workflow_analysis",
                fallback="你是一个请求分析专家，擅长分析用户请求的特征。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": analysis_system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            
            # 降级：简单分析
            return {
                "complexity": "medium",
                "request_type": "other",
                "data_requirements": [],
                "processing_type": "real_time",
                "output_requirements": {},
                "estimated_duration": "5-10秒"
            }
            
        except Exception as e:
            logger.error(f"Request analysis failed: {e}", exc_info=True)
            return {
                "complexity": "medium",
                "request_type": "other",
                "error": str(e)
            }
    
    async def _design_network(
        self,
        user_input: str,
        context: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """设计智能体网络"""
        
        if not analysis:
            analysis = await self._analyze_request(user_input, context)
        
        agent_pool_desc = self._get_agent_pool_description()
        
        prompt = f"""
基于这个具体请求，设计最优的智能体执行路径：

用户请求: "{user_input}"
请求分析: {json.dumps(analysis, ensure_ascii=False, indent=2)}
用户上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

可用智能体池:
{agent_pool_desc}

请分析这个请求的特点，设计最合适的执行网络：

**考虑因素**：
1. **请求复杂度**：简单查询 vs 复杂分析 vs 内容创作
2. **数据需求**：需要什么数据？从哪里获取？
3. **处理类型**：实时响应 vs 批量处理 vs 交互式
4. **输出要求**：格式、详细程度、交付方式

**设计输出**：
- 需要哪些智能体？（从池中选择）
- 执行顺序和并行策略
- 智能体间的数据流和依赖关系
- 预期执行时间和资源分配

返回JSON格式：
{{
    "agents": [
        {{
            "id": "agent_1",
            "agent_type": "metadata_agent",
            "task": "任务描述",
            "input": {{"参数": "值"}},
            "dependencies": [],
            "output_key": "output_key"
        }}
    ],
    "execution_layers": [
        ["agent_1"],
        ["agent_2", "agent_3"],
        ["agent_4"]
    ],
    "estimated_duration": "预计时间",
    "complexity": "simple|medium|complex",
    "parallel_strategy": "full|partial|sequential"
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from .prompt_utils import get_system_prompt
            design_system_prompt = get_system_prompt(
                "workflow_design",
                fallback="你是一个智能体网络设计专家，擅长为任务设计最优的执行路径。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": design_system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    network_design = json.loads(response[json_start:json_end])
                else:
                    network_design = self._create_fallback_design(user_input, analysis)
            else:
                network_design = response
            
            # 验证和优化设计
            validated_design = await self._validate_design(network_design)
            
            return validated_design
            
        except Exception as e:
            logger.error(f"Network design failed: {e}", exc_info=True)
            return self._create_fallback_design(user_input, analysis)
    
    async def _validate_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """验证网络设计"""
        
        # 确保必要字段
        if "agents" not in design:
            design["agents"] = []
        if "execution_layers" not in design:
            design["execution_layers"] = []
        
        # 验证智能体ID唯一性
        agent_ids = [agent.get("id") for agent in design["agents"]]
        if len(agent_ids) != len(set(agent_ids)):
            logger.warning("Duplicate agent IDs found, fixing...")
            # 修复重复ID
            seen = set()
            for agent in design["agents"]:
                original_id = agent.get("id")
                if original_id in seen:
                    agent["id"] = f"{original_id}_{len(seen)}"
                seen.add(agent["id"])
        
        # 验证依赖关系
        valid_agent_ids = set(agent["id"] for agent in design["agents"])
        for agent in design["agents"]:
            deps = agent.get("dependencies", [])
            invalid_deps = [dep for dep in deps if dep not in valid_agent_ids]
            if invalid_deps:
                logger.warning(f"Invalid dependencies {invalid_deps} for agent {agent.get('id')}")
                agent["dependencies"] = [dep for dep in deps if dep in valid_agent_ids]
        
        # 如果没有执行层，根据依赖关系生成
        if not design["execution_layers"]:
            design["execution_layers"] = self._generate_execution_layers(design["agents"])
        
        return design
    
    def _generate_execution_layers(self, agents: List[Dict[str, Any]]) -> List[List[str]]:
        """根据依赖关系生成执行层"""
        
        # 构建依赖图
        in_degree = {agent["id"]: 0 for agent in agents}
        graph = defaultdict(list)
        
        for agent in agents:
            for dep in agent.get("dependencies", []):
                if dep in in_degree:
                    graph[dep].append(agent["id"])
                    in_degree[agent["id"]] += 1
        
        # 拓扑排序
        layers = []
        queue = deque([agent_id for agent_id, degree in in_degree.items() if degree == 0])
        
        while queue:
            layer = []
            level_size = len(queue)
            
            for _ in range(level_size):
                agent_id = queue.popleft()
                layer.append(agent_id)
                
                for neighbor in graph[agent_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            if layer:
                layers.append(layer)
        
        return layers
    
    async def _validate_and_optimize(
        self,
        design: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证和优化设计"""
        
        # 基本验证
        validated = await self._validate_design(design)
        
        # 可以添加优化逻辑
        # 例如：合并可以并行的智能体、优化执行顺序等
        
        return validated
    
    def _get_agent_pool_description(self) -> str:
        """返回可用智能体池的描述"""
        desc = "智能体池:\n"
        
        categories = {
            "元数据类": ["metadata_agent"],
            "数据类": ["data_query_agent", "data_clean_agent", "data_enrich_agent"],
            "工具类": ["mcp_tool_agent", "workflow_agent"],
            "分析类": ["analysis_agent", "insight_agent", "validation_agent"],
            "内容类": ["content_agent", "format_agent", "mcp_tool_agent"]
        }
        
        for category, agent_types in categories.items():
            desc += f"\n├─ **{category}**\n"
            for agent_type in agent_types:
                agent_info = self.agent_pool.get(agent_type, {})
                desc += f"│  ├─ {agent_type}: {agent_info.get('description', '')}\n"
        
        return desc
    
    def _create_fallback_design(
        self,
        user_input: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建降级设计"""
        
        complexity = analysis.get("complexity", "medium")
        
        if complexity == "instant" or complexity == "simple":
            # 简单任务：直接使用内容智能体
            return {
                "agents": [
                    {
                        "id": "content_agent_1",
                        "agent_type": "content_agent",
                        "task": f"处理用户请求：{user_input}",
                        "input": {"task": user_input},
                        "dependencies": [],
                        "output_key": "result"
                    }
                ],
                "execution_layers": [["content_agent_1"]],
                "estimated_duration": "1-3秒",
                "complexity": "simple"
            }
        else:
            # 中等复杂度：使用元数据 + 工具/内容
            return {
                "agents": [
                    {
                        "id": "metadata_agent_1",
                        "agent_type": "metadata_agent",
                        "task": "提供业务上下文",
                        "input": {"task": user_input},
                        "dependencies": [],
                        "output_key": "business_context"
                    },
                    {
                        "id": "content_agent_1",
                        "agent_type": "content_agent",
                        "task": "生成响应内容",
                        "input": {"task": user_input},
                        "dependencies": ["metadata_agent_1"],
                        "output_key": "result"
                    }
                ],
                "execution_layers": [
                    ["metadata_agent_1"],
                    ["content_agent_1"]
                ],
                "estimated_duration": "3-5秒",
                "complexity": "medium"
            }

