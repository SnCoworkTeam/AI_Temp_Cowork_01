"""
结果合成智能体
专门协调所有智能体输出，合成最终结果
"""
import logging
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
            
            response = await self.llm.chat([
                {"role": "system", "content": "你是一个结果合成专家，擅长分析结果合成需求。"},
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
        processed_agent_results = {}
        for agent_id, result in agent_results.items():
            if isinstance(result, dict) and result.get("agent_type") == "format":
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
        
        prompt = f"""
作为结果合成专家，协调以下所有智能体的输出，合成最终结果：

用户原始请求: "{user_input}"
智能体结果摘要: {json.dumps(results_summary, ensure_ascii=False, indent=2)}
合成策略: {synthesis_plan.get('synthesis_strategy', '') if synthesis_plan else '智能整合所有结果'}
优先级规则: {json.dumps(synthesis_plan.get('priority_rules', []), ensure_ascii=False) if synthesis_plan else []}
输出格式要求: {synthesis_plan.get('output_format', '') if synthesis_plan else ''}

所有智能体的详细结果: {json.dumps(processed_agent_results, ensure_ascii=False, indent=2)[:3000]}

请进行结果合成，包括：
1. **结果整合**：整合所有智能体的输出
2. **冲突解决**：解决不同智能体输出之间的冲突
3. **优先级排序**：根据重要性排序信息
4. **内容优化**：优化最终输出的内容和结构
5. **格式统一**：统一输出格式

返回JSON格式：
{{
    "synthesized_result": {{
        "title": "结果标题",
        "summary": "执行摘要",
        "main_content": "主要内容",
        "key_findings": ["发现1", "发现2"],
        "recommendations": ["建议1", "建议2"],
        "details": {{"详细内容": "..."}}
    }},
    "formatted_output": "格式化的最终输出文本（Markdown格式）",
    "synthesis_summary": {{
        "agents_used": ["智能体1", "智能体2"],
        "results_integrated": 整合的结果数量,
        "conflicts_resolved": 解决的冲突数量,
        "priority_ranked": true/false
    }},
    "synthesis_report": "合成报告文本"
}}
"""
        
        try:
            # 添加超时保护，避免LLM调用时间过长
            import asyncio
            response = await asyncio.wait_for(
                self.llm.chat([
                    {"role": "system", "content": "你是一个专业的结果合成专家，擅长协调多个智能体的输出并合成高质量的最终结果。"},
                    {"role": "user", "content": prompt}
                ]),
                timeout=60.0  # 60秒超时
            )
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
                else:
                    # 如果没有JSON，尝试提取文本
                    return {
                        "synthesized_result": {
                            "title": "执行结果",
                            "summary": response[:500],
                            "main_content": response
                        },
                        "formatted_output": response,
                        "synthesis_summary": {
                            "agents_used": list(agent_results.keys()),
                            "results_integrated": len(agent_results)
                        }
                    }
            else:
                return response
            
        except Exception as e:
            logger.warning(f"LLM result synthesis failed: {e}")
            # 降级：简单合并，优先使用 format_agent 的格式化内容
            fallback_output = None
            for agent_id, result in processed_agent_results.items():
                if isinstance(result, dict):
                    # 优先使用 format_agent 的 formatted_text
                    if result.get("agent_type") == "format":
                        formatted_text = result.get("formatted_text") or result.get("extracted_content")
                        if formatted_text:
                            fallback_output = formatted_text
                            break
                    # 或者使用其他智能体的 formatted_text
                    elif result.get("formatted_text"):
                        fallback_output = result.get("formatted_text")
                        break
            
            # 如果没有找到格式化内容，使用 JSON 格式
            if not fallback_output:
                fallback_output = json.dumps(processed_agent_results, ensure_ascii=False, indent=2)
            
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


