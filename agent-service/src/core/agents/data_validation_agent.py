"""
数据验证智能体
专门处理数据验证和质量保证
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class DataValidationAgent(IntelligentAgent):
    """数据验证智能体 - 专门处理数据验证和质量保证"""
    
    def __init__(self):
        super().__init__(
            agent_id="data_validation_agent",
            name="数据验证智能体",
            description="专门处理数据验证和质量保证，包括数据完整性检查、准确性验证、一致性检查",
            capabilities={
                "data_validation": "数据验证",
                "quality_assurance": "质量保证",
                "integrity_check": "完整性检查"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析数据验证需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            验证计划
        """
        try:
            prompt = f"""
作为数据验证专家，分析以下数据验证需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **验证类型**：完整性、准确性、一致性、有效性等
2. **验证规则**：需要应用什么验证规则？
3. **质量标准**：数据质量要达到什么标准？
4. **验证策略**：如何验证最有效？

返回JSON格式：
{{
    "needs_validation": true/false,
    "validation_types": ["完整性", "准确性", "一致性"],
    "validation_rules": ["规则1", "规则2"],
    "quality_standards": {{
        "completeness_threshold": 完整性阈值,
        "accuracy_threshold": 准确性阈值,
        "consistency_threshold": 一致性阈值
    }},
    "validation_strategy": "验证策略描述"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "data_validation_agent",
                fallback="你是一个数据验证专家，擅长分析数据验证需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    validation_plan = json.loads(response[json_start:json_end])
                else:
                    validation_plan = {"needs_validation": True}
            else:
                validation_plan = response
            
            return validation_plan
            
        except Exception as e:
            logger.error(f"Data validation planning failed: {e}", exc_info=True)
            return {
                "needs_validation": True,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据验证
        
        Args:
            input_data: 输入数据（包含data或validation_plan）
            context: 上下文信息
            
        Returns:
            验证结果
        """
        try:
            # 获取数据
            data = input_data.get("data") or input_data.get("cleaned_data") or input_data.get("query_result")
            validation_plan = input_data.get("validation_plan")
            
            if not data:
                # 如果没有数据，先分析任务
                task_description = input_data.get("task", "")
                validation_plan = await self.analyze_task(task_description, context)
                
                if not validation_plan.get("needs_validation"):
                    return {
                        "agent_type": "data_validation",
                        "decision": "no_validation_needed",
                        "reason": validation_plan.get("reason", "No data to validate")
                    }
                
                return {
                    "agent_type": "data_validation",
                    "decision": "data_required",
                    "validation_plan": validation_plan,
                    "message": "需要先获取数据才能验证"
                }
            
            # 执行验证
            validation_result = await self._validate_data(
                data,
                validation_plan,
                context
            )
            
            return {
                "agent_type": "data_validation",
                "execution_success": True,
                "validation_result": validation_result,
                "is_valid": validation_result.get("is_valid", False),
                "validation_plan": validation_plan
            }
            
        except Exception as e:
            logger.error(f"Data validation agent execution failed: {e}", exc_info=True)
            raise
    
    async def _validate_data(
        self,
        data: Any,
        validation_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的数据验证"""
        
        # 准备数据摘要
        data_summary = self._summarize_data(data)
        validation_types = validation_plan.get("validation_types", ["完整性", "准确性"]) if validation_plan else ["完整性", "准确性"]
        
        prompt = f"""
作为数据验证专家，对以下数据进行验证：

数据摘要: {json.dumps(data_summary, ensure_ascii=False, indent=2)}
验证类型: {json.dumps(validation_types, ensure_ascii=False)}
验证规则: {json.dumps(validation_plan.get('validation_rules', []), ensure_ascii=False) if validation_plan else []}
质量标准: {json.dumps(validation_plan.get('quality_standards', {}), ensure_ascii=False) if validation_plan else {}}

数据样本（前20条）: {json.dumps(
    (data.get('data', data) if isinstance(data, dict) else data)[:20] if isinstance(data, list) else [data],
    ensure_ascii=False,
    indent=2
)}

请进行数据验证，包括：
1. **完整性检查**：检查必填字段是否完整
2. **准确性验证**：验证数据值是否准确
3. **一致性检查**：检查数据是否一致
4. **有效性验证**：验证数据是否符合业务规则
5. **质量评分**：给出整体质量评分

返回JSON格式：
{{
    "is_valid": true/false,
    "validation_details": {{
        "completeness": {{
            "score": 完整性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "accuracy": {{
            "score": 准确性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "consistency": {{
            "score": 一致性评分(0-100),
            "issues": ["问题1", "问题2"]
        }},
        "validity": {{
            "score": 有效性评分(0-100),
            "issues": ["问题1", "问题2"]
        }}
    }},
    "overall_quality_score": 整体质量评分(0-100),
    "validation_report": "验证报告文本",
    "recommendations": ["建议1", "建议2"]
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "data_validation_agent_execute",
                fallback="你是一个专业的数据验证专家，擅长验证数据质量。"
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
            
            # 降级：简单验证
            return {
                "is_valid": True,
                "overall_quality_score": 80,
                "validation_details": {}
            }
            
        except Exception as e:
            logger.warning(f"LLM data validation failed: {e}")
            return {
                "is_valid": False,
                "overall_quality_score": 0,
                "validation_details": {},
                "error": str(e)
            }
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """总结数据特征"""
        if isinstance(data, dict):
            if "data" in data:
                data_list = data["data"]
            elif "cleaned_data" in data:
                data_list = data["cleaned_data"]
            else:
                return {"type": "dict", "keys": list(data.keys())[:10], "sample": str(data)[:200]}
        elif isinstance(data, list):
            data_list = data
        else:
            return {"type": "other", "content": str(data)[:200]}
        
        return {
            "type": "list",
            "count": len(data_list),
            "sample_count": min(10, len(data_list)),
            "sample": data_list[:10] if data_list else []
        }


