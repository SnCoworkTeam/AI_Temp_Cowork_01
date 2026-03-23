"""
结果合成智能体
专门协调所有智能体输出，合成最终结果
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class ResultSynthesisAgent(IntelligentAgent):
    """结果合成智能体 - 专门协调所有智能体输出，合成最终结果"""
    
    def __init__(self):
        super().__init__(
            agent_id="result_synthesis_agent",
            name="结果合成智能体",
            description="专门协调所有智能体输出，合成最终结果，包括结果整合、冲突解决、优先级排序",
            capabilities={
                "result_synthesis": "结果合成",
                "conflict_resolution": "冲突解决",
                "priority_ranking": "优先级排序"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析结果合成需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            合成计划
        """
        try:
            prompt = f"""
作为结果合成专家，分析以下结果合成需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **合成类型**：结果整合、冲突解决、优先级排序等
2. **合成策略**：如何合成最有效？
3. **优先级规则**：如何确定优先级？
4. **输出格式**：最终输出应该是什么格式？

返回JSON格式：
{{
    "needs_synthesis": true/false,
    "synthesis_types": ["结果整合", "冲突解决"],
    "synthesis_strategy": "合成策略描述",
    "priority_rules": ["规则1", "规则2"],
    "output_format": "输出格式要求"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "result_synthesis_agent",
                fallback="你是一个结果合成专家，擅长分析结果合成需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    synthesis_plan = json.loads(response[json_start:json_end])
                else:
                    synthesis_plan = {"needs_synthesis": True}
            else:
                synthesis_plan = response
            
            return synthesis_plan
            
        except Exception as e:
            logger.error(f"Result synthesis planning failed: {e}", exc_info=True)
            return {
                "needs_synthesis": True,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行结果合成
        
        Args:
            input_data: 输入数据（包含agent_results或synthesis_plan）
            context: 上下文信息
            
        Returns:
            合成后的最终结果
        """
        try:
            # 获取所有智能体的结果
            agent_results = input_data.get("agent_results") or {}
            user_input = context.get("user_input", input_data.get("task", ""))
            synthesis_plan = input_data.get("synthesis_plan")
            
            logger.info(f"[ResultSynthesisAgent] Starting synthesis with {len(agent_results)} agent results")
            logger.info(f"[ResultSynthesisAgent] Agent IDs: {list(agent_results.keys())}")
            
            if not agent_results:
                logger.warning("[ResultSynthesisAgent] No agent results provided")
                # 如果没有结果，先分析任务
                task_description = input_data.get("task", user_input)
                synthesis_plan = await self.analyze_task(task_description, context)
                
                return {
                    "agent_type": "result_synthesis",
                    "decision": "results_required",
                    "synthesis_plan": synthesis_plan,
                    "message": "需要先执行其他智能体才能合成结果",
                    "execution_success": False
                }
            
            # 执行合成
            final_result = await self._synthesize_results(
                agent_results,
                user_input,
                synthesis_plan,
                context
            )
            
            logger.info(f"[ResultSynthesisAgent] Synthesis completed: has_formatted_output={'formatted_output' in final_result}, "
                       f"formatted_output_length={len(str(final_result.get('formatted_output', '')))}")
            
            return {
                "agent_type": "result_synthesis",
                "execution_success": True,
                "final_result": final_result,
                "synthesis_summary": final_result.get("synthesis_summary", {}),
                "synthesis_plan": synthesis_plan
            }
            
        except Exception as e:
            logger.error(f"Result synthesis agent execution failed: {e}", exc_info=True)
            raise
    
    async def _synthesize_results(
        self,
        agent_results: Dict[str, Any],
        user_input: str,
        synthesis_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的结果合成"""
        
        # 预处理 agent_results，提取 format_agent 的 formatted_text
        # 同时处理StandardResult对象，提取真实的agent_type
        processed_agent_results = {}
        from ..agents.protocols import StandardResult
        
        for agent_id, result in agent_results.items():
            # 处理StandardResult对象
            if isinstance(result, StandardResult):
                actual_output = result.output
                # 从output中提取真实的agent_type
                if isinstance(actual_output, dict):
                    real_agent_type = actual_output.get("agent_type")
                    # 如果output是嵌套的result结构，继续提取
                    if "result" in actual_output and not real_agent_type:
                        nested_result = actual_output["result"]
                        if isinstance(nested_result, dict):
                            real_agent_type = nested_result.get("agent_type")
                            actual_output = nested_result
                    
                    # 转换为字典格式，保留真实的agent_type
                    processed_agent_results[agent_id] = {
                        "agent_type": real_agent_type if real_agent_type and real_agent_type != "standardized" else "unknown",
                        "execution_success": result.success,
                        "result": actual_output,
                        "confidence": result.confidence,
                        "quality_score": result.quality_score
                    }
                else:
                    processed_agent_results[agent_id] = {
                        "agent_type": "unknown",
                        "execution_success": result.success,
                        "result": actual_output
                    }
            elif isinstance(result, dict) and result.get("agent_type") == "format":
                formatted_content = result.get("formatted_content", {})
                if isinstance(formatted_content, dict):
                    formatted_text = formatted_content.get("formatted_text")
                    if formatted_text:
                        # 将格式化的文本作为主要内容，方便 LLM 处理
                        processed_agent_results[agent_id] = {
                            **result,
                            "formatted_text": formatted_text,
                            "main_content": formatted_text,
                            "extracted_content": formatted_text  # 明确标记已提取的内容
                        }
                    else:
                        processed_agent_results[agent_id] = result
                else:
                    processed_agent_results[agent_id] = result
            else:
                processed_agent_results[agent_id] = result
        
        # 准备结果摘要
        results_summary = self._summarize_results(processed_agent_results)
        
        # 提取关键信息用于提示词
        key_info = {}
        for agent_id, result in processed_agent_results.items():
            if isinstance(result, dict):
                actual_result = result.get("result", result)
                agent_type = result.get("agent_type", "unknown")
                
                # 提取格式化文本
                formatted_text = None
                if "formatted_text" in result:
                    formatted_text = result["formatted_text"]
                elif isinstance(actual_result, dict):
                    formatted_result = actual_result.get("formatted_result", {})
                    if isinstance(formatted_result, dict):
                        formatted_text = formatted_result.get("formatted_text")
                
                if formatted_text and not isinstance(formatted_text, dict):
                    key_info[agent_id] = {
                        "agent_type": agent_type,
                        "formatted_text": formatted_text[:500]  # 限制长度
                    }
                elif isinstance(actual_result, dict):
                    # 提取摘要信息
                    summary_info = {}
                    if "formatted_result" in actual_result:
                        fr = actual_result["formatted_result"]
                        if isinstance(fr, dict):
                            summary = fr.get("summary", {})
                            if isinstance(summary, dict):
                                summary_info["total_count"] = summary.get("total_count")
                                summary_info["key_statistics"] = summary.get("key_statistics", {})
                    key_info[agent_id] = {
                        "agent_type": agent_type,
                        "summary": summary_info
                    }
        
        prompt = f"""
作为结果合成专家，协调以下所有智能体的输出，合成最终结果：

用户原始请求: "{user_input}"
智能体结果摘要: {json.dumps(results_summary, ensure_ascii=False, indent=2)}
合成策略: {synthesis_plan.get('synthesis_strategy', '') if synthesis_plan else '智能整合所有结果'}
优先级规则: {json.dumps(synthesis_plan.get('priority_rules', []), ensure_ascii=False) if synthesis_plan else []}
输出格式要求: {synthesis_plan.get('output_format', '') if synthesis_plan else ''}

关键信息摘要: {json.dumps(key_info, ensure_ascii=False, indent=2)}

请进行结果合成，生成**适合向领导汇报的、美观易读的纯Markdown格式报告**（**重要：只使用Markdown语法，不要包含任何HTML标签**），包括：
1. **结果整合**：整合所有智能体的输出，避免显示原始JSON代码
2. **冲突解决**：解决不同智能体输出之间的冲突
3. **格式要求**：使用纯Markdown语法（如 **粗体**、## 标题、- 列表等），**绝对不要使用HTML标签**（如<span>、<div>、<strong>等）
3. **优先级排序**：根据重要性排序信息
4. **内容优化**：优化最终输出的内容和结构，使用清晰的标题、列表、表格等
5. **格式统一**：统一输出格式，使用Markdown语法美化展示

**重要要求**：
        - formatted_output必须是美观的Markdown格式，不要包含JSON代码块或原始字典格式（如 `key: value`）
- 组织架构数据应显示为树形结构，使用缩进和图标，每个组织显示名称、代码和描述
- 数据源列表应显示为清晰的列表，不要显示原始JSON
- 统计信息应突出显示，使用表格或列表，字典格式应转换为文本（如 `集团: 1, 部门: 2`）
- 所有字典和对象数据都应转换为易读的文本格式，不要直接显示原始JSON
- 内容要简洁明了，适合向领导汇报

返回JSON格式：
{{
    "synthesized_result": {{
        "title": "结果标题",
        "summary": "执行摘要（1-2句话）",
        "main_content": "主要内容（Markdown格式，不要包含JSON代码）",
        "key_findings": ["发现1", "发现2"],
        "recommendations": ["建议1", "建议2"]
    }},
    "formatted_output": "格式化的最终输出文本（Markdown格式，美观易读，适合向领导汇报，不要包含JSON代码块）",
    "synthesis_summary": {{
        "agents_used": ["智能体1", "智能体2"],
        "results_integrated": 整合的结果数量,
        "conflicts_resolved": 解决的冲突数量,
        "priority_ranked": true/false
    }}
}}
"""
        
        try:
            # 添加超时保护，避免LLM调用时间过长
            response = await asyncio.wait_for(
                self.llm.chat([
                    {"role": "system", "content": get_system_prompt(
                        "result_synthesis_agent_execute",
                        fallback="你是一个专业的结果合成专家，擅长协调多个智能体的输出并合成高质量的最终结果。"
                    )},
                    {"role": "user", "content": prompt}
                ]),
                timeout=60.0  # 60秒超时
            )
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    parsed_result = json.loads(response[json_start:json_end])
                    # 清理formatted_output：移除JSON代码块和HTML标签
                    if "formatted_output" in parsed_result:
                        formatted_output = parsed_result["formatted_output"]
                        if isinstance(formatted_output, str):
                            # 移除JSON代码块
                            if "```json" in formatted_output.lower():
                                formatted_output = formatted_output.replace("```json", "").replace("```", "").strip()
                            
                            # 移除所有HTML标签，只保留纯Markdown
                            import re
                            formatted_output = re.sub(r'<[^>]+>', '', formatted_output)
                            formatted_output = re.sub(r'\n\s*\n\s*\n', '\n\n', formatted_output)
                            formatted_output = formatted_output.strip()
                            
                            parsed_result["formatted_output"] = formatted_output
                    
                    # 同样清理main_content
                    if "synthesized_result" in parsed_result:
                        synthesized = parsed_result["synthesized_result"]
                        if isinstance(synthesized, dict) and "main_content" in synthesized:
                            main_content = synthesized["main_content"]
                            if isinstance(main_content, str):
                                import re
                                main_content = re.sub(r'<[^>]+>', '', main_content)
                                main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
                                main_content = main_content.strip()
                                synthesized["main_content"] = main_content
                    
                    return parsed_result
                else:
                    # 如果没有JSON，尝试提取文本并清理HTML标签
                    import re
                    cleaned_response = re.sub(r'<[^>]+>', '', response)
                    cleaned_response = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_response)
                    cleaned_response = cleaned_response.strip()
                    
                    return {
                        "synthesized_result": {
                            "title": "执行结果",
                            "summary": cleaned_response[:500],
                            "main_content": cleaned_response
                        },
                        "formatted_output": cleaned_response,
                        "synthesis_summary": {
                            "agents_used": list(agent_results.keys()),
                            "results_integrated": len(agent_results)
                        }
                    }
            else:
                result = response
                # 清理formatted_output：移除JSON代码块和HTML标签
                if isinstance(result, dict) and "formatted_output" in result:
                    formatted_output = result["formatted_output"]
                    if isinstance(formatted_output, str):
                        # 移除JSON代码块
                        if "```json" in formatted_output.lower():
                            formatted_output = formatted_output.replace("```json", "").replace("```", "").strip()
                        
                        # 移除所有HTML标签，只保留纯Markdown
                        import re
                        # 移除HTML标签，但保留内容
                        formatted_output = re.sub(r'<[^>]+>', '', formatted_output)
                        # 清理多余的空白
                        formatted_output = re.sub(r'\n\s*\n\s*\n', '\n\n', formatted_output)
                        formatted_output = formatted_output.strip()
                        
                        result["formatted_output"] = formatted_output
                
                # 同样清理main_content
                if isinstance(result, dict) and "synthesized_result" in result:
                    synthesized = result["synthesized_result"]
                    if isinstance(synthesized, dict) and "main_content" in synthesized:
                        main_content = synthesized["main_content"]
                        if isinstance(main_content, str):
                            import re
                            # 移除HTML标签
                            main_content = re.sub(r'<[^>]+>', '', main_content)
                            # 清理多余的空白
                            main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
                            main_content = main_content.strip()
                            synthesized["main_content"] = main_content
                
                return result
            
        except Exception as e:
            logger.warning(f"LLM result synthesis failed: {e}")
            # 降级：智能格式化，转换为友好的Markdown格式
            fallback_output = self._format_results_as_markdown(processed_agent_results, user_input)
            
            # 清理fallback输出中的HTML标签（如果有）
            import re
            if isinstance(fallback_output, str):
                fallback_output = re.sub(r'<[^>]+>', '', fallback_output)
                fallback_output = re.sub(r'\n\s*\n\s*\n', '\n\n', fallback_output)
                fallback_output = fallback_output.strip()
            
            return {
                "synthesized_result": {
                    "title": "执行结果",
                    "summary": "已整合所有智能体的输出",
                    "main_content": fallback_output
                },
                "formatted_output": fallback_output,
                "synthesis_summary": {
                    "agents_used": list(processed_agent_results.keys()),
                    "results_integrated": len(processed_agent_results)
                }
            }
    
    def _format_results_as_markdown(
        self,
        agent_results: Dict[str, Any],
        user_input: str
    ) -> str:
        """将智能体结果格式化为友好的Markdown格式"""
        lines = []
        lines.append(f"# 📊 查询结果\n")
        lines.append(f"**查询内容**: {user_input}\n")
        
        # 按智能体类型分组处理
        for agent_id, result in agent_results.items():
            # 处理StandardResult对象
            from ..agents.protocols import StandardResult
            if isinstance(result, StandardResult):
                actual_result = result.output
                agent_type = None
                success = result.success
                
                # 从output中提取agent_type
                if isinstance(actual_result, dict):
                    agent_type = actual_result.get("agent_type")
                    # 如果output是嵌套的result结构，继续提取
                    if "result" in actual_result:
                        actual_result = actual_result["result"]
                        if isinstance(actual_result, dict) and not agent_type:
                            agent_type = actual_result.get("agent_type")
            elif isinstance(result, dict):
                # 提取实际结果
                actual_result = result.get("result", result)
                agent_type = result.get("agent_type", "unknown")
                success = result.get("execution_success", result.get("success", True))
            else:
                continue
            
            # 如果actual_result是dict，尝试从其中提取agent_type
            if isinstance(actual_result, dict) and not agent_type:
                agent_type = actual_result.get("agent_type", "unknown")
            
            # 如果agent_type是"standardized"，尝试从实际结果中提取真实类型
            if agent_type == "standardized" and isinstance(actual_result, dict):
                agent_type = actual_result.get("agent_type", "unknown")
            
            # 如果还是unknown，尝试从agent_id推断
            if agent_type == "unknown" or agent_type == "standardized":
                if "metadata" in agent_id or "agent_1" in agent_id:
                    agent_type = "metadata"
                elif "data_query" in agent_id or "query" in agent_id or "agent_2" in agent_id:
                    agent_type = "data_query"
                elif "format" in agent_id or "agent_4" in agent_id:
                    agent_type = "format"
                elif "clean" in agent_id or "agent_3" in agent_id:
                    agent_type = "data_clean"
            
            # 优先使用已格式化的内容（从StandardResult或dict中提取）
            formatted_text = None
            if isinstance(result, StandardResult):
                if isinstance(actual_result, dict):
                    formatted_text = actual_result.get("formatted_text") or actual_result.get("formatted_output")
            elif isinstance(result, dict):
                formatted_text = result.get("formatted_text")
            
            if formatted_text and not isinstance(formatted_text, dict):
                lines.append(f"## {self._get_agent_display_name(agent_type)}\n")
                lines.append(f"{formatted_text}\n")
                continue
            
            # 根据智能体类型进行特殊处理
            if agent_type == "data_query":
                lines.extend(self._format_data_query_result(actual_result))
            elif agent_type == "metadata":
                lines.extend(self._format_metadata_result(actual_result))
            elif agent_type == "format":
                formatted_content = actual_result.get("formatted_content", {})
                if isinstance(formatted_content, dict):
                    formatted_text = formatted_content.get("formatted_text")
                    if formatted_text:
                        lines.append(f"## 📝 格式化结果\n")
                        lines.append(f"{formatted_text}\n")
            elif agent_type == "data_clean":
                # 数据清洗智能体的特殊处理
                lines.append(f"## {self._get_agent_display_name(agent_type)}\n")
                if success:
                    lines.append("✅ **执行成功**\n")
                    # 提取清洗结果
                    if isinstance(actual_result, dict):
                        cleaned_data = actual_result.get("cleaned_data")
                        cleaning_summary = actual_result.get("cleaning_summary", {})
                        if cleaning_summary:
                            lines.append("### 清洗摘要\n")
                            if isinstance(cleaning_summary, dict):
                                for key, value in cleaning_summary.items():
                                    if isinstance(value, (dict, list)):
                                        value_str = json.dumps(value, ensure_ascii=False, indent=2)
                                        lines.append(f"- **{key}**: {value_str}\n")
                                    else:
                                        lines.append(f"- **{key}**: {value}\n")
                else:
                    # 失败情况：格式化错误信息
                    error_msg = actual_result.get('error', '未知错误')
                    message = actual_result.get('message', '')
                    decision = actual_result.get('decision', '')
                    
                    if decision == "data_required":
                        lines.append("⚠️ **数据清洗未执行**\n\n")
                        lines.append(f"**原因**：{message or error_msg}\n\n")
                        lines.append("**说明**：数据清洗智能体需要先获取数据才能执行。请确保数据查询步骤已成功完成。\n")
                    else:
                        lines.append(f"❌ **执行失败**: {error_msg}\n")
                        if message:
                            lines.append(f"\n**详细信息**：{message}\n")
                    
                    # 如果有清洗计划，显示计划信息
                    cleaning_plan = actual_result.get('cleaning_plan')
                    if cleaning_plan and isinstance(cleaning_plan, dict):
                        if cleaning_plan.get('needs_cleaning'):
                            lines.append("\n### 清洗计划\n")
                            cleaning_types = cleaning_plan.get('cleaning_types', [])
                            if cleaning_types:
                                lines.append("**清洗类型**：\n")
                                for ct in cleaning_types:
                                    lines.append(f"- {ct}\n")
            else:
                # 通用格式化
                lines.append(f"## {self._get_agent_display_name(agent_type)}\n")
                if success:
                    lines.append("✅ **执行成功**\n")
                else:
                    # 格式化错误信息，避免显示原始字典
                    error_msg = actual_result.get('error', '未知错误')
                    message = actual_result.get('message', '')
                    decision = actual_result.get('decision', '')
                    
                    if decision:
                        lines.append(f"⚠️ **执行状态**: {decision}\n")
                    else:
                        lines.append(f"❌ **执行失败**: {error_msg}\n")
                    
                    if message and message != error_msg:
                        lines.append(f"\n**详细信息**：{message}\n")
                
                # 提取关键信息
                if isinstance(actual_result, dict):
                    if "formatted_result" in actual_result:
                        formatted_result = actual_result["formatted_result"]
                        if isinstance(formatted_result, dict):
                            if "formatted_text" in formatted_result:
                                lines.append(f"{formatted_result['formatted_text']}\n")
                            elif "summary" in formatted_result:
                                summary = formatted_result.get("summary", {})
                                if isinstance(summary, dict):
                                    lines.append(f"## {self._get_agent_display_name(agent_type)}\n")
                                    total_count = summary.get("total_count", 0)
                                    if total_count > 0:
                                        lines.append(f"**查询结果**: 共找到 **{total_count}** 条记录\n")
                                    
                                    key_stats = summary.get("key_statistics", {})
                                    if isinstance(key_stats, dict) and key_stats:
                                        lines.append("### 📊 关键统计\n")
                                        for key, value in key_stats.items():
                                            # 如果值是字典，格式化为友好的文本
                                            if isinstance(value, dict):
                                                value_str = ", ".join([f"{k}: {v}" for k, v in value.items()])
                                                lines.append(f"- **{key}**: {value_str}\n")
                                            elif isinstance(value, list):
                                                value_str = ", ".join([str(v) for v in value])
                                                lines.append(f"- **{key}**: {value_str}\n")
                                            else:
                                                lines.append(f"- **{key}**: {value}\n")
                                    
                                    # 显示数据（如果有）
                                    data = formatted_result.get("data", [])
                                    if data and isinstance(data, list) and len(data) > 0:
                                        lines.append("### 📋 数据详情\n")
                                        # 显示前几条数据
                                        for item in data[:5]:
                                            if isinstance(item, dict):
                                                # 提取关键字段
                                                name = item.get("部门名称") or item.get("name") or item.get("display_name", "未知")
                                                lines.append(f"- **{name}**\n")
                                        if len(data) > 5:
                                            lines.append(f"\n*还有 {len(data) - 5} 条记录未显示*\n")
                                    continue
        
        return "\n".join(lines)
    
    def _format_data_query_result(self, result: Dict[str, Any]) -> List[str]:
        """格式化数据查询结果"""
        lines = []
        lines.append("## 📋 组织架构查询结果\n")
        
        if isinstance(result, dict):
            formatted_result = result.get("formatted_result", {})
            if isinstance(formatted_result, dict):
                # 显示摘要
                summary = formatted_result.get("summary", {})
                if isinstance(summary, dict):
                    total_count = summary.get("total_count", 0)
                    lines.append(f"**查询结果**: 共找到 **{total_count}** 条组织架构记录\n")
                    
                    key_stats = summary.get("key_statistics", {})
                    if isinstance(key_stats, dict) and key_stats:
                        lines.append("### 📊 关键统计\n")
                        for key, value in key_stats.items():
                            # 如果值是字典，格式化为友好的文本
                            if isinstance(value, dict):
                                value_str = ", ".join([f"{k}: {v}" for k, v in value.items()])
                                lines.append(f"- **{key}**: {value_str}\n")
                            elif isinstance(value, list):
                                value_str = ", ".join([str(v) for v in value])
                                lines.append(f"- **{key}**: {value_str}\n")
                            else:
                                lines.append(f"- **{key}**: {value}\n")
                
                # 显示组织架构树形结构
                data = formatted_result.get("data", [])
                if data and isinstance(data, list):
                    lines.append("### 🏢 组织架构详情\n")
                    # 构建树形结构
                    org_tree = self._build_org_tree(data)
                    lines.extend(self._format_org_tree(org_tree))
                
                # 显示格式化文本
                formatted_text = formatted_result.get("formatted_text")
                if formatted_text:
                    lines.append(f"\n{formatted_text}\n")
        
        return lines
    
    def _format_metadata_result(self, result: Dict[str, Any]) -> List[str]:
        """格式化元数据结果"""
        lines = []
        lines.append("## 🔍 元数据增强结果\n")
        
        if isinstance(result, dict):
            enhancements = result.get("enhancements_provided", {})
            if isinstance(enhancements, dict):
                data_sources = enhancements.get("data_sources", [])
                if data_sources:
                    lines.append(f"### 📚 发现的数据源（共 {len(data_sources)} 个）\n")
                    # 去重并分组
                    unique_sources = {}
                    for source in data_sources:
                        if isinstance(source, dict):
                            display_name = source.get("display_name", source.get("name", "未知"))
                            if display_name not in unique_sources:
                                unique_sources[display_name] = source
                    
                    for display_name, source in list(unique_sources.items())[:10]:  # 最多显示10个
                        source_system = source.get("source_system", "未知")
                        asset_type = source.get("asset_type", "未知")
                        lines.append(f"- **{display_name}** ({asset_type}) - 来源: {source_system}\n")
                    
                    if len(unique_sources) > 10:
                        lines.append(f"\n*还有 {len(unique_sources) - 10} 个数据源未显示*\n")
        
        return lines
    
    def _build_org_tree(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建组织架构树"""
        # 创建索引
        org_map = {}
        root_orgs = []
        
        for org in data:
            if isinstance(org, dict):
                org_id = org.get("部门ID") or org.get("id")
                if org_id:
                    org_map[org_id] = org
                    parent_id = org.get("上级部门") or org.get("parent_id")
                    # 处理parent_id可能是字符串ID或对象的情况
                    if not parent_id or parent_id == "无（集团总部）" or parent_id == "无":
                        root_orgs.append(org_id)
        
        # 构建树结构
        def build_tree(org_id: str, level: int = 0) -> Optional[Dict[str, Any]]:
            org = org_map.get(org_id)
            if not org:
                return None
            
            children = []
            for child_id, child_org in org_map.items():
                if child_id == org_id:
                    continue
                parent_id = child_org.get("上级部门") or child_org.get("parent_id")
                # 匹配parent_id
                if parent_id == org_id:
                    child_node = build_tree(child_id, level + 1)
                    if child_node:
                        children.append(child_node)
            
            return {
                "org": org,
                "children": children,
                "level": level
            }
        
        tree = []
        for root_id in root_orgs:
            node = build_tree(root_id)
            if node:
                tree.append(node)
        
        return {"roots": tree}
    
    def _format_org_tree(self, tree: Dict[str, Any], indent: int = 0) -> List[str]:
        """格式化组织架构树为Markdown"""
        lines = []
        roots = tree.get("roots", [])
        
        def format_node(node: Dict[str, Any], level: int = 0):
            org = node.get("org", {})
            org_name = org.get("部门名称") or org.get("name") or org.get("display_name", "未知")
            org_type = org.get("组织类型") or org.get("organization_type", "")
            org_level = org.get("部门层级") or org.get("level", 0)
            org_code = org.get("code") or org.get("部门代码", "")
            org_desc = org.get("description") or org.get("描述", "")
            
            # 根据层级添加缩进和图标
            indent_str = "  " * level
            if org_type == "集团":
                icon = "🏢"
            elif org_type == "部门":
                icon = "🏛️"
            else:
                icon = "👥"
            
            # 格式化显示
            display_text = f"{icon} **{org_name}**"
            if org_code:
                display_text += f" (`{org_code}`)"
            display_text += f" - {org_type}"
            
            lines.append(f"{indent_str}- {display_text}\n")
            
            # 显示子节点
            children = node.get("children", [])
            for child in children:
                format_node(child, level + 1)
        
        for root in roots:
            format_node(root, 0)
        
        return lines
    
    def _get_agent_display_name(self, agent_type: str) -> str:
        """获取智能体显示名称"""
        names = {
            "metadata": "🔍 元数据增强",
            "data_query": "📋 数据查询",
            "data_clean": "🧹 数据清洗",
            "format": "📝 格式化",
            "result_synthesis": "📊 结果合成"
        }
        return names.get(agent_type, f"📌 {agent_type}")
    
    def _summarize_results(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """总结智能体结果（特殊处理 format_agent 的结果）"""
        summary = {}
        for agent_id, result in agent_results.items():
            try:
                # 特殊处理 format_agent 的结果，提取 formatted_text
                if isinstance(result, dict) and result.get("agent_type") == "format":
                    formatted_content = result.get("formatted_content", {})
                    if isinstance(formatted_content, dict):
                        formatted_text = formatted_content.get("formatted_text")
                        if formatted_text:
                            # 将格式化的文本作为主要内容
                            result = {
                                **result,
                                "formatted_text": formatted_text,
                                "main_content": formatted_text
                            }
                if isinstance(result, dict):
                    if "result" in result:
                        actual_result = result["result"]
                        summary[agent_id] = {
                            "agent_type": result.get("agent_type", "unknown"),
                            "success": result.get("execution_success", False) or result.get("success", False),
                            "result_type": type(actual_result).__name__,
                            "result_keys": list(actual_result.keys())[:5] if isinstance(actual_result, dict) else None,
                            "preview": str(actual_result)[:200] if actual_result else "Empty result"
                        }
                    else:
                        summary[agent_id] = {
                            "agent_type": result.get("agent_type", "unknown"),
                            "success": result.get("execution_success", False) or result.get("success", False),
                            "preview": str(result)[:200]
                        }
                else:
                    # 处理StandardResult或其他类型
                    from ..agents.protocols import StandardResult
                    if isinstance(result, StandardResult):
                        summary[agent_id] = {
                            "agent_type": "standardized",
                            "success": result.success,
                            "result_type": type(result.output).__name__,
                            "confidence": result.confidence,
                            "preview": str(result.output)[:200] if result.output else "Empty output"
                        }
                    else:
                        summary[agent_id] = {
                            "result_type": type(result).__name__,
                            "preview": str(result)[:200]
                        }
            except Exception as e:
                logger.warning(f"Error summarizing result for agent {agent_id}: {e}")
                summary[agent_id] = {
                    "error": str(e),
                    "preview": "Error summarizing result"
                }
        return summary
