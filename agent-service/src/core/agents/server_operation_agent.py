"""
服务器操作智能体
负责将用户需求转化为安全的服务器命令并执行
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
from dataclasses import dataclass, asdict
from datetime import datetime

# 延迟导入SSH执行器，避免启动时错误
import sys
import os
from pathlib import Path
from typing import Optional

SSHCommandExecutor = None
DeploymentExecutor = None
CommandResult = None

def _lazy_import_ssh():
    """延迟导入SSH执行器"""
    global SSHCommandExecutor, DeploymentExecutor, CommandResult
    if SSHCommandExecutor is None:
        try:
            # 尝试多个可能的路径
            possible_paths = [
                "/app/tools",
                "/opt/enterprise-ai-platform/tools",
                str(Path(__file__).resolve().parents[3] / "tools"),
            ]
            for tools_path in possible_paths:
                if os.path.exists(tools_path) and tools_path not in sys.path:
                    sys.path.insert(0, tools_path)
                    logger.debug(f"Added tools path to sys.path: {tools_path}")

            # 先检查paramiko是否可用
            try:
                import paramiko
                logger.debug(f"paramiko可用，版本: {paramiko.__version__}")
            except ImportError as paramiko_err:
                logger.error(f"paramiko未安装: {paramiko_err}")
                raise ImportError(f"paramiko未安装: {paramiko_err}")

            # 尝试导入
            try:
                from tools.ssh_executor import SSHCommandExecutor, DeploymentExecutor, CommandResult
                logger.info("SSH执行器导入成功")
            except ImportError as import_err:
                # 输出更详细的错误信息
                logger.error(f"导入SSH执行器失败: {import_err}")
                logger.error(f"当前sys.path: {sys.path[:5]}...")  # 只显示前5个路径
                logger.error(f"尝试的路径: {possible_paths}")
                # 检查tools目录是否存在
                for path in possible_paths:
                    exists = os.path.exists(path)
                    ssh_file = os.path.join(path, "ssh_executor.py")
                    ssh_file_exists = os.path.exists(ssh_file)
                    logger.error(f"路径 {path}: 存在={exists}, ssh_executor.py存在={ssh_file_exists}")
                raise
        except ImportError as e:
            logger.warning(f"无法导入SSH执行器: {e}，功能将不可用")
            # 创建占位类
            class SSHCommandExecutor:
                def __init__(self, *args, **kwargs):
                    raise ImportError("SSH执行器未安装或tools模块不可用")
                @property
                def connected(self):
                    return False
                def connect(self):
                    raise ImportError("SSH执行器不可用")
                def execute(self, *args, **kwargs):
                    raise ImportError("SSH执行器不可用")
                def execute_sequence(self, *args, **kwargs):
                    raise ImportError("SSH执行器不可用")
                def close(self):
                    pass
            class DeploymentExecutor(SSHCommandExecutor):
                pass
            class CommandResult:
                pass

from ..llm_integration import deepseek_llm

# 检查LANGCHAIN是否可用
try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

# 从统一基类导入ExecutionPlan和ExecutionResult
from .unified_base_agent import BaseAgent, ExecutionPlan, ExecutionResult, AgentState

# 系统提示词 - 定义智能体的角色、能力和约束
SYSTEM_PROMPT = """你是一个专业的服务器操作智能体，负责将开发需求转化为安全、可执行的服务器命令序列。

# 你的核心能力
1. 理解用户需求，将其分解为具体的服务器操作步骤
2. 生成安全的Linux Bash命令
3. 考虑命令之间的依赖关系和执行顺序
4. 输出结构化、可解析的执行计划

# 你的操作环境
- 服务器系统: Linux (Ubuntu/CentOS)
- 工作目录: /opt/enterprise-ai-platform (所有操作必须在此目录或子目录下)
- 权限: 普通用户权限，无sudo特权

# 安全约束 (必须遵守!)
- 禁止任何系统级破坏命令 (如 'rm -rf /', 'mkfs', 'dd' 等)
- 禁止安装来自非官方源的软件包
- 禁止直接操作/projects目录外的任何文件
- 禁止尝试提升权限或修改系统配置
- 单个命令执行时间限制: 30秒

# 输出格式要求
你必须以以下JSON格式输出，只输出JSON，不要额外解释：
{
  "plan_name": "任务名称",
  "description": "简要描述",
  "execution_mode": "single|sequence|dynamic",
  "commands": ["命令1", "命令2", ...],
  "expected_outcomes": ["预期结果1", "预期结果2", ...],
  "rollback_commands": ["回滚命令1", ...]  // 可选，用于失败时清理
}

# 重要原则
1. 每条命令都应该是独立可执行的
2. 考虑命令的幂等性 (重复执行不会导致错误)
3. 包含必要的错误检查
4. 对于复杂操作，优先使用现有的、安全的工具和命令
"""


class ServerOperationAgent(BaseAgent):
    """
    服务器操作智能体
    将用户需求转化为服务器命令并执行
    """

    def __init__(self,
                 ssh_config: Dict[str, Any],
                 llm_integration=None,
                 agent_config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体

        Args:
            ssh_config: SSH配置
                {
                    "host": "43.143.139.197",
                    "username": "ubuntu",
                    "private_key_path": "/path/to/key.pem",
                    "base_workdir": "/opt/enterprise-ai-platform"
                }
            llm_integration: LLM集成对象（可选，默认使用deepseek_llm的code模型）
            agent_config: 智能体配置（可选，可包含llm_model字段）
        """
        # 调用基类初始化
        super().__init__(
            agent_id=agent_config.get("agent_id", "server_operation_agent") if agent_config else "server_operation_agent",
            name="SSH服务器操作智能体",
            description="专门用于服务器操作和命令执行的智能体，通过SSH连接远程服务器执行命令",
            capabilities={
                "server_operation": "服务器操作",
                "command_execution": "命令执行",
                "task_planning": "任务规划"
            }
        )
        # 从agent_config中读取llm_model配置
        agent_model = None
        if agent_config and isinstance(agent_config, dict):
            agent_model = agent_config.get("llm_model")
            if agent_model:
                logger.info(f"从智能体配置中读取模型: {agent_model}")

        # 如果未提供LLM集成，创建专门用于代码生成的LLM实例
        if llm_integration is None:
            import os
            import asyncio
            from ..llm_integration import DeepSeekLLM

            # 创建专门的LLM实例
            # 优先使用agent_config中指定的模型，否则使用默认模型
            if agent_model:
                code_llm = DeepSeekLLM(model=agent_model)
                logger.info(f"使用智能体配置的模型: {agent_model}")
            else:
                code_llm = DeepSeekLLM()

            # 如果LLM未初始化，尝试加载配置
            if not code_llm.llm:
                logger.warning("LLM未初始化，尝试加载配置...")
                # 优先尝试同步加载（更可靠）
                try:
                    code_llm._load_config_from_env()
                    if code_llm.api_key and LANGCHAIN_AVAILABLE:
                        code_llm._init_llm()
                        logger.info("LLM通过同步方式初始化成功")
                except Exception as sync_err:
                    logger.warning(f"同步加载配置失败: {sync_err}，尝试异步加载...")
                    try:
                        # 尝试异步加载配置
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果事件循环正在运行，无法同步等待，记录警告
                            logger.warning("事件循环正在运行，无法同步初始化LLM，将在首次使用时初始化")
                        else:
                            # 如果事件循环未运行，直接运行
                            loop.run_until_complete(code_llm._load_config_async())
                            if code_llm.api_key and LANGCHAIN_AVAILABLE and not code_llm.llm:
                                code_llm._init_llm()
                            logger.info("LLM通过异步方式初始化成功")
                    except RuntimeError:
                        # 没有事件循环，再次尝试同步加载
                        logger.warning("无法异步加载配置，再次尝试同步加载...")
                        code_llm._load_config_from_env()
                        if code_llm.api_key and LANGCHAIN_AVAILABLE:
                            code_llm._init_llm()
                    except Exception as async_err:
                        logger.error(f"异步加载配置也失败: {async_err}", exc_info=True)
                        # 最后一次尝试同步加载
                        code_llm._load_config_from_env()
                        if code_llm.api_key and LANGCHAIN_AVAILABLE:
                            code_llm._init_llm()

            # 检查LLM是否已初始化
            if not code_llm.llm:
                logger.error("LLM初始化失败，检查配置...")
                logger.error(f"API Key存在: {bool(code_llm.api_key)}")
                logger.error(f"Base URL: {code_llm.base_url}")
                logger.error(f"Model: {code_llm.model}")
                logger.error(f"LANGCHAIN_AVAILABLE: {LANGCHAIN_AVAILABLE}")
                raise RuntimeError(
                    "DeepSeek LLM未初始化。请检查配置：\n"
                    f"1. OPENAI_API_KEY环境变量是否设置: {bool(os.getenv('OPENAI_API_KEY'))}\n"
                    f"2. LLM_BASE_URL环境变量是否设置: {bool(os.getenv('LLM_BASE_URL'))}\n"
                    f"3. 配置中心是否可用\n"
                    f"4. LangChain包是否已安装"
                )

            # 如果agent_config中没有指定模型，使用默认逻辑
            if not agent_model:
                # 检查当前模型，如果不是code模型，则切换
                current_model = code_llm.model or os.getenv("LLM_MODEL", "deepseek-chat")
                if current_model == "deepseek-chat":
                    # 切换到deepseek-coder模型（向后兼容）
                    code_llm.model = "deepseek-coder"
                    # 重新初始化LLM（使用code模型）
                    if code_llm.api_key and LANGCHAIN_AVAILABLE:
                        code_llm._init_llm()
                    logger.info(f"SSH智能体使用deepseek-coder模型进行代码生成")
                else:
                    logger.info(f"SSH智能体使用模型: {current_model}")

            # 再次检查LLM是否已初始化
            if not code_llm.llm:
                raise RuntimeError("LLM初始化失败，即使尝试了所有配置方法")

            self.llm = code_llm
        else:
            self.llm = llm_integration

        self.ssh_config = ssh_config
        self.executor: Optional[SSHCommandExecutor] = None

        logger.info(f"服务器操作智能体初始化完成，目标服务器: {ssh_config.get('host')}, 使用模型: {self.llm.model if hasattr(self.llm, 'model') else 'default'}")

    def _get_executor(self) -> SSHCommandExecutor:
        """获取或创建SSH执行器"""
        # 延迟导入检查
        _lazy_import_ssh()
        if SSHCommandExecutor is None:
            logger.error("SSHCommandExecutor is None after lazy import")
            raise ImportError("SSH执行器未安装或tools模块不可用")
        try:
            if self.executor is None or not self.executor.connected:
                logger.info(f"Creating SSH executor with config: host={self.ssh_config.get('host')}")
                self.executor = SSHCommandExecutor(**self.ssh_config)
                logger.info("SSH executor created, connecting...")
                self.executor.connect()
                logger.info("SSH executor connected successfully")
            return self.executor
        except Exception as e:
            logger.error(f"Failed to create or connect SSH executor: {e}", exc_info=True)
            raise

    def _close_executor(self):
        """关闭SSH执行器"""
        if self.executor:
            self.executor.close()
            self.executor = None

    def _parse_llm_response(self, response: str) -> ExecutionPlan:
        """
        解析LLM返回的执行计划

        Args:
            response: LLM返回的文本

        Returns:
            ExecutionPlan: 解析后的执行计划
        """
        try:
            # 尝试提取JSON
            response = response.strip()

            # 如果响应包含代码块，提取JSON部分
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # 解析JSON
            plan_data = json.loads(response)

            return ExecutionPlan(
                plan_name=plan_data.get("plan_name", "未命名任务"),
                description=plan_data.get("description", ""),
                execution_mode=plan_data.get("execution_mode", "sequence"),
                commands=plan_data.get("commands", []),
                expected_outcomes=plan_data.get("expected_outcomes", []),
                rollback_commands=plan_data.get("rollback_commands")
            )

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM响应失败: {e}, 响应内容: {response[:200]}")
            raise ValueError(f"无法解析执行计划: {e}")
        except Exception as e:
            logger.error(f"解析执行计划时发生错误: {e}")
            raise

    async def plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[ExecutionPlan, AsyncIterator[str]]:
        """
        规划任务（统一接口实现）

        Args:
            task: 任务描述
            context: 上下文信息（可选，可包含对话历史）

        Returns:
            ExecutionPlan: 执行计划
            或 AsyncIterator[str]: 流式输出（如果支持）
        """
        # 默认非流式，如果需要流式可以调用generate_plan
        return await self.generate_plan(task, context, stream=False)

    async def generate_plan(
        self,
        user_request: str,
        context: Optional[Dict] = None,
        stream: bool = False
    ):
        """
        根据用户需求生成执行计划（保留向后兼容）

        Args:
            user_request: 用户请求
            context: 上下文信息（可选，可包含对话历史）
            stream: 是否流式输出

        Returns:
            ExecutionPlan: 执行计划
            或 AsyncIterator[str]: 流式输出
        """
        self.set_state(AgentState.PLANNING)
        # 构建提示词
        user_prompt = f"""
用户需求: {user_request}

请根据上述需求，生成一个安全的服务器操作执行计划。
"""

        # 添加对话历史（如果有）- 限制长度以提高速度
        if context and context.get("conversation_history"):
            conversation_history = context.get("conversation_history", [])
            if conversation_history and len(conversation_history) > 0:
                # 只取最近3轮对话（6条消息），减少上下文长度
                recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                history_text = "\n\n最近的对话：\n"
                for msg in recent_history:
                    role_name = "用户" if msg.get("role") == "user" else "智能体"
                    content = msg.get('content', '')
                    # 限制每条消息长度，避免过长
                    if len(content) > 200:
                        content = content[:200] + "..."
                    history_text += f"{role_name}: {content}\n"
                user_prompt = history_text + "\n" + user_prompt

        # 添加其他上下文信息
        if context:
            other_context = {k: v for k, v in context.items() if k != "conversation_history"}
            if other_context:
                user_prompt += f"\n上下文信息: {json.dumps(other_context, ensure_ascii=False, indent=2)}"

        # 调用LLM生成计划
        try:
            # 构建消息列表（包含对话历史）
            messages_list = []

            # 如果有对话历史，构建完整的消息列表
            if context and context.get("conversation_history"):
                conversation_history = context.get("conversation_history", [])
                # 只取最近3轮对话（6条消息），减少上下文长度以提高速度
                recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                for msg in recent_history:
                    # 跳过当前消息（已经在user_prompt中）
                    if msg.get("content") != user_request:
                        messages_list.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })

            # 添加当前用户请求
            messages_list.append({"role": "user", "content": user_prompt})

            # 优先使用chat方法（async）
            if hasattr(self.llm, 'chat'):
                import asyncio
                # 检查是否是协程
                if asyncio.iscoroutinefunction(self.llm.chat):
                    chat_result = await self.llm.chat(
                        messages=messages_list if messages_list else [{"role": "user", "content": user_prompt}],
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.3,
                        stream=stream
                    )

                    if stream:
                        # 流式输出，返回生成器
                        async def stream_plan():
                            full_response = ""
                            async for chunk in chat_result:
                                full_response += chunk
                                yield chunk
                            # 流式输出完成后，解析完整响应
                            try:
                                plan = self._parse_llm_response(full_response)
                                yield f"\n\n[计划生成完成: {plan.plan_name}]"
                            except Exception as e:
                                logger.error(f"解析流式响应失败: {e}")
                                yield f"\n\n[错误: 无法解析执行计划]"
                        return stream_plan()
                    else:
                        response = chat_result
                else:
                    response = self.llm.chat(
                        messages=messages_list if messages_list else [{"role": "user", "content": user_prompt}],
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.3
                    )
            elif hasattr(self.llm, 'invoke'):
                # 使用LangChain的invoke方式
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt)
                ]
                response_obj = self.llm.invoke(messages)
                response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            elif hasattr(self.llm, 'generate'):
                # 尝试generate方法（同步）
                response = self.llm.generate(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.3,
                    max_tokens=2000
                )
            else:
                # 尝试直接调用
                response = str(self.llm(user_prompt))

            # 如果是流式输出，已经返回生成器，不需要继续处理
            if stream:
                return response

            logger.info(f"LLM生成执行计划: {response[:200]}...")

            # 解析响应
            plan = self._parse_llm_response(response)

            logger.info(f"执行计划生成成功: {plan.plan_name}, 包含 {len(plan.commands)} 条命令")
            self.set_state(AgentState.IDLE)
            return plan

        except Exception as e:
            logger.error(f"生成执行计划失败: {e}")
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
        project_id = context.get("project_id") if context else None
        # execute_plan是同步方法，但execute是异步接口，所以需要包装
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute_plan, plan, project_id)

    def execute_plan(self, plan: ExecutionPlan, project_id: Optional[str] = None) -> ExecutionResult:
        """
        执行计划

        Args:
            plan: 执行计划
            project_id: 项目ID（可选）

        Returns:
            ExecutionResult: 执行结果
        """
        self.set_state(AgentState.EXECUTING)
        executor = self._get_executor()

        try:
            results = []

            if plan.execution_mode == "single" and len(plan.commands) > 0:
                # 单命令模式
                result = executor.execute(plan.commands[0], project_id)
                results.append({
                    "command": result.command,
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.success,
                    "duration": result.duration
                })

            elif plan.execution_mode == "sequence":
                # 序列执行模式
                command_results = executor.execute_sequence(
                    plan.commands,
                    project_id,
                    stop_on_failure=True
                )

                for result in command_results:
                    results.append({
                        "command": result.command,
                        "exit_code": result.exit_code,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.success,
                        "duration": result.duration
                    })

            else:
                # 动态模式 - 根据前一个命令的结果决定下一个命令
                for cmd in plan.commands:
                    result = executor.execute(cmd, project_id)
                    results.append({
                        "command": result.command,
                        "exit_code": result.exit_code,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.success,
                        "duration": result.duration
                    })

                    # 如果失败，停止执行
                    if not result.success:
                        break

            # 统计结果
            success_count = sum(1 for r in results if r.get("success", False))
            total_count = len(results)
            all_success = success_count == total_count

            # 如果失败且有回滚命令，执行回滚
            if not all_success and plan.rollback_commands:
                logger.warning("执行失败，开始执行回滚命令")
                for rollback_cmd in plan.rollback_commands:
                    try:
                        executor.execute(rollback_cmd, project_id)
                    except Exception as e:
                        logger.error(f"回滚命令执行失败: {rollback_cmd}, 错误: {e}")

            result = ExecutionResult(
                plan_name=plan.plan_name,
                success=all_success,
                commands_executed=total_count,
                commands_succeeded=success_count,
                results=results,
                summary=f"执行了 {total_count} 条命令，成功 {success_count} 条"
            )
            self.set_state(AgentState.COMPLETED if all_success else AgentState.FAILED)
            self.execution_count += 1
            if all_success:
                self.success_count += 1
            else:
                self.failure_count += 1
            self.last_executed_at = datetime.utcnow()
            return result

        except Exception as e:
            logger.error(f"执行计划失败: {e}")
            self.set_state(AgentState.FAILED)
            self.execution_count += 1
            self.failure_count += 1
            self.last_executed_at = datetime.utcnow()
            return ExecutionResult(
                plan_name=plan.plan_name,
                success=False,
                commands_executed=0,
                commands_succeeded=0,
                results=[],
                error=str(e),
                summary=f"执行失败: {e}"
            )

    async def process_request(self,
                       user_request: str,
                       project_id: Optional[str] = None,
                       context: Optional[Dict] = None,
                       auto_execute: bool = True) -> Dict[str, Any]:
        """
        处理用户请求（生成计划并执行）

        Args:
            user_request: 用户请求
            project_id: 项目ID（可选）
            context: 上下文信息（可选）
            auto_execute: 是否自动执行（如果为False，只生成计划不执行）

        Returns:
            处理结果
        """
        try:
            # 生成执行计划
            plan = await self.generate_plan(user_request, context)

            result = {
                "plan": asdict(plan),
                "executed": False,
                "execution_result": None
            }

            # 如果自动执行
            if auto_execute:
                execution_result = self.execute_plan(plan, project_id)
                result["executed"] = True
                result["execution_result"] = asdict(execution_result)

            return result

        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {
                "error": str(e),
                "plan": None,
                "executed": False,
                "execution_result": None
            }
        finally:
            # 关闭连接
            self._close_executor()

    def __del__(self):
        """析构函数，确保连接关闭"""
        self._close_executor()

