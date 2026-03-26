"""
结果整合器
整合多个服务的执行结果，生成最终响应
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResultAggregator:
    """结果整合器"""
    
    def __init__(self):
        pass
    
    async def aggregate_results(
        self,
        step_results: Dict[str, Any],
        plan_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        整合多个步骤的执行结果
        
        Args:
            step_results: 步骤执行结果字典 {step_id: result}
            plan_context: 计划上下文
            
        Returns:
            整合后的结果
        """
        try:
            # 分析所有步骤的执行状态
            all_success = all(
                result.get("success", False) 
                for result in step_results.values()
            )
            
            # 收集所有输出
            outputs = []
            errors = []
            
            for step_id, result in step_results.items():
                if result.get("success"):
                    output = result.get("output") or result.get("result")
                    if output:
                        outputs.append({
                            "step_id": step_id,
                            "output": output
                        })
                else:
                    error = result.get("error") or result.get("error_message")
                    if error:
                        errors.append({
                            "step_id": step_id,
                            "error": error
                        })
            
            # 构建整合结果
            aggregated_result = {
                "success": all_success,
                "total_steps": len(step_results),
                "successful_steps": sum(1 for r in step_results.values() if r.get("success")),
                "failed_steps": sum(1 for r in step_results.values() if not r.get("success")),
                "outputs": outputs,
                "errors": errors if errors else None,
                "aggregated_output": self._format_aggregated_output(outputs),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 如果有错误，添加错误摘要
            if errors:
                aggregated_result["error_summary"] = self._generate_error_summary(errors)
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Result aggregation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Result aggregation failed: {str(e)}",
                "step_results": step_results
            }
    
    def _format_aggregated_output(self, outputs: List[Dict[str, Any]]) -> str:
        """
        格式化整合后的输出
        
        Args:
            outputs: 输出列表
            
        Returns:
            格式化后的输出字符串
        """
        if not outputs:
            return "无输出结果"
        
        if len(outputs) == 1:
            # 单个输出，直接返回
            output = outputs[0].get("output")
            if isinstance(output, str):
                return output
            elif isinstance(output, dict):
                # 尝试提取关键信息
                return str(output.get("result") or output.get("data") or output)
            else:
                return str(output)
        
        # 多个输出，需要整合
        formatted_parts = []
        for i, output_item in enumerate(outputs, 1):
            step_id = output_item.get("step_id", f"步骤{i}")
            output = output_item.get("output")
            
            if isinstance(output, str):
                formatted_parts.append(f"【{step_id}】\n{output}")
            elif isinstance(output, dict):
                # 提取关键信息
                key_info = output.get("result") or output.get("data") or output
                formatted_parts.append(f"【{step_id}】\n{key_info}")
            else:
                formatted_parts.append(f"【{step_id}】\n{str(output)}")
        
        return "\n\n".join(formatted_parts)
    
    def _generate_error_summary(self, errors: List[Dict[str, Any]]) -> str:
        """
        生成错误摘要
        
        Args:
            errors: 错误列表
            
        Returns:
            错误摘要字符串
        """
        if not errors:
            return ""
        
        error_messages = []
        for error_item in errors:
            step_id = error_item.get("step_id", "未知步骤")
            error = error_item.get("error", "未知错误")
            error_messages.append(f"{step_id}: {error}")
        
        return f"共{len(errors)}个步骤执行失败：\n" + "\n".join(error_messages)
    
    async def aggregate_with_llm(
        self,
        step_results: Dict[str, Any],
        original_task: str,
        plan_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用LLM整合结果（更智能的整合）
        
        Args:
            step_results: 步骤执行结果
            original_task: 原始任务
            plan_context: 计划上下文
            
        Returns:
            整合后的结果
        """
        try:
            # 先进行基础整合
            base_result = await self.aggregate_results(step_results, plan_context)
            
            # 如果有LLM可用，使用LLM进行智能整合
            import os
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from langchain_openai import ChatOpenAI
                    from langchain.schema import HumanMessage, SystemMessage
                    
                    api_key = os.getenv("OPENAI_API_KEY")
                    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/v1").rstrip("/")
                    model = os.getenv("LLM_MODEL", "deepseek-chat")
                    
                    llm = ChatOpenAI(
                        model=model,
                        temperature=0.3,
                        api_key=api_key,
                        base_url=base_url,
                    )
                    
                    # 构建整合提示
                    system_prompt = """你是一个结果整合专家，负责将多个步骤的执行结果整合成清晰、完整的最终答案。

请分析所有步骤的结果，提取关键信息，生成一个结构化的最终答案。"""
                    
                    outputs_text = base_result.get("aggregated_output", "")
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"""原始任务：{original_task}

执行结果：
{outputs_text}

请整合这些结果，生成一个清晰、完整的最终答案。""")
                    ]
                    
                    response = await llm.ainvoke(messages)
                    base_result["llm_aggregated_output"] = response.content
                    base_result["aggregated_output"] = response.content
                    
                except Exception as e:
                    logger.warning(f"LLM aggregation failed, using base result: {e}")
            
            return base_result
            
        except Exception as e:
            logger.error(f"LLM result aggregation failed: {e}", exc_info=True)
            return await self.aggregate_results(step_results, plan_context)


# 全局结果整合器实例
result_aggregator = ResultAggregator()




