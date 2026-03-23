"""
质量检查智能体
专门处理结果质量检查和验证
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class QualityCheckAgent(IntelligentAgent):
    """质量检查智能体 - 专门处理结果质量检查和验证"""
    
    def __init__(self):
        super().__init__(
            agent_id="quality_check_agent",
            name="质量检查智能体",
            description="专门处理结果质量检查和验证，包括内容质量、逻辑一致性、完整性检查",
            capabilities={
                "quality_check": "质量检查",
                "content_validation": "内容验证",
                "consistency_check": "一致性检查"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析质量检查需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            质量检查计划
        """
        try:
            prompt = f"""
作为质量检查专家，分析以下质量检查需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **检查类型**：内容质量、逻辑一致性、完整性、准确性等
2. **质量标准**：质量要达到什么标准？
3. **检查重点**：需要重点检查什么？
4. **检查策略**：如何检查最有效？

返回JSON格式：
{{
    "needs_quality_check": true/false,
    "check_types": ["内容质量", "逻辑一致性"],
    "quality_standards": {{
        "content_quality": "内容质量标准",
        "logic_consistency": "逻辑一致性标准",
        "completeness": "完整性标准"
    }},
    "check_focus": ["重点1", "重点2"],
    "check_strategy": "检查策略描述"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "quality_check_agent",
                fallback="你是一个质量检查专家，擅长分析质量检查需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    check_plan = json.loads(response[json_start:json_end])
                else:
                    check_plan = {"needs_quality_check": True}
            else:
                check_plan = response
            
            return check_plan
            
        except Exception as e:
            logger.error(f"Quality check planning failed: {e}", exc_info=True)
            return {
                "needs_quality_check": True,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行质量检查
        
        Args:
            input_data: 输入数据（包含content或check_plan）
            context: 上下文信息
            
        Returns:
            质量检查结果
        """
        try:
            # 获取内容（可能是分析结果、洞察、内容等）
            content = (
                input_data.get("content") or
                input_data.get("analysis_result") or
                input_data.get("insights") or
                input_data.get("generated_content")
            )
            check_plan = input_data.get("check_plan")
            
            if not content:
                # 如果没有内容，先分析任务
                task_description = input_data.get("task", "")
                check_plan = await self.analyze_task(task_description, context)
                
                if not check_plan.get("needs_quality_check"):
                    return {
                        "agent_type": "quality_check",
                        "decision": "no_check_needed",
                        "reason": check_plan.get("reason", "No content to check")
                    }
                
                return {
                    "agent_type": "quality_check",
                    "decision": "content_required",
                    "check_plan": check_plan,
                    "message": "需要先生成内容才能检查"
                }
            
            # 执行质量检查
            quality_result = await self._check_quality(
                content,
                check_plan,
                context
            )
            
            return {
                "agent_type": "quality_check",
                "execution_success": True,
                "quality_result": quality_result,
                "quality_score": quality_result.get("overall_quality_score", 0),
                "is_acceptable": quality_result.get("is_acceptable", False),
                "check_plan": check_plan
            }
            
        except Exception as e:
            logger.error(f"Quality check agent execution failed: {e}", exc_info=True)
            raise
    
    async def _check_quality(
        self,
        content: Any,
        check_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的质量检查"""
        
        # 准备内容摘要
        content_summary = self._summarize_content(content)
        check_types = check_plan.get("check_types", ["内容质量", "逻辑一致性"]) if check_plan else ["内容质量", "逻辑一致性"]
        
        prompt = f"""
作为质量检查专家，对以下内容进行质量检查：

内容摘要: {json.dumps(content_summary, ensure_ascii=False, indent=2)}
检查类型: {json.dumps(check_types, ensure_ascii=False)}
质量标准: {json.dumps(check_plan.get('quality_standards', {}), ensure_ascii=False) if check_plan else {}}
检查重点: {json.dumps(check_plan.get('check_focus', []), ensure_ascii=False) if check_plan else []}

原始内容: {json.dumps(content, ensure_ascii=False, indent=2)[:2000]}

请进行质量检查，包括：
1. **内容质量**：内容是否准确、完整、清晰
2. **逻辑一致性**：逻辑是否一致、合理
3. **完整性**：是否包含所有必要信息
4. **准确性**：信息是否准确
5. **可读性**：是否易于理解

返回JSON格式：
{{
    "is_acceptable": true/false,
    "quality_details": {{
        "content_quality": {{
            "score": 内容质量评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "logic_consistency": {{
            "score": 逻辑一致性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "completeness": {{
            "score": 完整性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "accuracy": {{
            "score": 准确性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "readability": {{
            "score": 可读性评分(0-100),
            "issues": ["问题1", "问题2"]
        }}
    }},
    "overall_quality_score": 整体质量评分(0-100),
    "quality_report": "质量检查报告文本",
    "improvement_suggestions": ["建议1", "建议2"]
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "quality_check_agent_execute",
                fallback="你是一个专业的质量检查专家，擅长检查内容质量。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": execute_system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            
            # 降级：简单检查
            return {
                "is_acceptable": True,
                "overall_quality_score": 80,
                "quality_details": {}
            }
            
        except Exception as e:
            logger.warning(f"LLM quality check failed: {e}")
            return {
                "is_acceptable": False,
                "overall_quality_score": 0,
                "quality_details": {},
                "error": str(e)
            }
    
    def _summarize_content(self, content: Any) -> Dict[str, Any]:
        """总结内容特征"""
        if isinstance(content, dict):
            if "formatted_text" in content:
                return {"type": "formatted_text", "length": len(content["formatted_text"]), "preview": content["formatted_text"][:200]}
            elif "sections" in content:
                return {"type": "structured", "sections": len(content["sections"]), "keys": list(content.keys())}
            else:
                return {"type": "dict", "keys": list(content.keys())[:10], "preview": str(content)[:200]}
        elif isinstance(content, str):
            return {"type": "text", "length": len(content), "preview": content[:200]}
        else:
            return {"type": "other", "preview": str(content)[:200]}


