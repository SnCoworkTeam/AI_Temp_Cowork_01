"""
智能体管理器
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..models.agent_models import Agent, AgentCreate, AgentUpdate, AgentStatus, AgentCapability
from .llm_integration import deepseek_llm
from .conversation_agent import conversation_agent
from .task_classifier import task_classifier, ExecutionStrategy
from .service_integration import service_integration
from .state_manager import state_manager, ExecutionState
from ..services.metadata_client import metadata_client

logger = logging.getLogger(__name__)

# 数据库持久化（可选）
try:
    from database.src.core.session import init_session_factory, SessionLocal
    from database.src.models.agent_definition import AgentDefinition
    _AGENT_DB_AVAILABLE = True
    _AGENT_DB_IMPORT_ERROR = None
except Exception as e:
    _AGENT_DB_AVAILABLE = False
    _AGENT_DB_IMPORT_ERROR = e
    SessionLocal = None  # type: ignore
    AgentDefinition = None  # type: ignore


class AgentManager:
    """智能体管理器"""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._db_available = False
        self._init_db()

        if self._db_available:
            loaded = self._load_agents_from_db()
            if not loaded:
                self._initialize_default_agents(persist=True)
        else:
            self._initialize_default_agents()

    def _init_db(self) -> None:
        """初始化数据库会话工厂（可选）"""
        if not _AGENT_DB_AVAILABLE:
            if _AGENT_DB_IMPORT_ERROR:
                logger.warning(f"Agent DB modules not available: {_AGENT_DB_IMPORT_ERROR}")
            return

        try:
            init_session_factory()
            self._db_available = True
            logger.info("Agent DB session factory initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize agent DB session factory: {e}")
            self._db_available = False

    def _load_agents_from_db(self) -> bool:
        """从数据库加载智能体"""
        if not self._db_available:
            return False

        try:
            db = SessionLocal()
        except Exception as e:
            logger.warning(f"Failed to create DB session for agents: {e}")
            self._db_available = False
            return False

        try:
            rows = db.query(AgentDefinition).all()
            if not rows:
                logger.info("No agents found in database")
                return False

            for row in rows:
                agent = self._row_to_agent(row)
                self._agents[agent.id] = agent

            logger.info(f"Loaded {len(rows)} agents from database")
            return True
        except Exception as e:
            logger.warning(f"Failed to load agents from database: {e}")
            self._db_available = False
            return False
        finally:
            db.close()

    def _normalize_capabilities(self, capabilities: Optional[List[Any]]) -> List[str]:
        """将能力列表序列化为字符串列表"""
        if not capabilities:
            return []
        normalized = []
        for cap in capabilities:
            if isinstance(cap, str):
                normalized.append(cap)
            elif hasattr(cap, "value"):
                normalized.append(cap.value)
            else:
                normalized.append(str(cap))
        return normalized

    def _normalize_status(self, status: Any) -> str:
        """将状态规范化为字符串"""
        if hasattr(status, "value"):
            return status.value
        return str(status)

    def _row_to_agent(self, row: Any) -> Agent:
        """将数据库行转换为Agent对象"""
        return Agent(
            id=row.id,
            name=row.name,
            description=row.description,
            capabilities=row.capabilities or [],
            system_prompt=row.system_prompt,
            config=row.config or {},
            metadata=row.agent_metadata or {},
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
        )

    def _persist_agent_to_db(self, agent: Agent, allow_create: bool = True) -> None:
        """写入/更新智能体到数据库"""
        if not self._db_available:
            return

        db = SessionLocal()
        try:
            row = db.query(AgentDefinition).filter(AgentDefinition.id == agent.id).first()
            if row:
                row.name = agent.name
                row.description = agent.description
                row.capabilities = self._normalize_capabilities(agent.capabilities)
                row.system_prompt = agent.system_prompt
                row.config = agent.config or {}
                row.agent_metadata = agent.metadata or {}
                row.status = self._normalize_status(agent.status)
                row.updated_at = agent.updated_at
                row.created_by = agent.created_by
            else:
                if not allow_create:
                    raise ValueError(f"Agent not found in database: {agent.id}")
                row = AgentDefinition(
                    id=agent.id,
                    name=agent.name,
                    description=agent.description,
                    capabilities=self._normalize_capabilities(agent.capabilities),
                    system_prompt=agent.system_prompt,
                    config=agent.config or {},
                    agent_metadata=agent.metadata or {},
                    status=self._normalize_status(agent.status),
                    created_at=agent.created_at,
                    updated_at=agent.updated_at,
                    created_by=agent.created_by,
                )
                db.add(row)

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _initialize_default_agents(self, persist: bool = False):
        """初始化默认智能体"""
        default_agents = [
            {
                "name": "数据分析智能体",
                "description": "专门用于数据分析和图表生成的智能体",
                "capabilities": [AgentCapability.DATA_ANALYSIS],
                "system_prompt": "你是一个专业的数据分析专家，擅长分析数据、生成图表和报告。",
            },
            {
                "name": "文档处理智能体",
                "description": "专门用于文档解析、摘要和内容提取的智能体",
                "capabilities": [AgentCapability.DOCUMENT_PROCESSING],
                "system_prompt": "你是一个专业的文档处理专家，擅长解析文档、生成摘要和提取关键信息。",
            },
            {
                "name": "工作流编排智能体",
                "description": "专门用于工作流规划和任务编排的智能体",
                "capabilities": [AgentCapability.WORKFLOW_ORCHESTRATION, AgentCapability.TASK_PLANNING],
                "system_prompt": "你是一个专业的工作流编排专家，擅长将复杂任务分解为可执行的工作流。",
            },
            {
                "name": "SAP查询智能体",
                "description": "专门用于SAP ERP数据查询和分析的智能体，通过sap-odata-to-mcp-server（MCP服务名：sap-mcp-server）访问SAP系统",
                "capabilities": [AgentCapability.DATA_ANALYSIS],
                "system_prompt": """你是一个专业的SAP ERP数据查询和分析专家。

你的主要职责：
1. 通过MCP工具（sap_query）查询SAP系统中的各种业务数据
2. 理解用户的自然语言查询需求，自动转换为合适的SAP查询
3. 对查询结果进行深入分析，提供业务洞察和建议

技术架构：
- MCP服务：sap-odata-to-mcp-server（服务名：sap-mcp-server）
- 通过MCP Gateway调用SAP OData服务
- 支持OData查询参数（$filter, $top, $skip等）

可查询的数据类型：
- 销售订单（I_SalesOrder）：包括订单号、客户、日期、金额、状态等
- 采购订单：包括订单号、供应商、日期、金额等
- 物料主数据：包括物料号、描述、价格等
- 客户主数据：包括客户号、名称、地址等
- 供应商主数据：包括供应商号、名称等

查询能力：
- 支持自然语言查询，如"查询9月份的销售订单"
- 支持日期范围过滤，如"查询2024年9月的订单"
- 支持条件过滤，如"查询金额大于10000的订单"
- 自动解析日期条件（如"9月份"、"上个月"等）

分析能力：
- 数据概览和统计
- 趋势分析
- 异常识别
- 业务建议

使用MCP工具：
- 工具名称：sap_query
- MCP服务器：sap-mcp-server（对应sap-odata-to-mcp-server）
- 参数：table（表名，如I_SalesOrder）、query（查询条件）

请始终使用sap_query工具来查询SAP数据，不要直接回答假设的数据。""",
                "config": {
                    "preferred_tools": ["sap_query"],
                    "use_tool_integration": True,
                    "auto_analysis": True,
                    "default_table": "I_SalesOrder"
                },
                "metadata": {
                    "mcp_server": "sap-mcp-server",
                    "mcp_server_project": "sap-odata-to-mcp-server",
                    "integration_type": "mcp_tool",
                    "version": "1.0.0"
                }
            },
            {
                "name": "SSH服务器操作智能体",
                "description": "专门用于服务器操作和命令执行的智能体，通过SSH连接远程服务器执行命令",
                "capabilities": [AgentCapability.SERVER_OPERATION, AgentCapability.TASK_PLANNING],
                "system_prompt": """你是一个专业的服务器操作智能体，负责将开发需求转化为安全、可执行的服务器命令序列。

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
4. 对于复杂操作，优先使用现有的、安全的工具和命令""",
                "config": {
                    "use_tool_integration": False,
                    "auto_execute": True,
                    "ssh_enabled": True,
                    "agent_type": "server_operation"
                },
                "metadata": {
                    "integration_type": "ssh_executor",
                    "api_endpoint": "/server-operation/execute",
                    "version": "1.0.0"
                }
            },
        ]

        for agent_data in default_agents:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=agent_data["name"],
                description=agent_data["description"],
                capabilities=agent_data["capabilities"],
                system_prompt=agent_data.get("system_prompt"),
                config=agent_data.get("config", {}),
                metadata=agent_data.get("metadata", {}),
                status=AgentStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            if persist and self._db_available:
                try:
                    self._persist_agent_to_db(agent)
                except Exception as e:
                    logger.warning(f"Failed to persist default agent {agent.name}: {e}")

            self._agents[agent.id] = agent
            logger.info(f"Initialized default agent: {agent.name} ({agent.id})")

    async def create_agent(self, agent_data: AgentCreate, created_by: Optional[str] = None) -> Agent:
        """
        创建智能体

        Args:
            agent_data: 智能体创建数据
            created_by: 创建者ID

        Returns:
            创建的智能体
        """
        agent = Agent(
            id=str(uuid.uuid4()),
            name=agent_data.name,
            description=agent_data.description,
            capabilities=agent_data.capabilities,
            system_prompt=agent_data.system_prompt,
            config=agent_data.config,
            metadata=agent_data.metadata,
            status=AgentStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=created_by,
        )

        if self._db_available:
            db = SessionLocal()
            try:
                existing = db.query(AgentDefinition).filter(AgentDefinition.name == agent.name).first()
                if existing:
                    raise ValueError(f"Agent name already exists: {agent.name}")
            finally:
                db.close()

            try:
                self._persist_agent_to_db(agent)
            except Exception as e:
                logger.error(f"Failed to persist agent {agent.name} to database: {e}", exc_info=True)
                raise

        self._agents[agent.id] = agent
        logger.info(f"Created agent: {agent.name} ({agent.id})")

        # 注册到metadata-service（同时注册为AI模型和业务实体）
        try:
            # 处理capabilities：可能是枚举对象或字符串
            def get_capability_value(cap):
                if isinstance(cap, str):
                    return cap
                elif hasattr(cap, 'value'):
                    return cap.value
                else:
                    return str(cap)

            capabilities_list = [get_capability_value(cap) for cap in agent.capabilities]
            status_value = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)

            # 注册为AI模型
            await metadata_client.register_agent_as_ai_model(
                agent.id,
                agent.name,
                agent.description,
                capabilities_list,
                agent.config or {},
                agent.metadata or {},
                status_value
            )
            # 同时注册为业务实体，方便在元数据管理页面查看
            await metadata_client.register_agent_as_business_entity(
                agent.id,
                agent.name,
                agent.description,
                capabilities_list,
                agent.config or {},
                agent.metadata or {},
                status_value
            )
        except Exception as e:
            logger.warning(f"Failed to register agent {agent.id} to metadata service: {e}")

        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取智能体"""
        return self._agents.get(agent_id)

    async def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        capability: Optional[AgentCapability] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Agent]:
        """
        列出智能体

        Args:
            status: 状态过滤
            capability: 能力过滤
            limit: 限制数量
            offset: 偏移量

        Returns:
            智能体列表
        """
        agents = list(self._agents.values())

        # 状态过滤
        if status:
            agents = [a for a in agents if a.status == status]

        # 能力过滤
        if capability:
            agents = [a for a in agents if capability in a.capabilities]

        # 排序（按更新时间倒序）
        agents.sort(key=lambda x: x.updated_at, reverse=True)

        # 分页
        return agents[offset:offset + limit]

    async def update_agent(self, agent_id: str, agent_data: AgentUpdate) -> Optional[Agent]:
        """
        更新智能体

        Args:
            agent_id: 智能体ID
            agent_data: 更新数据

        Returns:
            更新后的智能体
        """
        agent = self._agents.get(agent_id)
        if not agent and self._db_available:
            db = SessionLocal()
            try:
                row = db.query(AgentDefinition).filter(AgentDefinition.id == agent_id).first()
                if row:
                    agent = self._row_to_agent(row)
                    self._agents[agent_id] = agent
            finally:
                db.close()

        if not agent:
            return None

        # 更新字段
        update_data = agent_data.dict(exclude_unset=True)
        updated_agent = agent.copy(deep=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(updated_agent, key, value)

        updated_agent.updated_at = datetime.utcnow()

        if self._db_available:
            if "name" in update_data and update_data.get("name"):
                db = SessionLocal()
                try:
                    existing = db.query(AgentDefinition).filter(
                        AgentDefinition.name == updated_agent.name,
                        AgentDefinition.id != agent_id
                    ).first()
                    if existing:
                        raise ValueError(f"Agent name already exists: {updated_agent.name}")
                finally:
                    db.close()

            try:
                self._persist_agent_to_db(updated_agent, allow_create=True)
            except Exception as e:
                logger.error(f"Failed to persist agent {updated_agent.name} update: {e}", exc_info=True)
                raise

        self._agents[agent_id] = updated_agent
        logger.info(f"Updated agent: {updated_agent.name} ({updated_agent.id})")

        # 更新metadata-service中的元数据
        try:
            capabilities_list = self._normalize_capabilities(updated_agent.capabilities)
            status_value = updated_agent.status.value if hasattr(updated_agent.status, "value") else str(updated_agent.status)
            await metadata_client.update_agent_metadata(
                updated_agent.id,
                updated_agent.name,
                updated_agent.description,
                capabilities_list,
                updated_agent.config or {},
                updated_agent.metadata or {},
                status_value
            )
        except Exception as e:
            logger.warning(f"Failed to update agent {updated_agent.id} metadata in metadata service: {e}")

        return updated_agent

    async def delete_agent(self, agent_id: str) -> bool:
        """
        删除智能体

        Args:
            agent_id: 智能体ID

        Returns:
            是否成功删除
        """
        if self._db_available:
            db = SessionLocal()
            try:
                row = db.query(AgentDefinition).filter(AgentDefinition.id == agent_id).first()
                if row:
                    db.delete(row)
                    db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to delete agent {agent_id} from database: {e}", exc_info=True)
                return False
            finally:
                db.close()

        if agent_id in self._agents:
            agent = self._agents[agent_id]
            del self._agents[agent_id]
            logger.info(f"Deleted agent: {agent.name} ({agent.id})")
            return True
        return False

    async def execute_agent(
        self,
        agent_id: str,
        task: str,
        context: Dict = None,
        parameters: Dict = None
    ) -> Dict:
        """
        执行智能体

        Args:
            agent_id: 智能体ID
            task: 任务描述
            context: 上下文信息
            parameters: 执行参数

        Returns:
            执行结果
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        if agent.status != AgentStatus.ACTIVE:
            raise ValueError(f"Agent is not active: {agent.status}")

        context = context or {}
        parameters = parameters or {}

        # 检查智能体类型和配置
        agent_config = agent.config or {}
        agent_metadata = agent.metadata or {}
        agent_type = agent_config.get("agent_type") or agent_metadata.get("integration_type")

        # 如果是SSH/服务器操作智能体，使用专门的执行逻辑
        if agent_type == "server_operation" or agent_type == "ssh_executor":
            logger.info(f"Agent {agent.name} is server operation agent, using ServerOperationAgent")
            try:
                from .agents.server_operation_agent import ServerOperationAgent
                import os

                # 从配置或环境变量读取SSH配置
                ssh_config = {
                    "host": os.getenv("SSH_HOST", "43.143.139.197"),
                    "username": os.getenv("SSH_USERNAME", "ubuntu"),
                    "private_key_path": os.getenv("SSH_PRIVATE_KEY_PATH", "/opt/enterprise-ai-platform/enterprise_ai_platform.pem"),
                    "base_workdir": os.getenv("SSH_BASE_WORKDIR", "/opt/enterprise-ai-platform"),
                    "port": int(os.getenv("SSH_PORT", "22")),
                    "connection_timeout": int(os.getenv("SSH_CONNECTION_TIMEOUT", "30"))
                }

                # 从智能体配置中获取agent_config
                agent_config = agent.config or {}
                # 创建ServerOperationAgent实例，传入agent_config以支持模型配置
                # 确保agent_config包含必要的配置
                if not agent_config:
                    agent_config = {}
                # 如果智能体配置中有llm_model，传递给ServerOperationAgent
                if agent.config and isinstance(agent.config, dict):
                    agent_config = {**agent_config, **agent.config}

                server_agent = ServerOperationAgent(
                    ssh_config=ssh_config,
                    agent_config=agent_config
                )

                # 使用统一接口：plan_and_execute
                # 保持向后兼容：如果支持统一接口，使用统一接口；否则使用旧接口
                if hasattr(server_agent, 'plan_and_execute'):
                    result = await server_agent.plan_and_execute(
                        task=task,
                        context=context,
                        auto_execute=True,
                        stream=False
                    )
                else:
                    # 向后兼容：使用旧接口
                    result = await server_agent.process_request(
                        user_request=task,
                        project_id=context.get("project_id"),
                        context=context,
                        auto_execute=True
                    )

                # 处理统一接口返回格式
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "output": result.get("error", "执行失败"),
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                    }

                # 构建响应（兼容统一接口和旧接口）
                execution_result = result.get("execution_result")
                if execution_result:
                    # 格式化输出
                    output_parts = []
                    if execution_result.get("summary"):
                        output_parts.append(f"执行摘要: {execution_result['summary']}")

                    if execution_result.get("results"):
                        output_parts.append("\n执行详情:")
                        for i, cmd_result in enumerate(execution_result["results"], 1):
                            output_parts.append(f"\n命令 {i}: {cmd_result.get('command', 'N/A')}")
                            if cmd_result.get("stdout"):
                                output_parts.append(f"输出: {cmd_result['stdout']}")
                            if cmd_result.get("stderr"):
                                output_parts.append(f"错误: {cmd_result['stderr']}")
                            output_parts.append(f"状态: {'成功' if cmd_result.get('success') else '失败'}")

                    output = "\n".join(output_parts) if output_parts else "执行完成"
                else:
                    output = "计划已生成，但未执行"

                return {
                    "success": execution_result.get("success", False) if execution_result else False,
                    "output": output,
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "plan": result.get("plan"),
                    "execution_result": execution_result
                }
            except Exception as e:
                logger.error(f"Server operation agent execution failed: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "output": f"执行失败: {str(e)}",
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                }

        # 检查智能体是否配置了MCP工具集成
        preferred_tools = agent_config.get("preferred_tools", [])
        use_tool_integration = agent_config.get("use_tool_integration", False)

        # 如果智能体配置了工具集成，使用编排引擎执行（支持工具调用）
        if use_tool_integration or preferred_tools:
            logger.info(f"Agent {agent.name} configured for tool integration, using orchestration engine")
            # 使用编排引擎执行，支持工具调用
            from .orchestration_engine import orchestration_engine

            # 构建上下文，包含可用工具信息
            execution_context = {
                **context,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "preferred_tools": preferred_tools,
                "available_tools": preferred_tools  # 告诉编排引擎可用的工具
            }

            # 使用编排引擎执行任务
            result = await orchestration_engine.orchestrate_request(
                user_input=task,
                context=execution_context
            )

            return {
                "success": result.get("success", False),
                "output": result.get("final_response") or result.get("output", ""),
                "agent_id": agent_id,
                "agent_name": agent.name,
                "execution_path": result.get("execution_path", []),
                "raw_result": result
            }

        # 尝试使用统一接口（如果智能体继承BaseAgent）
        from .agents.unified_base_agent import BaseAgent
        if isinstance(agent, BaseAgent) or hasattr(agent, 'plan_and_execute'):
            try:
                logger.info(f"Agent {agent.name} supports unified interface, using plan_and_execute")
                result = await agent.plan_and_execute(
                    task=task,
                    context=context,
                    auto_execute=True,
                    stream=False
                )

                # 统一接口返回格式
                if isinstance(result, dict):
                    execution_result = result.get("execution_result")
                    if execution_result:
                        output_parts = []
                        if execution_result.get("summary"):
                            output_parts.append(execution_result["summary"])
                        if execution_result.get("results"):
                            for r in execution_result["results"]:
                                if isinstance(r, dict):
                                    output_parts.append(str(r))
                        output = "\n".join(output_parts) if output_parts else "执行完成"
                    else:
                        output = "计划已生成，但未执行"

                    return {
                        "success": execution_result.get("success", False) if execution_result else False,
                        "output": output,
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "plan": result.get("plan"),
                        "execution_result": execution_result
                    }
            except Exception as e:
                logger.warning(f"Unified interface failed for {agent.name}, falling back to legacy: {e}")

        # 尝试使用适配器（如果智能体是IntelligentAgent）
        from .agents.base_agent import IntelligentAgent
        from .agents.agent_adapter_unified import AgentAdapter
        try:
            # 检查是否可以通过适配器使用
            if hasattr(agent, 'analyze_task') and hasattr(agent, 'execute'):
                # 创建适配器
                adapter = AgentAdapter(agent)
                result = await adapter.plan_and_execute(
                    task=task,
                    context=context,
                    auto_execute=True,
                    stream=False
                )

                execution_result = result.get("execution_result")
                if execution_result:
                    output = execution_result.get("summary", "执行完成")
                else:
                    output = "计划已生成，但未执行"

                return {
                    "success": execution_result.get("success", False) if execution_result else False,
                    "output": output,
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "plan": result.get("plan"),
                    "execution_result": execution_result
                }
        except Exception as e:
            logger.warning(f"Adapter failed for {agent.name}, falling back to LLM: {e}")

        # 否则使用传统的LLM直接调用
        # 构建消息
        messages = [
            {"role": "user", "content": task}
        ]

        # 如果有上下文，添加到消息中
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.insert(0, {"role": "system", "content": f"上下文信息:\n{context_str}"})

        # 调用DeepSeek LLM
        try:
            response = await deepseek_llm.chat(
                messages=messages,
                system_prompt=agent.system_prompt,
                temperature=parameters.get("temperature", 0.7)
            )

            return {
                "success": True,
                "output": response,
                "agent_id": agent_id,
                "agent_name": agent.name,
            }
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "agent_name": agent.name,
            }

    async def intelligent_chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能对话处理
        自动理解意图、分类任务、路由到合适的服务

        Args:
            message: 用户消息
            conversation_history: 对话历史
            user_context: 用户上下文

        Returns:
            执行结果
        """
        # 创建执行记录
        execution_id = await state_manager.create_execution(
            task=message,
            context=user_context
        )

        try:
            # 更新状态为运行中
            await state_manager.update_execution_state(
                execution_id,
                ExecutionState.RUNNING
            )
            # 步骤1: 对话理解
            intent_analysis = await conversation_agent.understand_conversation(
                message, conversation_history, user_context
            )

            logger.info(
                f"Intent analysis: type={intent_analysis.task_type.value}, "
                f"confidence={intent_analysis.confidence:.2f}"
            )

            # 步骤2: 任务分类和路由决策
            available_agents = await self.list_agents(status=AgentStatus.ACTIVE)
            agents_dict = [{"id": a.id, "name": a.name, "capabilities": a.capabilities} for a in available_agents]

            routing_decision = await task_classifier.classify_and_route(
                intent_analysis, agents_dict
            )

            logger.info(
                f"Routing decision: strategy={routing_decision.strategy.value}, "
                f"target_service={routing_decision.target_service}"
            )

            # 步骤3: 执行任务
            if routing_decision.strategy == ExecutionStrategy.DIRECT_LLM:
                # 直接使用LLM
                if routing_decision.target_agent_id:
                    result = await self.execute_agent(
                        routing_decision.target_agent_id,
                        message,
                        user_context
                    )
                else:
                    # 使用默认LLM
                    response = await deepseek_llm.chat(
                        messages=[{"role": "user", "content": message}],
                        system_prompt="你是一个有用的AI助手。"
                    )
                    result = {
                        "success": True,
                        "output": response,
                        "strategy": "direct_llm"
                    }
            else:
                # 使用服务集成层执行
                result = await service_integration.execute_routing_decision(
                    routing_decision,
                    message,
                    user_context
                )
                result["strategy"] = routing_decision.strategy.value
                result["routing_decision"] = routing_decision.reasoning

            # 添加元数据
            result["intent_analysis"] = {
                "task_type": intent_analysis.task_type.value,
                "confidence": intent_analysis.confidence,
                "reasoning": intent_analysis.reasoning
            }
            result["execution_id"] = execution_id

            # 更新执行状态
            final_state = ExecutionState.COMPLETED if result.get("success") else ExecutionState.FAILED
            await state_manager.update_execution_state(
                execution_id,
                final_state,
                result=result,
                error=result.get("error")
            )

            # 存储对话记忆（如果提供了session_id和user_context）
            if session_id and user_context and user_context.get("user_id"):
                try:
                    await service_integration.memory.update_context(
                        session_id=session_id,
                        user_id=user_context["user_id"],
                        user_input=message,
                        agent_response=result.get("output", ""),
                        agent_id=None  # 可以从routing_decision中获取
                    )
                    logger.info(f"Stored conversation memory for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to store conversation memory: {e}")

            # 异步存储到知识库（不阻塞响应）
            try:
                await state_manager.store_to_knowledge_base(execution_id)
            except Exception as e:
                logger.warning(f"Failed to store execution to knowledge base: {e}")

            return result

        except Exception as e:
            logger.error(f"Intelligent chat failed: {e}", exc_info=True)

            # 更新执行状态为失败
            await state_manager.update_execution_state(
                execution_id,
                ExecutionState.FAILED,
                error=str(e)
            )

            return {
                "success": False,
                "error": str(e),
                "message": "智能对话处理失败",
                "execution_id": execution_id
            }


# 全局智能体管理器实例
agent_manager = AgentManager()
