"""
ReAct引擎
实现思考-行动-观察循环
"""
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """行动类型"""
    TOOL_USE = "tool_use"
    PLAN = "plan"
    OBSERVE = "observe"
    FINAL = "final"


@dataclass
class Thought:
    """思考结果"""
    content: str
    should_act: bool
    action_type: Optional[ActionType] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    plan_description: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Action:
    """行动"""
    id: str
    action_type: ActionType
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    success: bool = False
    is_final: bool = False
    error: Optional[str] = None


@dataclass
class Observation:
    """观察结果"""
    action_id: str
    result: Any
    success: bool
    is_final: bool = False
    error: Optional[str] = None


class ReActEngine:
    """ReAct引擎 - 实现思考-行动-观察循环"""

    def __init__(self, llm, tool_registry=None):
        """
        初始化ReAct引擎

        Args:
            llm: LLM实例
            tool_registry: 工具注册表（可选）
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = 10

    async def react_loop(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        ReAct循环：思考-行动-观察

        Args:
            task: 任务描述
            context: 上下文信息
            max_iterations: 最大迭代次数

        Returns:
            执行结果
        """
        max_iterations = max_iterations or self.max_iterations
        context = context or {}

        observations: List[Observation] = []
        thoughts: List[Thought] = []
        actions: List[Action] = []

        for i in range(max_iterations):
            logger.info(f"ReAct循环迭代 {i+1}/{max_iterations}")

            # 1. 思考（Reasoning）
            thought = await self._think(task, observations, thoughts, actions, context)
            thoughts.append(thought)
            logger.debug(f"思考结果: {thought.content[:100]}...")

            # 2. 判断是否需要行动
            if thought.should_act:
                # 3. 行动（Acting）
                action = await self._act(thought, context)
                actions.append(action)
                logger.info(f"执行行动: {action.action_type.value}")

                # 4. 观察（Observing）
                observation = await self._observe(action)
                observations.append(observation)
                logger.debug(f"观察结果: success={observation.success}, is_final={observation.is_final}")

                # 5. 判断是否完成
                if observation.is_final:
                    logger.info("任务完成")
                    break
            else:
                # 不需要行动，直接返回结果
                logger.info("不需要进一步行动")
                break

        # 汇总结果
        return {
            "success": len(observations) > 0 and all(o.success for o in observations),
            "thoughts": [t.content for t in thoughts],
            "actions": [self._action_to_dict(a) for a in actions],
            "observations": [self._observation_to_dict(o) for o in observations],
            "iterations": len(thoughts),
            "final_result": observations[-1].result if observations else None
        }

    async def _think(
        self,
        task: str,
        observations: List[Observation],
        thoughts: List[Thought],
        actions: List[Action],
        context: Dict[str, Any]
    ) -> Thought:
        """思考下一步行动"""
        # 构建思考提示词
        prompt = self._build_think_prompt(task, observations, thoughts, actions, context)

        # 调用LLM
        response = await self.llm.chat([
            {"role": "user", "content": prompt}
        ])

        # 解析思考结果
        return self._parse_thought(response, observations, thoughts, actions)

    def _build_think_prompt(
        self,
        task: str,
        observations: List[Observation],
        thoughts: List[Thought],
        actions: List[Action],
        context: Dict[str, Any]
    ) -> str:
        """构建思考提示词"""
        prompt_parts = [
            f"任务: {task}",
            "",
            "请思考下一步应该做什么。"
        ]

        # 添加之前的思考
        if thoughts:
            prompt_parts.append("\n之前的思考:")
            for i, thought in enumerate(thoughts[-3:], 1):  # 只显示最近3个思考
                prompt_parts.append(f"{i}. {thought.content}")

        # 添加之前的行动和观察
        if actions and observations:
            prompt_parts.append("\n之前的行动和结果:")
            for action, observation in zip(actions[-3:], observations[-3:]):  # 只显示最近3个
                prompt_parts.append(f"- 行动: {action.action_type.value}")
                if observation.success:
                    prompt_parts.append(f"  结果: {str(observation.result)[:200]}")
                else:
                    prompt_parts.append(f"  错误: {observation.error}")

        # 添加可用工具
        if self.tool_registry:
            tools = self.tool_registry.list_tools()
            if tools:
                prompt_parts.append("\n可用工具:")
                for tool in tools[:10]:  # 限制工具数量
                    prompt_parts.append(f"- {tool.name}: {tool.description}")

        prompt_parts.append("\n请返回JSON格式:")
        prompt_parts.append('{"should_act": true/false, "action_type": "tool_use|plan|final", "tool_name": "...", "tool_args": {...}, "reasoning": "思考过程"}')

        return "\n".join(prompt_parts)

    def _parse_thought(
        self,
        response: str,
        observations: List[Observation],
        thoughts: List[Thought],
        actions: List[Action]
    ) -> Thought:
        """解析思考结果"""
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return Thought(
                    content=data.get("reasoning", response),
                    should_act=data.get("should_act", False),
                    action_type=ActionType(data.get("action_type", "observe")) if data.get("action_type") else None,
                    tool_name=data.get("tool_name"),
                    tool_args=data.get("tool_args"),
                    confidence=0.8
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"解析思考结果失败: {e}")

        # 如果解析失败，尝试从文本推断
        should_act = "tool" in response.lower() or "execute" in response.lower()
        return Thought(
            content=response,
            should_act=should_act,
            confidence=0.5
        )

    async def _act(self, thought: Thought, context: Dict[str, Any]) -> Action:
        """执行行动"""
        import uuid
        action_id = str(uuid.uuid4())

        try:
            if thought.action_type == ActionType.TOOL_USE and thought.tool_name:
                # 使用工具
                if not self.tool_registry:
                    raise ValueError("工具注册表未配置")

                tool = self.tool_registry.get_tool(thought.tool_name)
                if not tool:
                    raise ValueError(f"工具未找到: {thought.tool_name}")

                result = await tool.execute(**(thought.tool_args or {}))

                return Action(
                    id=action_id,
                    action_type=ActionType.TOOL_USE,
                    tool_name=thought.tool_name,
                    tool_args=thought.tool_args,
                    result=result,
                    success=True,
                    is_final=False
                )
            elif thought.action_type == ActionType.PLAN:
                # 创建计划
                return Action(
                    id=action_id,
                    action_type=ActionType.PLAN,
                    plan_description=thought.plan_description,
                    result={"plan": thought.plan_description},
                    success=True,
                    is_final=False
                )
            elif thought.action_type == ActionType.FINAL:
                # 最终结果
                return Action(
                    id=action_id,
                    action_type=ActionType.FINAL,
                    result={"message": "任务完成"},
                    success=True,
                    is_final=True
                )
            else:
                # 默认观察行动
                return Action(
                    id=action_id,
                    action_type=ActionType.OBSERVE,
                    result={"message": "观察中"},
                    success=True,
                    is_final=False
                )
        except Exception as e:
            logger.error(f"执行行动失败: {e}", exc_info=True)
            return Action(
                id=action_id,
                action_type=thought.action_type or ActionType.OBSERVE,
                result=None,
                success=False,
                is_final=False,
                error=str(e)
            )

    async def _observe(self, action: Action) -> Observation:
        """观察行动结果"""
        return Observation(
            action_id=action.id,
            result=action.result,
            success=action.success,
            is_final=action.is_final,
            error=action.error
        )

    def _action_to_dict(self, action: Action) -> Dict[str, Any]:
        """将行动转换为字典"""
        return {
            "id": action.id,
            "action_type": action.action_type.value,
            "tool_name": action.tool_name,
            "tool_args": action.tool_args,
            "success": action.success,
            "is_final": action.is_final,
            "error": action.error
        }

    def _observation_to_dict(self, observation: Observation) -> Dict[str, Any]:
        """将观察转换为字典"""
        return {
            "action_id": observation.action_id,
            "success": observation.success,
            "is_final": observation.is_final,
            "error": observation.error,
            "result": str(observation.result)[:500] if observation.result else None
        }

