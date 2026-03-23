"""
数据增强智能体
专门处理数据增强和特征工程
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class DataEnrichAgent(IntelligentAgent):
    """数据增强智能体 - 专门处理数据增强和特征工程"""
    
    def __init__(self):
        super().__init__(
            agent_id="data_enrich_agent",
            name="数据增强智能体",
            description="专门处理数据增强和特征工程，包括数据补充、特征提取、数据关联",
            capabilities={
                "data_enhancement": "数据增强",
                "feature_engineering": "特征工程",
                "data_enrichment": "数据补充"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析数据增强需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            增强计划
        """
        try:
            prompt = f"""
作为数据增强专家，分析以下数据增强需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **增强类型**：数据补充、特征提取、数据关联、计算字段等
2. **增强策略**：如何增强数据？
3. **数据源**：需要从哪些数据源补充数据？
4. **特征需求**：需要提取什么特征？

返回JSON格式：
{{
    "needs_enrichment": true/false,
    "enrichment_types": ["数据补充", "特征提取"],
    "enrichment_strategy": "增强策略描述",
    "data_sources": ["数据源1", "数据源2"],
    "feature_requirements": ["特征1", "特征2"]
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "data_enrich_agent",
                fallback="你是一个数据增强专家，擅长分析数据增强需求。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    enrichment_plan = json.loads(response[json_start:json_end])
                else:
                    enrichment_plan = {"needs_enrichment": False}
            else:
                enrichment_plan = response
            
            return enrichment_plan
            
        except Exception as e:
            logger.error(f"Data enrichment planning failed: {e}", exc_info=True)
            return {
                "needs_enrichment": False,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据增强
        
        Args:
            input_data: 输入数据（包含data或enrichment_plan）
            context: 上下文信息
            
        Returns:
            增强后的数据
        """
        try:
            # 获取数据
            data = input_data.get("data") or input_data.get("cleaned_data") or input_data.get("validated_data")
            enrichment_plan = input_data.get("enrichment_plan")
            
            if not data:
                # 如果没有数据，先分析任务
                task_description = input_data.get("task", "")
                enrichment_plan = await self.analyze_task(task_description, context)
                
                if not enrichment_plan.get("needs_enrichment"):
                    return {
                        "agent_type": "data_enrich",
                        "decision": "no_enrichment_needed",
                        "reason": enrichment_plan.get("reason", "No data to enrich")
                    }
                
                return {
                    "agent_type": "data_enrich",
                    "execution_success": False,
                    "decision": "data_required",
                    "enrichment_plan": enrichment_plan,
                    "message": "需要先获取数据才能增强",
                    "error": "没有数据可供增强"
                }
            
            # 执行增强
            enriched_data = await self._enrich_data(
                data,
                enrichment_plan,
                context
            )
            
            return {
                "agent_type": "data_enrich",
                "execution_success": True,
                "enriched_data": enriched_data,
                "enrichment_summary": enriched_data.get("enrichment_summary", {}),
                "enrichment_plan": enrichment_plan
            }
            
        except Exception as e:
            logger.error(f"Data enrich agent execution failed: {e}", exc_info=True)
            raise
    
    async def _enrich_data(
        self,
        data: Any,
        enrichment_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的数据增强"""
        
        # 准备数据摘要
        data_summary = self._summarize_data(data)
        enrichment_types = enrichment_plan.get("enrichment_types", ["特征提取"]) if enrichment_plan else ["特征提取"]
        
        prompt = f"""
作为数据增强专家，对以下数据进行增强：

数据摘要: {json.dumps(data_summary, ensure_ascii=False, indent=2)}
增强类型: {json.dumps(enrichment_types, ensure_ascii=False)}
增强策略: {enrichment_plan.get('enrichment_strategy', '') if enrichment_plan else ''}
特征需求: {json.dumps(enrichment_plan.get('feature_requirements', []), ensure_ascii=False) if enrichment_plan else []}

原始数据（前20条）: {json.dumps(
    (data.get('data', data) if isinstance(data, dict) else data)[:20] if isinstance(data, list) else [data],
    ensure_ascii=False,
    indent=2
)}

请进行数据增强，包括：
1. **特征提取**：从现有数据中提取新特征
2. **数据补充**：补充缺失的信息
3. **计算字段**：计算衍生字段
4. **数据关联**：关联其他数据源的信息
5. **数据转换**：转换数据格式或单位

返回JSON格式：
{{
    "enriched_data": [
        {{"原始字段": "值", "新增字段1": "值", "新增字段2": "值"}}
    ],
    "enrichment_summary": {{
        "original_count": 原始记录数,
        "enriched_count": 增强后记录数,
        "new_features": ["新特征1", "新特征2"],
        "enrichment_methods": ["方法1", "方法2"],
        "value_added": "增强价值描述"
    }},
    "enrichment_report": "增强报告文本"
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "data_enrich_agent_execute",
                fallback="你是一个专业的数据增强专家，擅长增强数据价值。"
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
            
            # 降级：简单增强
            return {
                "enriched_data": data if isinstance(data, list) else [data],
                "enrichment_summary": {
                    "original_count": len(data) if isinstance(data, list) else 1,
                    "enriched_count": len(data) if isinstance(data, list) else 1,
                    "new_features": []
                }
            }
            
        except Exception as e:
            logger.warning(f"LLM data enrichment failed: {e}")
            return {
                "enriched_data": data if isinstance(data, list) else [data],
                "enrichment_summary": {
                    "original_count": len(data) if isinstance(data, list) else 1,
                    "enriched_count": len(data) if isinstance(data, list) else 1,
                    "new_features": []
                }
            }
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """总结数据特征"""
        if isinstance(data, dict):
            if "data" in data:
                data_list = data["data"]
            elif "cleaned_data" in data:
                data_list = data["cleaned_data"]
            elif "validated_data" in data:
                data_list = data["validated_data"]
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


