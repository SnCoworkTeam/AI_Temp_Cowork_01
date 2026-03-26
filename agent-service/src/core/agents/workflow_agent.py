"""
工作流智能体
管理和执行复杂业务流程
"""
import logging
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class WorkflowAgent(IntelligentAgent):
    """工作流智能体 - 管理和执行复杂业务流程"""
    
    def __init__(self, workflow_engine=None):
        """
        初始化工作流智能体
        
        Args:
            workflow_engine: Workflow Engine客户端（可选，默认使用service_clients）
        """
        super().__init__(
            agent_id="workflow_agent",
            name="工作流智能体",
            description="管理和执行复杂业务流程，包括工作流编排、执行监控、状态管理、故障恢复",
            capabilities={
                "workflow_orchestration": "工作流编排",
                "execution_monitoring": "执行监控",
                "state_management": "状态管理",
                "recovery_handling": "故障恢复"
            }
        )
        # 延迟导入避免循环依赖
        if workflow_engine is None:
            from ..service_clients import service_clients
            self.workflow_engine = service_clients.workflow_engine
        else:
            self.workflow_engine = workflow_engine
        self.llm = deepseek_llm
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务是否需要工作流执行
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            工作流执行决策
        """
        try:
            # 获取可用工作流列表
            try:
                available_workflows = await self.workflow_engine.list_workflows()
            except Exception as e:
                logger.warning(f"Failed to list workflows: {e}")
                available_workflows = []
            
            prompt = f"""
作为工作流专家，判断这个任务是否需要工作流执行：

任务: {task_description}
可用工作流: {json.dumps(available_workflows[:10], ensure_ascii=False, indent=2)}  # 限制数量
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **复杂度评估**：是否适合工作流执行？
2. **工作流选择**：哪个工作流最合适？
3. **参数映射**：如何映射任务参数到工作流参数？
4. **执行监控**：需要什么监控和反馈？

返回JSON格式：
{{
    "needs_workflow": true/false,
    "selected_workflow": "工作流名称或ID",
    "workflow_parameters": {{"参数名": "参数值"}},
    "execution_strategy": "sync|async",
    "monitoring": {{
        "track_progress": true/false,
        "send_notifications": true/false
    }},
    "reasoning": "决策理由"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "workflow_agent",
                fallback="你是一个工作流专家，擅长判断任务是否需要工作流执行。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            
            # 解析响应
            if isinstance(response, str):
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    decision = json.loads(response[json_start:json_end])
                else:
                    decision = {
                        "needs_workflow": False,
                        "reason": "Failed to parse LLM response"
                    }
            else:
                decision = response
            
            return decision
            
        except Exception as e:
            logger.error(f"Workflow analysis failed: {e}", exc_info=True)
            return {
                "needs_workflow": False,
                "error": str(e)
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            input_data: 输入数据（包含task或workflow_decision）
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            # 获取工作流决策
            task_description = input_data.get("task", "")
            workflow_decision = input_data.get("workflow_decision")
            
            if not workflow_decision:
                # 如果没有决策，先分析任务
                workflow_decision = await self.analyze_task(task_description, context)
            
            if not workflow_decision.get("needs_workflow"):
                return {
                    "agent_type": "workflow",
                    "decision": "skip_workflow",
                    "reason": workflow_decision.get("reason", "Task does not require workflow execution")
                }
            
            workflow_name = workflow_decision.get("selected_workflow")
            workflow_params = workflow_decision.get("workflow_parameters", {})
            
            if not workflow_name:
                return {
                    "agent_type": "workflow",
                    "decision": "no_workflow_selected",
                    "error": "No workflow selected in decision"
                }
            
            # 触发工作流执行
            try:
                # WorkflowClient.execute_workflow需要workflow_id和input_data
                workflow_result = await self.workflow_engine.execute_workflow(
                    workflow_name,  # workflow_id
                    {**input_data, **workflow_params}  # input_data
                )
                
                return {
                    "agent_type": "workflow",
                    "workflow_executed": workflow_name,
                    "execution_id": workflow_result.get("execution_id"),
                    "current_state": workflow_result.get("current_state"),
                    "completed_steps": workflow_result.get("completed_steps", []),
                    "next_actions": workflow_result.get("next_actions", []),
                    "execution_metrics": workflow_result.get("metrics", {}),
                    "workflow_decision": workflow_decision
                }
                
            except Exception as e:
                return await self._handle_workflow_failure(
                    workflow_name,
                    workflow_params,
                    e,
                    workflow_decision,
                    context
                )
                
        except Exception as e:
            logger.error(f"Workflow agent execution failed: {e}", exc_info=True)
            raise
    
    async def _handle_workflow_failure(
        self,
        workflow_name: str,
        workflow_params: Dict[str, Any],
        error: Exception,
        workflow_decision: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理工作流执行失败"""
        return {
            "agent_type": "workflow",
            "workflow_executed": workflow_name,
            "execution_success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "suggestion": "工作流执行失败，建议检查工作流参数或使用其他执行方式"
        }

