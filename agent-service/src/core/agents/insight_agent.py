"""
洞察生成智能体
专门生成业务洞察和业务解读
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class InsightAgent(IntelligentAgent):
    """洞察生成智能体 - 专门生成业务洞察和业务解读"""
    
    def __init__(self):
        super().__init__(
            agent_id="insight_agent",
            name="洞察生成智能体",
            description="专门生成业务洞察和业务解读，包括业务含义、行动建议、风险评估",
            capabilities={
                "insight_generation": "洞察生成",
                "business_interpretation": "业务解读",
                "action_recommendation": "行动建议"
            }
        )
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析洞察生成需求
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            洞察生成计划
        """
        try:
            prompt = f"""
作为业务洞察专家，分析以下洞察生成需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **洞察类型**：业务洞察、趋势洞察、风险洞察等
2. **洞察深度**：浅层洞察 vs 深度洞察
3. **目标受众**：管理层、业务人员、技术人员等
4. **输出格式**：报告、摘要、建议等

返回JSON格式：
{{
    "needs_insights": true/false,
    "insight_type": "business|trend|risk|opportunity|other",
    "insight_depth": "shallow|medium|deep",
    "target_audience": "管理层|业务人员|技术人员",
    "output_format": "report|summary|recommendations"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "insight_agent",
                fallback="你是一个业务洞察专家，擅长生成业务洞察和建议。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    insight_plan = json.loads(response[json_start:json_end])
                else:
                    insight_plan = {"needs_insights": False}
            else:
                insight_plan = response
            
            return insight_plan
            
        except Exception as e:
            logger.error(f"Insight planning failed: {e}", exc_info=True)
            return {
                "needs_insights": False,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成业务洞察
        
        Args:
            input_data: 输入数据（包含analysis_result或insight_plan）
            context: 上下文信息
            
        Returns:
            洞察结果
        """
        try:
            # 获取分析结果
            analysis_result = input_data.get("analysis_result") or input_data.get("data")
            insight_plan = input_data.get("insight_plan")
            
            if not analysis_result:
                # 如果没有分析结果，先分析任务
                task_description = input_data.get("task", "")
                insight_plan = await self.analyze_task(task_description, context)
                
                if not insight_plan.get("needs_insights"):
                    return {
                        "agent_type": "insight",
                        "decision": "no_insights_needed",
                        "reason": insight_plan.get("reason", "No analysis result to generate insights from")
                    }
                
                return {
                    "agent_type": "insight",
                    "decision": "analysis_required",
                    "insight_plan": insight_plan,
                    "message": "需要先进行数据分析才能生成洞察"
                }
            
            # 生成洞察
            insights = await self._generate_insights(
                analysis_result,
                insight_plan,
                context
            )
            
            return {
                "agent_type": "insight",
                "execution_success": True,
                "insights": insights,
                "insight_plan": insight_plan
            }
            
        except Exception as e:
            logger.error(f"Insight agent execution failed: {e}", exc_info=True)
            raise
    
    async def _generate_insights(
        self,
        analysis_result: Dict[str, Any],
        insight_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成业务洞察"""
        
        insight_type = insight_plan.get("insight_type", "business") if insight_plan else "business"
        target_audience = insight_plan.get("target_audience", "管理层") if insight_plan else "管理层"
        
        prompt = f"""
作为业务洞察专家，基于以下分析结果生成业务洞察：

分析结果: {json.dumps(analysis_result, ensure_ascii=False, indent=2)}
洞察类型: {insight_type}
目标受众: {target_audience}
业务上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请生成深度业务洞察，包括：
1. **核心发现**：最重要的发现（3-5条）
2. **业务含义**：这些发现对业务意味着什么？
3. **机会识别**：发现了什么业务机会？
4. **风险提示**：有什么潜在风险？
5. **行动建议**：基于洞察，建议采取什么行动？
6. **优先级**：哪些行动最紧急/重要？

返回JSON格式：
{{
    "core_findings": ["发现1", "发现2", "发现3"],
    "business_implications": ["含义1", "含义2"],
    "opportunities": ["机会1", "机会2"],
    "risks": ["风险1", "风险2"],
    "action_recommendations": [
        {{
            "action": "行动描述",
            "priority": "high|medium|low",
            "impact": "影响描述",
            "effort": "effort描述"
        }}
    ],
    "executive_summary": "执行摘要（1-2句话）"
}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "insight_agent_execute",
                fallback="你是一个业务洞察专家，擅长从数据分析结果中提取业务洞察并提供行动建议。"
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
            
            # 降级：简单洞察
            return {
                "core_findings": ["数据已分析，需要进一步解读"],
                "action_recommendations": []
            }
            
        except Exception as e:
            logger.warning(f"LLM insight generation failed: {e}")
            return {
                "core_findings": ["洞察生成失败"],
                "action_recommendations": []
            }


