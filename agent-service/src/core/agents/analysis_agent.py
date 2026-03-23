"""
分析智能体
专门处理数据分析和模式识别
"""
import logging
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from datetime import datetime
import json

from .base_agent import IntelligentAgent  # 保留用于向后兼容
from .unified_base_agent import BaseAgent, ExecutionPlan, ExecutionResult, AgentState
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """分析智能体 - 专门处理数据分析和模式识别"""

    def __init__(self):
        super().__init__(
            agent_id="analysis_agent",
            name="分析智能体",
            description="专门处理数据分析和模式识别，包括统计分析、趋势分析、异常检测",
            capabilities={
                "data_analysis": "数据分析",
                "pattern_recognition": "模式识别",
                "statistical_analysis": "统计分析"
            }
        )
        self.llm = deepseek_llm

    async def plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        规划任务（统一接口实现）

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            ExecutionPlan: 执行计划
        """
        self.set_state(AgentState.PLANNING)
        context = context or {}

        try:
            # 使用analyze_task生成分析计划
            analysis_plan = await self.analyze_task(task, context)

            # 转换为ExecutionPlan
            plan = ExecutionPlan(
                plan_name=f"数据分析: {task[:50]}",
                description=f"分析任务: {task}",
                execution_mode="sequence",
                steps=[{
                    "step_type": "analysis",
                    "analysis_type": analysis_plan.get("analysis_type", "statistical"),
                    "analysis_dimensions": analysis_plan.get("analysis_dimensions", []),
                    "analysis_methods": analysis_plan.get("analysis_methods", [])
                }],
                expected_outcomes=analysis_plan.get("output_requirements", {}).get("format", "分析报告"),
                metadata={"analysis_plan": analysis_plan}
            )

            self.set_state(AgentState.IDLE)
            return plan
        except Exception as e:
            logger.error(f"规划任务失败: {e}", exc_info=True)
            self.set_state(AgentState.FAILED)
            raise

    async def execute(
        self,
        plan: ExecutionPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        执行计划（统一接口实现）

        Args:
            plan: 执行计划
            context: 上下文信息

        Returns:
            ExecutionResult: 执行结果
        """
        self.set_state(AgentState.EXECUTING)
        context = context or {}

        try:
            # 从plan中提取分析计划
            analysis_plan = plan.metadata.get("analysis_plan", {})

            # 构建input_data（兼容旧接口）
            input_data = {
                "task": plan.description,
                "analysis_plan": analysis_plan,
                "data": context.get("data"),
                "query_result": context.get("query_result"),
                "formatted_result": context.get("formatted_result")
            }

            # 调用旧的execute方法
            old_result = await self._execute_legacy(input_data, context)

            # 转换为ExecutionResult
            result = ExecutionResult(
                plan_name=plan.plan_name,
                success=old_result.get("success", True),
                steps_executed=1,
                steps_succeeded=1 if old_result.get("success", True) else 0,
                results=[old_result],
                summary=old_result.get("summary", "分析完成"),
                metadata={"analysis_result": old_result}
            )

            self.set_state(AgentState.COMPLETED if result.success else AgentState.FAILED)
            self.execution_count += 1
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1
            self.last_executed_at = datetime.utcnow()

            return result
        except Exception as e:
            logger.error(f"执行计划失败: {e}", exc_info=True)
            self.set_state(AgentState.FAILED)
            self.execution_count += 1
            self.failure_count += 1
            self.last_executed_at = datetime.utcnow()

            return ExecutionResult(
                plan_name=plan.plan_name,
                success=False,
                steps_executed=0,
                steps_succeeded=0,
                results=[],
                error=str(e),
                summary=f"执行失败: {e}"
            )

    async def _execute_legacy(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据分析（旧接口，向后兼容）

        Args:
            input_data: 输入数据（包含data或analysis_plan）
            context: 上下文信息

        Returns:
            分析结果
        """
        try:
            # 获取数据（可能来自其他智能体的输出）
            data = input_data.get("data") or input_data.get("query_result") or input_data.get("formatted_result")
            analysis_plan = input_data.get("analysis_plan")

            if not data:
                # 如果没有数据，先分析任务
                task_description = input_data.get("task", "")
                analysis_plan = await self.analyze_task(task_description, context)

                if not analysis_plan.get("needs_analysis"):
                    return {
                        "agent_type": "analysis",
                        "decision": "no_analysis_needed",
                        "reason": analysis_plan.get("reason", "No data to analyze"),
                        "success": False
                    }

                return {
                    "agent_type": "analysis",
                    "decision": "data_required",
                    "analysis_plan": analysis_plan,
                    "message": "需要先获取数据才能进行分析",
                    "success": False
                }

            # 执行分析
            analysis_type = analysis_plan.get("analysis_type", "statistical") if analysis_plan else "statistical"
            analysis_result = await self._perform_analysis(
                data,
                analysis_type,
                analysis_plan,
                context
            )

            return {
                "agent_type": "analysis",
                "execution_success": True,
                "success": True,
                "analysis_type": analysis_type,
                "analysis_result": analysis_result,
                "analysis_plan": analysis_plan,
                "summary": f"数据分析完成: {analysis_type}"
            }

        except Exception as e:
            logger.error(f"Analysis agent execution failed: {e}", exc_info=True)
            return {
                "agent_type": "analysis",
                "execution_success": False,
                "success": False,
                "error": str(e)
            }

    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析数据分析需求

        Args:
            task_description: 任务描述
            context: 上下文信息

        Returns:
            分析计划
        """
        try:
            prompt = f"""
作为数据分析专家，分析以下数据分析需求：

任务: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **分析类型**：统计分析、趋势分析、异常检测、对比分析等
2. **分析维度**：需要从哪些维度分析？
3. **分析方法**：使用什么分析方法？
4. **输出要求**：需要什么格式的分析结果？

返回JSON格式：
{{
    "needs_analysis": true/false,
    "analysis_type": "statistical|trend|anomaly|comparison|other",
    "analysis_dimensions": ["维度1", "维度2"],
    "analysis_methods": ["方法1", "方法2"],
    "output_requirements": {{
        "format": "格式要求",
        "detail_level": "详细程度"
    }}
}}
"""

            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "analysis_agent",
                fallback="你是一个数据分析专家，擅长分析数据分析需求。"
            )

            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])

            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis_plan = json.loads(response[json_start:json_end])
                else:
                    analysis_plan = {"needs_analysis": False}
            else:
                analysis_plan = response

            return analysis_plan

        except Exception as e:
            logger.error(f"Analysis planning failed: {e}", exc_info=True)
            return {
                "needs_analysis": False,
                "error": str(e)
            }

    # 注意：新的统一接口execute()已在上面实现（继承自BaseAgent）
    # 旧的execute()方法已重命名为_execute_legacy()，通过execute_legacy()访问（向后兼容）
    async def execute_legacy(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据分析（旧接口，向后兼容）

        Args:
            input_data: 输入数据（包含data或analysis_plan）
            context: 上下文信息

        Returns:
            分析结果
        """
        return await self._execute_legacy(input_data, context)

    # 为了向后兼容，保留execute方法名，但调用新的统一接口
    # 如果调用时传入的是Dict而不是ExecutionPlan，则使用旧逻辑
    async def execute_old(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据分析（旧接口，向后兼容）
        注意：新代码应该使用统一的execute(plan, context)接口
        """
        return await self._execute_legacy(input_data, context)

    async def _perform_analysis(
        self,
        data: Any,
        analysis_type: str,
        analysis_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体的数据分析"""

        # 准备数据摘要
        data_summary = self._summarize_data(data)

        prompt = f"""
作为数据分析专家，对以下数据进行分析：

数据摘要: {json.dumps(data_summary, ensure_ascii=False, indent=2)}
分析类型: {analysis_type}
分析维度: {json.dumps(analysis_plan.get('analysis_dimensions', []), ensure_ascii=False)}
分析方法: {json.dumps(analysis_plan.get('analysis_methods', []), ensure_ascii=False)}

原始数据（前10条）: {json.dumps(
    (data.get('data', data) if isinstance(data, dict) else data)[:10] if isinstance(data, list) else [data],
    ensure_ascii=False,
    indent=2
)}

请进行深度分析，包括：
1. **统计分析**：基本统计指标（平均值、最大值、最小值、总数等）
2. **趋势分析**：如果有时间维度，分析趋势
3. **模式识别**：识别数据中的模式和规律
4. **异常检测**：识别异常值和异常模式
5. **业务洞察**：从业务角度解读数据

返回JSON格式：
{{
    "statistical_summary": {{
        "total_count": 数字,
        "key_metrics": {{"指标名": "值"}},
        "distributions": {{"分布项": "值"}}
    }},
    "trend_analysis": {{
        "has_trend": true/false,
        "trend_direction": "上升|下降|平稳",
        "trend_description": "趋势描述"
    }},
    "patterns": ["模式1", "模式2"],
    "anomalies": ["异常1", "异常2"],
    "business_insights": ["洞察1", "洞察2"],
    "recommendations": ["建议1", "建议2"]
}}
"""

        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            execute_system_prompt = get_system_prompt(
                "analysis_agent_execute",
                fallback="你是一个专业的数据分析专家，擅长深度分析数据并提供业务洞察。"
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

            # 降级：简单分析
            return {
                "statistical_summary": {
                    "total_count": len(data) if isinstance(data, list) else 1
                },
                "business_insights": ["数据已获取，需要进一步分析"]
            }

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return {
                "statistical_summary": {"total_count": 0},
                "business_insights": ["分析失败，请检查数据"]
            }

    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """总结数据特征"""
        if isinstance(data, dict):
            if "data" in data:
                data_list = data["data"]
            elif "summary" in data:
                return {"type": "summary", "content": data}
            else:
                return {"type": "dict", "keys": list(data.keys()), "sample": str(data)[:200]}
        elif isinstance(data, list):
            return {
                "type": "list",
                "count": len(data),
                "sample_count": min(5, len(data)),
                "sample": data[:5] if data else []
            }
        else:
            return {"type": "other", "content": str(data)[:200]}


