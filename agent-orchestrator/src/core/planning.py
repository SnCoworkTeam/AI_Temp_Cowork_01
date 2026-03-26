"""
任务规划引擎
"""
import logging
from typing import Dict, List, Any
import os

from ..models.plan_models import TaskDecomposition

logger = logging.getLogger(__name__)


class PlanningEngine:
    """任务规划引擎"""
    
    def __init__(self):
        self.use_llm = bool(os.getenv("OPENAI_API_KEY"))
        if self.use_llm:
            try:
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage
                
                api_key = os.getenv("OPENAI_API_KEY")
                base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/v1").rstrip("/")
                model = os.getenv("LLM_MODEL", "deepseek-chat")
                
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.3,
                    api_key=api_key,
                    base_url=base_url,
                )
                logger.info("PlanningEngine LLM initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM for planning: {str(e)}")
                self.use_llm = False
                self.llm = None
        else:
            self.llm = None
    
    async def decompose_task(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> TaskDecomposition:
        """
        分解任务为子任务
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            任务分解结果
        """
        if self.use_llm and self.llm:
            return await self._decompose_with_llm(task, context)
        else:
            return await self._decompose_simple(task, context)
    
    async def _decompose_with_llm(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> TaskDecomposition:
        """使用LLM分解任务"""
        try:
            from langchain.schema import HumanMessage, SystemMessage
            
            prompt = f"""请将以下任务分解为3-5个子任务，每个子任务需要明确：
1. 任务名称
2. 任务描述
3. 需要的智能体能力（从以下选择：data_analysis, document_processing, workflow_orchestration, code_generation, knowledge_retrieval, conversation, task_planning）
4. 执行参数

任务：{task}

请以JSON格式返回，格式如下：
{{
  "subtasks": [
    {{
      "name": "子任务名称",
      "description": "子任务描述",
      "task": "具体任务内容",
      "capabilities": ["需要的能力"],
      "parameters": {{}}
    }}
  ],
  "dependencies": {{
    "step_2": ["step_1"],
    "step_3": ["step_1", "step_2"]
  }}
}}"""
            
            messages = [
                SystemMessage(content="你是一个专业的任务分解专家，擅长将复杂任务分解为可执行的子任务。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            # 解析JSON（简化版本，实际应该更健壮）
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group(0))
            else:
                raise ValueError("No JSON found in LLM response")
            
            subtasks = []
            for i, subtask_data in enumerate(result_dict.get("subtasks", []), 1):
                subtask_data["step_id"] = f"step_{i}"
                subtasks.append(subtask_data)
            
            dependencies = result_dict.get("dependencies", {})
            
            return TaskDecomposition(
                task=task,
                subtasks=subtasks,
                dependencies=dependencies
            )
        except Exception as e:
            logger.error(f"LLM decomposition failed: {str(e)}", exc_info=True)
            return await self._decompose_simple(task, context)
    
    async def _decompose_simple(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> TaskDecomposition:
        """简单任务分解（不使用LLM）"""
        # 简单的启发式分解
        subtasks = [
            {
                "step_id": "step_1",
                "name": "任务分析",
                "description": "分析任务需求",
                "task": f"分析任务：{task}",
                "capabilities": ["task_planning"],
                "parameters": {}
            },
            {
                "step_id": "step_2",
                "name": "任务执行",
                "description": "执行主要任务",
                "task": task,
                "capabilities": [],
                "parameters": {}
            },
            {
                "step_id": "step_3",
                "name": "结果汇总",
                "description": "汇总执行结果",
                "task": f"汇总任务结果：{task}",
                "capabilities": ["task_planning"],
                "parameters": {}
            }
        ]
        
        dependencies = {
            "step_2": ["step_1"],
            "step_3": ["step_2"]
        }
        
        return TaskDecomposition(
            task=task,
            subtasks=subtasks,
            dependencies=dependencies
        )

