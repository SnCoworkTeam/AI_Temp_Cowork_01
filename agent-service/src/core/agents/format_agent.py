"""
格式优化智能体
专门处理格式优化和模板应用
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class FormatAgent(IntelligentAgent):
    """格式优化智能体 - 专门处理格式优化和模板应用"""
    
    def __init__(self):
        super().__init__(
            agent_id="format_agent",
            name="格式优化智能体",
            description="专门处理格式优化和模板应用，包括Markdown格式化、HTML格式化、邮件格式化",
            capabilities={
                "format_optimization": "格式优化",
                "template_application": "模板应用",
                "style_enhancement": "样式增强"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析格式优化需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            格式优化计划
        """
        try:
            # 清理上下文，移除不能序列化的对象
            clean_context = self._clean_context_for_json(context)
            
            prompt = f"""
作为格式优化专家，分析以下格式优化需求：

任务: {task_description}
上下文: {json.dumps(clean_context, ensure_ascii=False, indent=2)}

请分析：
1. **目标格式**：Markdown、HTML、邮件、PDF、其他
2. **格式要求**：需要什么格式特性？
3. **模板需求**：是否需要应用模板？
4. **样式要求**：需要什么样式？

返回JSON格式：
{{
    "needs_formatting": true/false,
    "target_format": "markdown|html|email|pdf|other",
    "format_requirements": ["要求1", "要求2"],
    "template_needed": true/false,
    "template_name": "模板名称（如果需要）",
    "style_requirements": ["样式1", "样式2"]
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "format_agent",
                fallback="你是一个格式优化专家，擅长分析格式优化需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    format_plan = json.loads(response[json_start:json_end])
                else:
                    format_plan = {"needs_formatting": True, "target_format": "markdown"}
            else:
                format_plan = response
            
            return format_plan
            
        except Exception as e:
            logger.error(f"Format planning failed: {e}", exc_info=True)
            return {
                "needs_formatting": True,
                "target_format": "markdown",
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化格式
        
        Args:
            input_data: 输入数据（包含content或format_plan）
            context: 上下文信息
            
        Returns:
            格式化后的内容
        """
        try:
            # 尝试多种方式获取内容
            content = (input_data.get("content") or 
                      input_data.get("generated_content") or
                      input_data.get("content_agent_result") or
                      context.get("content_agent_result") or
                      context.get("agent_7_result") or  # content_agent通常是agent_7
                      context.get("agent_6_result") or   # 也可能是insight_agent的结果
                      None)
            
            # 如果content是字典，尝试提取实际内容
            if isinstance(content, dict):
                content = (content.get("generated_content") or
                          content.get("formatted_text") or
                          content.get("content") or
                          content.get("sections") or
                          content.get("main_content") or
                          content)
            
            format_plan = input_data.get("format_plan")
            
            if not content:
                # 尝试从所有智能体结果中查找内容
                agent_results = context.get("_agent_results", {})
                for agent_id, result in agent_results.items():
                    if "content" in agent_id.lower() or "agent_7" in agent_id:
                        if isinstance(result, dict):
                            content = (result.get("generated_content") or
                                      result.get("formatted_text") or
                                      result.get("content") or
                                      result.get("result", {}).get("generated_content") if isinstance(result.get("result"), dict) else None)
                        if content:
                            break
                
                if not content:
                    # 如果没有内容，先分析任务
                    task_description = input_data.get("task", "")
                    format_plan = await self.analyze_task(task_description, context)
                    
                    return {
                        "agent_type": "format",
                        "execution_success": False,
                        "decision": "content_required",
                        "format_plan": format_plan,
                        "message": "需要先生成内容才能格式化",
                        "error": "没有内容可供格式化"
                    }
            
            # 优化格式
            formatted_content = await self._optimize_format(
                content,
                format_plan,
                context
            )
            
            return {
                "agent_type": "format",
                "execution_success": True,
                "target_format": format_plan.get("target_format", "markdown") if format_plan else "markdown",
                "formatted_content": formatted_content,
                "format_plan": format_plan
            }
            
        except Exception as e:
            logger.error(f"Format agent execution failed: {e}", exc_info=True)
            raise
    
    async def _optimize_format(
        self,
        content: Any,
        format_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化格式"""
        
        target_format = format_plan.get("target_format", "markdown") if format_plan else "markdown"
        
        # 如果内容已经是字典，提取文本
        if isinstance(content, dict):
            text_content = content.get("formatted_text") or content.get("content") or json.dumps(content, ensure_ascii=False, indent=2)
        else:
            text_content = str(content)
        
        prompt = f"""
作为格式优化专家，优化以下内容的格式：

原始内容: {text_content[:2000]}  # 限制长度
目标格式: {target_format}
格式要求: {json.dumps(format_plan.get('format_requirements', []), ensure_ascii=False) if format_plan else []}
样式要求: {json.dumps(format_plan.get('style_requirements', []), ensure_ascii=False) if format_plan else []}

请优化格式，要求：
1. **格式正确**：符合目标格式规范
2. **结构清晰**：层次分明，易于阅读
3. **样式美观**：应用合适的样式
4. **内容完整**：不丢失任何重要信息

返回JSON格式：
{{
    "formatted_text": "格式化后的文本内容",
    "format_type": "{target_format}",
    "format_metadata": {{
        "sections": ["章节1", "章节2"],
        "key_elements": ["元素1", "元素2"]
    }}
}}
"""
        
        try:
            # 从提示词模板获取系统提示词（支持动态参数）
            from ..prompt_utils import format_prompt
            system_prompt = format_prompt("format_agent_execute", target_format=target_format)
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
                else:
                    # 如果没有JSON，直接使用文本
                    return {
                        "formatted_text": response,
                        "format_type": target_format
                    }
            else:
                return response
            
        except Exception as e:
            logger.warning(f"LLM format optimization failed: {e}")
            return {
                "formatted_text": text_content,
                "format_type": target_format
            }
    
    def _clean_context_for_json(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理上下文，移除不能JSON序列化的对象（如StandardResult）
        
        Args:
            context: 原始上下文
            
        Returns:
            清理后的上下文
        """
        from ..agents.protocols import StandardResult
        
        clean_context = {}
        for key, value in context.items():
            try:
                # 尝试序列化以检查是否可序列化
                if isinstance(value, StandardResult):
                    # 转换StandardResult为字典
                    clean_context[key] = value.to_dict()
                elif isinstance(value, dict):
                    # 递归清理字典
                    clean_context[key] = self._clean_context_for_json(value)
                elif isinstance(value, list):
                    # 清理列表中的元素
                    clean_context[key] = [
                        item.to_dict() if isinstance(item, StandardResult) else item
                        for item in value
                    ]
                else:
                    # 尝试序列化检查
                    json.dumps(value, ensure_ascii=False)
                    clean_context[key] = value
            except (TypeError, ValueError):
                # 如果不能序列化，转换为字符串
                clean_context[key] = str(value)
        
        return clean_context


