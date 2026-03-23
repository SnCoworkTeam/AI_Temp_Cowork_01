"""
数据查询智能体
专门处理数据获取和查询优化
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class DataQueryAgent(IntelligentAgent):
    """数据查询智能体 - 专门处理数据获取和查询优化"""
    
    def __init__(self, mcp_tool_agent=None, sap_odata_agent=None):
        """
        初始化数据查询智能体
        
        Args:
            mcp_tool_agent: MCP工具智能体（用于非SAP查询）
            sap_odata_agent: SAP OData智能体（用于SAP查询）
        """
        super().__init__(
            agent_id="data_query_agent",
            name="数据查询智能体",
            description="专门处理数据获取和查询优化，包括查询规划、参数优化、结果格式化",
            capabilities={
                "data_acquisition": "数据获取",
                "query_optimization": "查询优化",
                "result_formatting": "结果格式化"
            }
        )
        self.mcp_tool_agent = mcp_tool_agent
        self.sap_odata_agent = sap_odata_agent
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析数据查询需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            查询计划
        """
        try:
            # 检查是否有元数据智能体的结果
            metadata_result = None
            for key in context.keys():
                if key.endswith("_result") and "metadata" in key.lower():
                    metadata_result = context[key]
                    break
            
            metadata_context = ""
            has_data_source_hint = context.get("_has_data_source", False)
            detected_data_source_hint = context.get("_detected_data_source")
            
            if metadata_result:
                enhancements = metadata_result.get("enhancements_provided", {})
                business_entities = enhancements.get("business_entities", [])
                data_sources = enhancements.get("data_sources", [])
                
                if business_entities or data_sources:
                    metadata_context = f"""
元数据信息：
- 业务实体: {json.dumps([e.get('name', '') for e in business_entities[:3]], ensure_ascii=False)}
- 数据源: {json.dumps([s.get('name', '') for s in data_sources[:3]], ensure_ascii=False)}
- 数据源详情: {json.dumps([{"name": s.get("name", ""), "asset_type": s.get("asset_type", ""), "display_name": s.get("display_name", "")} for s in data_sources[:3]], ensure_ascii=False, indent=2) if data_sources else '无'}
- 业务实体详情: {json.dumps(business_entities[:2], ensure_ascii=False, indent=2) if business_entities else '无'}

**重要提示**：如果元数据信息中提供了数据源（data_sources），则必须返回 "needs_data_query": true，因为数据源的存在意味着需要执行数据查询。
"""
            
            # 如果有数据源提示，在 prompt 中明确说明
            data_source_instruction = ""
            if has_data_source_hint:
                data_source_instruction = f"\n**关键要求**：检测到数据源（{detected_data_source_hint}），必须返回 \"needs_data_query\": true。"
            
            prompt = f"""
作为数据查询专家，分析以下数据查询需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}
{metadata_context}{data_source_instruction}

请分析：
1. **数据源识别**：需要从哪个数据源获取数据？
2. **查询类型**：是SAP查询、数据库查询还是其他？
3. **查询参数**：需要什么查询条件？
4. **结果要求**：需要多少数据？需要什么格式？

**重要规则**：
- 如果元数据信息中提供了数据源（data_sources），则必须返回 "needs_data_query": true
- 如果任务描述明确要求查询数据（如"查询"、"获取"、"显示"等），则必须返回 "needs_data_query": true
- 只有在明确不需要数据查询的情况下（如纯分析、纯格式化等），才返回 "needs_data_query": false

返回JSON格式：
{{
    "needs_data_query": true/false,
    "data_source": "sap|database|api|enterprise_architecture|other",
    "query_type": "查询类型",
    "query_parameters": {{"参数名": "参数值"}},
    "result_requirements": {{
        "limit": 数字,
        "format": "格式要求",
        "fields": ["字段1", "字段2"]
    }},
    "optimization_suggestions": ["建议1", "建议2"]
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "data_query_agent",
                fallback="你是一个数据查询专家，擅长分析数据查询需求并优化查询。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    query_plan = json.loads(response[json_start:json_end])
                else:
                    query_plan = {"needs_data_query": False}
            else:
                query_plan = response
            
            return query_plan
            
        except Exception as e:
            logger.error(f"Data query analysis failed: {e}", exc_info=True)
            return {
                "needs_data_query": False,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据查询
        
        Args:
            input_data: 输入数据（包含task或query_plan）
            context: 上下文信息
            
        Returns:
            查询结果
        """
        try:
            task_description = input_data.get("task", "")
            query_plan = input_data.get("query_plan")
            
            # 检查是否有元数据智能体的结果（从input_data和context中获取）
            metadata_result = None
            
            # 首先从input_data中查找（依赖结果会在这里）
            for key in input_data.keys():
                if key.endswith("_result") and "metadata" in key.lower():
                    metadata_result = input_data[key]
                    break
            
            # 如果input_data中没有，再从context中查找
            if not metadata_result:
                for key in context.keys():
                    if key.endswith("_result") and "metadata" in key.lower():
                        metadata_result = context[key]
                        break
            
            # **关键修复：先检查 metadata_result，确定是否需要查询，再调用 analyze_task**
            # 这样可以避免 LLM 错误地返回 needs_data_query: False
            has_data_source = False
            detected_data_source = None
            
            if metadata_result:
                enhancements = metadata_result.get("enhancements_provided", {})
                business_entities = enhancements.get("business_entities", [])
                data_sources = enhancements.get("data_sources", [])
                
                # 检查是否有数据源
                if data_sources:
                    has_data_source = True
                    first_source = data_sources[0]
                    detected_data_source = first_source.get("asset_type", "sap")
                    logger.info(f"Found data source from metadata: {detected_data_source}")
                
                # 检查是否有业务实体（可能包含SAP表名）
                if business_entities:
                    for entity in business_entities:
                        sap_table = entity.get("metadata", {}).get("sap_table_name") or entity.get("sap_table_name")
                        if sap_table:
                            has_data_source = True
                            detected_data_source = "sap"
                            logger.info(f"Found SAP table from metadata: {sap_table}")
                            break
            
            # 如果没有query_plan，调用 analyze_task 获取查询计划
            # 但如果有数据源，告诉 LLM 必须返回 needs_data_query: True
            if not query_plan:
                # 如果有数据源，在 context 中添加标记，让 analyze_task 知道必须查询
                analysis_context = context.copy()
                if has_data_source:
                    analysis_context["_has_data_source"] = True
                    analysis_context["_detected_data_source"] = detected_data_source
                
                query_plan = await self.analyze_task(task_description, analysis_context)
            
            # 如果元数据智能体提供了业务实体或数据源信息，使用它们
            if metadata_result:
                enhancements = metadata_result.get("enhancements_provided", {})
                business_entities = enhancements.get("business_entities", [])
                data_sources = enhancements.get("data_sources", [])
                
                # 如果有数据源，强制设置 needs_data_query = True（这是核心逻辑）
                if data_sources:
                    query_plan["needs_data_query"] = True
                    if not query_plan.get("data_source"):
                        first_source = data_sources[0]
                        source_type = first_source.get("asset_type", "sap")
                        query_plan["data_source"] = source_type
                        logger.info(f"Using data source from metadata: {source_type}, forcing needs_data_query = True")
                
                # 如果有业务实体，提取SAP表名等信息
                if business_entities:
                    for entity in business_entities:
                        # 检查是否有SAP表名
                        sap_table = entity.get("metadata", {}).get("sap_table_name") or entity.get("sap_table_name")
                        if sap_table:
                            if "query_parameters" not in query_plan:
                                query_plan["query_parameters"] = {}
                            query_plan["query_parameters"]["table"] = sap_table
                            query_plan["data_source"] = "sap"
                            query_plan["needs_data_query"] = True
                            logger.info(f"Using SAP table from metadata: {sap_table}, forcing needs_data_query = True")
            
            # 如果任务描述中包含组织架构相关关键词，也强制设置 needs_data_query = True
            org_keywords = ["组织架构", "organization", "org", "部门", "员工", "组织"]
            if any(keyword in task_description.lower() for keyword in org_keywords):
                if not query_plan.get("needs_data_query"):
                    query_plan["needs_data_query"] = True
                    if not query_plan.get("data_source"):
                        query_plan["data_source"] = "enterprise_architecture"
                    logger.info("Detected organization-related keywords in task, forcing needs_data_query = True")
            
            if not query_plan.get("needs_data_query"):
                return {
                    "agent_type": "data_query",
                    "execution_success": False,
                    "decision": "no_query_needed",
                    "reason": query_plan.get("reason", "Task does not require data query"),
                    "error": "任务不需要数据查询"
                }
            
            # 根据数据源选择智能体
            data_source = query_plan.get("data_source", "sap")
            query_params = query_plan.get("query_parameters", {})
            
            # SAP查询：直接使用sap_odata_agent
            if data_source == "sap":
                # 如果没有sap_odata_agent，创建一个
                if not self.sap_odata_agent:
                    from .sap_odata_agent import SAPODataAgent
                    self.sap_odata_agent = SAPODataAgent()
                
                # 构建SAP查询任务
                sap_task = task_description or f"查询SAP数据"
                if query_params.get("table"):
                    sap_task += f"，表：{query_params.get('table')}"
                
                # 构建sap_odata_agent的执行计划
                sap_execution_plan = {
                    "needs_sap_operation": True,
                    "operation_type": "query",
                    "parameters": {
                        "entity_name": query_params.get("table", ""),
                        "query": query_params.get("query", ""),
                        "$top": query_params.get("limit", 100)
                    }
                }
                
                # 如果有表名，尝试查找对应的工具
                if query_params.get("table"):
                    sap_execution_plan["entity_name"] = query_params.get("table")
                
                # 执行SAP查询
                sap_result = await self.sap_odata_agent.execute({
                    "task": sap_task,
                    "execution_plan": sap_execution_plan
                }, context)
                
                if not sap_result.get("execution_success", False):
                    return {
                        "agent_type": "data_query",
                        "execution_success": False,
                        "error": sap_result.get("error", "SAP query execution failed"),
                        "sap_result": sap_result
                    }
                
                # 提取SAP查询结果
                raw_result = sap_result.get("result") or sap_result.get("data") or sap_result
                
                # 格式化结果
                formatted_result = await self._format_query_result(
                    raw_result,
                    query_plan.get("result_requirements", {}),
                    context
                )
                
                return {
                    "agent_type": "data_query",
                    "execution_success": True,
                    "data_source": "sap",
                    "query_type": query_plan.get("query_type"),
                    "raw_result": raw_result,
                    "formatted_result": formatted_result,
                    "query_plan": query_plan,
                    "sap_result": sap_result
                }
            
            # 非SAP查询：根据数据源类型选择查询方式
            else:
                # 组织架构查询：直接调用metadata-service API
                if data_source in ["organization", "org", "组织架构", "enterprise_architecture"] or \
                   "组织架构" in task_description or "organization" in task_description.lower():
                    try:
                        import httpx
                        import os
                        
                        metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
                        
                        # 调用metadata-service的组织架构API
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            # 查询所有组织单元
                            response = await client.get(
                                f"{metadata_service_url}/api/enterprise-architecture/organizations",
                                params={
                                    "skip": query_params.get("skip", 0),
                                    "limit": query_params.get("limit", 1000)
                                }
                            )
                            
                            if response.status_code == 200:
                                org_data = response.json()
                                raw_result = org_data.get("organizations", []) if isinstance(org_data, dict) else org_data
                                
                                # 格式化结果
                                formatted_result = await self._format_query_result(
                                    raw_result,
                                    query_plan.get("result_requirements", {}),
                                    context
                                )
                                
                                return {
                                    "agent_type": "data_query",
                                    "execution_success": True,
                                    "data_source": "organization",
                                    "query_type": "organization_architecture",
                                    "raw_result": raw_result,
                                    "formatted_result": formatted_result,
                                    "query_plan": query_plan
                                }
                            else:
                                logger.error(f"Failed to query organization architecture: {response.status_code} - {response.text}")
                                return {
                                    "agent_type": "data_query",
                                    "execution_success": False,
                                    "error": f"Failed to query organization architecture: HTTP {response.status_code}"
                                }
                    except Exception as e:
                        logger.error(f"Error querying organization architecture: {e}", exc_info=True)
                        return {
                            "agent_type": "data_query",
                            "execution_success": False,
                            "error": f"Error querying organization architecture: {str(e)}"
                        }
                
                # 其他数据源：尝试使用MCP工具（如果存在）
                else:
                    # 如果没有MCP工具智能体，创建一个
                    if not self.mcp_tool_agent:
                        from .mcp_tool_agent import MCPToolAgent
                        self.mcp_tool_agent = MCPToolAgent()
                    
                    # 尝试查找合适的工具（不再硬编码tool_name）
                    # 让MCP工具智能体自己选择工具
                    tool_result = await self.mcp_tool_agent.execute({
                        "task": f"执行{data_source}数据查询",
                        "execution_plan": {
                            "needs_tool": True,
                            "task_description": task_description,
                            "query_parameters": query_params
                        }
                    }, context)
                    
                    if not tool_result.get("execution_success"):
                        return {
                            "agent_type": "data_query",
                            "execution_success": False,
                            "error": tool_result.get("error", "Query execution failed")
                        }
                    
                    # 格式化结果
                    raw_result = tool_result.get("raw_result") or tool_result.get("understood_result", {})
                    formatted_result = await self._format_query_result(
                        raw_result,
                        query_plan.get("result_requirements", {}),
                        context
                    )
                    
                    return {
                        "agent_type": "data_query",
                        "execution_success": True,
                        "data_source": data_source,
                        "query_type": query_plan.get("query_type"),
                        "raw_result": raw_result,
                        "formatted_result": formatted_result,
                        "query_plan": query_plan
                    }
            
        except Exception as e:
            logger.error(f"Data query agent execution failed: {e}", exc_info=True)
            raise
    
    async def _format_query_result(
        self,
        raw_result: Any,
        requirements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """格式化查询结果"""
        try:
            # 如果结果已经是格式化好的，直接返回
            if isinstance(raw_result, dict) and "formatted" in raw_result:
                return raw_result
            
            # 使用LLM格式化结果
            prompt = f"""
格式化以下数据查询结果：

原始结果: {json.dumps(raw_result, ensure_ascii=False, indent=2)}
格式要求: {json.dumps(requirements, ensure_ascii=False, indent=2)}

请格式化结果，包括：
1. **数据摘要**：总记录数、关键统计
2. **数据列表**：格式化后的数据列表
3. **关键字段**：突出显示重要字段

返回JSON格式：
{{
    "summary": {{
        "total_count": 数字,
        "key_statistics": {{"统计项": "值"}}
    }},
    "data": [
        {{"字段1": "值1", "字段2": "值2"}}
    ],
    "formatted_text": "格式化的文本描述"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            format_system_prompt = get_system_prompt(
                "data_query_agent_format",
                fallback="你是一个数据格式化专家，擅长格式化数据查询结果。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": format_system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            
            # 降级：简单格式化
            return {
                "summary": {"total_count": len(raw_result) if isinstance(raw_result, list) else 1},
                "data": raw_result if isinstance(raw_result, list) else [raw_result],
                "formatted_text": json.dumps(raw_result, ensure_ascii=False, indent=2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to format query result: {e}")
            return {
                "summary": {"total_count": 0},
                "data": [],
                "formatted_text": str(raw_result)
            }


