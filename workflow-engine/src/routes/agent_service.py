"""
智能体服务实现
处理智能体的业务逻辑、数据库操作和AI模型集成
"""

import asyncio
import json
import uuid
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import IntegrityError

from shared_libs.luminaos_common.schemas.agent_schemas import (
    AgentRegistry,
    AgentNode,
    AgentContext,
    AgentExecutionRecord,
    AgentNodeInput,
    AgentNodeOutput,
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    ListAgentsResponse,
    AgentStatus,
    AgentType,
    AgentExecutionState,
    ConversationMessage,
    ConversationRole
)
from database.src.models.agent_models import (
    AgentRegistryModel,
    AgentNodeModel,
    AgentContextModel,
    AgentExecutionRecordModel,
    ConversationMessageModel
)
from .ai_client import AIClient
from .workflow_executor import WorkflowExecutor
from ..core.context_manager import ContextManager
import logging

logger = logging.getLogger(__name__)


class AgentService:
    """智能体服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClient()
        # AI客户端会在初始化时尝试从配置中心加载配置
        # 如果配置中心不可用，会降级到环境变量
        self.workflow_executor = WorkflowExecutor()
        self.context_manager = ContextManager(db)

    # ==================== 智能体管理 ====================

    async def create_agent(self, agent: AgentRegistry, created_by: str) -> str:
        """创建新的智能体"""
        try:
            # 检查名称是否已存在
            existing = self.db.query(AgentRegistryModel).filter_by(name=agent.name).first()
            if existing:
                raise ValueError(f"智能体名称 '{agent.name}' 已存在")

            # 创建数据库模型
            agent_model = AgentRegistryModel(
                id=agent.id,
                name=agent.name,
                display_name=agent.display_name,
                description=agent.description,
                agent_type=agent.agent_type,
                status=agent.status,
                version=agent.version,

                # 人格设定
                personality_name=agent.personality.name,
                personality_description=agent.personality.description,
                personality_traits=agent.personality.traits,
                communication_style=agent.personality.communication_style,
                expertise_areas=agent.personality.expertise_areas,
                limitations=agent.personality.limitations,

                # 能力列表
                capabilities=[cap.dict() for cap in agent.capabilities],

                # 配置
                model=agent.configuration.model,
                temperature=agent.configuration.temperature,
                max_tokens=agent.configuration.max_tokens,
                top_p=agent.configuration.top_p,
                frequency_penalty=agent.configuration.frequency_penalty,
                presence_penalty=agent.configuration.presence_penalty,
                timeout=agent.configuration.timeout,
                max_tool_calls=agent.configuration.max_tool_calls,
                enable_memory=agent.configuration.enable_memory,
                memory_size=agent.configuration.memory_size,

                # 提示词
                system_prompt=agent.system_prompt,
                user_prompt_template=agent.user_prompt_template,

                # 工具和权限
                available_tools=agent.available_tools,
                required_permissions=agent.required_permissions,

                # 元数据
                tags=agent.tags,
                category=agent.category,
                author=agent.author,
                created_by=created_by,

                # 时间戳
                created_at=datetime.now(),
                updated_at=datetime.now(),

                # 统计
                usage_count=0,
                success_rate=0.0,
                average_execution_time=0.0
            )

            self.db.add(agent_model)
            self.db.commit()

            logger.info(f"智能体创建成功: {agent.name} (ID: {agent.id})")
            return agent.id

        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"智能体创建失败: 数据完整性错误 - {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建智能体失败: {str(e)}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[AgentRegistry]:
        """获取指定智能体"""
        try:
            agent_model = self.db.query(AgentRegistryModel).filter_by(id=agent_id).first()

            if not agent_model:
                return None

            # 转换为Pydantic模型
            return self._convert_agent_model_to_schema(agent_model)

        except Exception as e:
            logger.error(f"获取智能体失败: {str(e)}")
            raise

    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[AgentType] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        user_id: str = None
    ) -> ListAgentsResponse:
        """获取智能体列表"""
        try:
            query = self.db.query(AgentRegistryModel)

            # 应用过滤条件
            if status:
                query = query.filter(AgentRegistryModel.status == status)

            if agent_type:
                query = query.filter(AgentRegistryModel.agent_type == agent_type)

            if category:
                query = query.filter(AgentRegistryModel.category == category)

            if search:
                search_filter = or_(
                    AgentRegistryModel.name.ilike(f"%{search}%"),
                    AgentRegistryModel.display_name.ilike(f"%{search}%"),
                    AgentRegistryModel.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)

            # 计算总数
            total = query.count()

            # 应用分页
            offset = (page - 1) * page_size
            agents_models = query.order_by(desc(AgentRegistryModel.updated_at)).offset(offset).limit(page_size).all()

            # 转换为Pydantic模型
            agents = [self._convert_agent_model_to_schema(model) for model in agents_models]

            return ListAgentsResponse(
                agents=agents,
                total=total,
                page=page,
                page_size=page_size
            )

        except Exception as e:
            logger.error(f"获取智能体列表失败: {str(e)}")
            raise

    async def update_agent(self, agent_id: str, agent_data: AgentRegistry, updated_by: str) -> str:
        """更新智能体"""
        try:
            agent_model = self.db.query(AgentRegistryModel).filter_by(id=agent_id).first()

            if not agent_model:
                raise ValueError("智能体不存在")

            # 更新字段
            agent_model.name = agent_data.name
            agent_model.display_name = agent_data.display_name
            agent_model.description = agent_data.description
            agent_model.agent_type = agent_data.agent_type
            agent_model.status = agent_data.status
            agent_model.version = agent_data.version

            # 更新人格设定
            agent_model.personality_name = agent_data.personality.name
            agent_model.personality_description = agent_data.personality.description
            agent_model.personality_traits = agent_data.personality.traits
            agent_model.communication_style = agent_data.personality.communication_style
            agent_model.expertise_areas = agent_data.personality.expertise_areas
            agent_model.limitations = agent_data.personality.limitations

            # 更新能力
            agent_model.capabilities = [cap.dict() for cap in agent_data.capabilities]

            # 更新配置
            agent_model.model = agent_data.configuration.model
            agent_model.temperature = agent_data.configuration.temperature
            agent_model.max_tokens = agent_data.configuration.max_tokens
            agent_model.top_p = agent_data.configuration.top_p
            agent_model.frequency_penalty = agent_data.configuration.frequency_penalty
            agent_model.presence_penalty = agent_data.configuration.presence_penalty
            agent_model.timeout = agent_data.configuration.timeout
            agent_model.max_tool_calls = agent_data.configuration.max_tool_calls
            agent_model.enable_memory = agent_data.configuration.enable_memory
            agent_model.memory_size = agent_data.configuration.memory_size

            # 更新提示词
            agent_model.system_prompt = agent_data.system_prompt
            agent_model.user_prompt_template = agent_data.user_prompt_template

            # 更新工具和权限
            agent_model.available_tools = agent_data.available_tools
            agent_model.required_permissions = agent_data.required_permissions

            # 更新元数据
            agent_model.tags = agent_data.tags
            agent_model.category = agent_data.category
            agent_model.updated_at = datetime.now()

            self.db.commit()

            logger.info(f"智能体更新成功: {agent_data.name} (ID: {agent_id})")
            return agent_id

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新智能体失败: {str(e)}")
            raise

    async def delete_agent(self, agent_id: str):
        """删除智能体"""
        try:
            # 删除相关的节点和执行记录
            self.db.query(AgentExecutionRecordModel).filter_by(agent_id=agent_id).delete()
            self.db.query(AgentNodeModel).filter_by(agent_id=agent_id).delete()
            self.db.query(AgentContextModel).filter_by(agent_id=agent_id).delete()

            # 删除智能体
            result = self.db.query(AgentRegistryModel).filter_by(id=agent_id).delete()

            if result == 0:
                raise ValueError("智能体不存在")

            self.db.commit()

            logger.info(f"智能体删除成功: ID {agent_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除智能体失败: {str(e)}")
            raise

    # ==================== 智能体执行 ====================

    async def execute_agent(
        self,
        agent_id: str,
        request: ExecuteAgentRequest,
        user_id: str
    ) -> ExecuteAgentResponse:
        """执行智能体"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # 获取智能体信息
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValueError("智能体不存在")

            # 获取或创建上下文
            node_id = request.context.node_id if request.context else ""
            conversation_id = request.context.conversation_id if request.context else execution_id
            
            if request.context:
                # 如果提供了上下文，更新它
                context = request.context
                context.execution_count += 1
            else:
                # 获取或创建新上下文
                context = self.context_manager.get_or_create_context(
                    conversation_id=conversation_id,
                    agent_id=agent_id,
                    node_id=node_id
                )
                context.execution_count += 1

            # 构建消息（包含历史对话）
            messages = []
            if agent.system_prompt:
                messages.append({
                    "role": "system",
                    "content": agent.system_prompt
                })
            
            # 添加历史消息
            for msg in context.messages[-10:]:  # 只保留最近10条消息
                messages.append({
                    "role": msg.role.value if hasattr(msg.role, 'value') else msg.role,
                    "content": msg.content
                })

            # 创建执行记录
            execution_record = AgentExecutionRecordModel(
                id=execution_id,
                agent_id=agent_id,
                node_id=request.context.node_id if request.context else "",
                workflow_id=request.context.conversation_id if request.context else "",
                execution_id=execution_id,
                input_data=request.input_data.dict(),
                state=AgentExecutionState.RUNNING,
                start_time=start_time,
                record_metadata={}
            )
            self.db.add(execution_record)
            self.db.commit()

            # 准备AI客户端参数
            ai_params = {
                "model": agent.configuration.model,
                "temperature": agent.configuration.temperature,
                "max_tokens": agent.configuration.max_tokens,
                "top_p": agent.configuration.top_p,
                "frequency_penalty": agent.configuration.frequency_penalty,
                "presence_penalty": agent.configuration.presence_penalty
            }

            # 用户输入
            user_content = agent.user_prompt_template.format(input=request.input_data.content)
            messages.append({
                "role": "user",
                "content": user_content
            })

            # 调用AI模型
            response = await self.ai_client.chat_completion(
                messages=messages,
                **ai_params
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 创建输出数据
            output_data = AgentNodeOutput(
                content=response.get("content", ""),
                metadata=response.get("metadata", {}),
                tool_calls=response.get("tool_calls", []),
                reasoning_steps=response.get("reasoning_steps", []),
                confidence_score=response.get("confidence_score", 1.0),
                execution_time=execution_time,
                tokens_used=response.get("usage", {}).get("total_tokens", 0)
            )

            # 更新执行记录
            execution_record.output_data = output_data.dict()
            execution_record.state = AgentExecutionState.COMPLETED
            execution_record.end_time = end_time
            execution_record.execution_time = execution_time
            execution_record.tokens_used = output_data.tokens_used
            execution_record.success = True
            self.db.commit()

            # 更新上下文
            # 添加用户消息到上下文
            from shared_libs.luminaos_common.schemas.agent_schemas import ConversationRole
            context.messages.append(ConversationMessage(
                role=ConversationRole.USER,
                content=user_content,
                timestamp=start_time
            ))
            # 添加助手响应到上下文
            context.messages.append(ConversationMessage(
                role=ConversationRole.ASSISTANT,
                content=output_data.content,
                tool_calls=output_data.tool_calls or [],
                metadata=output_data.metadata or {},
                timestamp=end_time
            ))
            # 更新上下文统计
            context.total_tokens += output_data.tokens_used
            context.total_execution_time += execution_time
            context.updated_at = datetime.now()
            # 保存上下文
            self.context_manager.save_context(context)

            # 更新智能体统计
            await self._update_agent_statistics(agent_id, execution_time, True)

            # 返回执行结果
            return ExecuteAgentResponse(
                success=True,
                execution_id=execution_id,
                output_data=output_data,
                context=context,
                execution_record=execution_record
            )

        except Exception as e:
            # 更新执行记录为失败状态
            if 'execution_record' in locals():
                execution_record.state = AgentExecutionState.FAILED
                execution_record.error_message = str(e)
                execution_record.end_time = datetime.now()
                execution_record.success = False
                self.db.commit()

            # 更新智能体统计
            await self._update_agent_statistics(agent_id, 0, False)

            logger.error(f"智能体执行失败: {str(e)}")
            raise

    async def execute_agent_stream(
        self,
        agent_id: str,
        request: ExecuteAgentRequest,
        user_id: str
    ) -> AsyncGenerator[str, None]:
        """流式执行智能体"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # 获取智能体信息
            agent = await self.get_agent(agent_id)
            if not agent:
                raise ValueError("智能体不存在")

            # 准备消息和参数
            messages = []
            if agent.system_prompt:
                messages.append({"role": "system", "content": agent.system_prompt})

            user_content = agent.user_prompt_template.format(input=request.input_data.content)
            messages.append({"role": "user", "content": user_content})

            ai_params = {
                "model": agent.configuration.model,
                "temperature": agent.configuration.temperature,
                "max_tokens": agent.configuration.max_tokens,
                "top_p": agent.configuration.top_p,
                "frequency_penalty": agent.configuration.frequency_penalty,
                "presence_penalty": agent.configuration.presence_penalty,
                "stream": True
            }

            # 流式调用AI模型
            full_content = ""
            async for chunk in self.ai_client.chat_completion_stream(messages=messages, **ai_params):
                if chunk.get("content"):
                    full_content += chunk["content"]

                yield json.dumps({
                    "type": "content",
                    "data": chunk,
                    "execution_id": execution_id
                })

            # 执行完成后的处理
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 保存执行记录
            execution_record = AgentExecutionRecordModel(
                id=execution_id,
                agent_id=agent_id,
                node_id=request.context.node_id if request.context else "",
                workflow_id=request.context.conversation_id if request.context else "",
                execution_id=execution_id,
                input_data=request.input_data.dict(),
                output_data={
                    "content": full_content,
                    "execution_time": execution_time
                },
                state=AgentExecutionState.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                success=True,
                record_metadata={}
            )
            self.db.add(execution_record)
            self.db.commit()

            # 最终消息
            yield json.dumps({
                "type": "completed",
                "data": {
                    "execution_id": execution_id,
                    "execution_time": execution_time,
                    "success": True
                }
            })

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "data": {
                    "error": str(e),
                    "execution_id": execution_id
                }
            })

    # ==================== 辅助方法 ====================

    def _convert_agent_model_to_schema(self, agent_model: AgentRegistryModel) -> AgentRegistry:
        """将数据库模型转换为Pydantic模式"""
        from shared_libs.luminaos_common.schemas.agent_schemas import AgentPersonality, AgentConfiguration, AgentCapability

        # 重建人格设定
        personality = AgentPersonality(
            name=agent_model.personality_name,
            description=agent_model.personality_description,
            traits=agent_model.personality_traits or [],
            communication_style=agent_model.communication_style,
            expertise_areas=agent_model.expertise_areas or [],
            limitations=agent_model.limitations or []
        )

        # 重建能力列表
        capabilities = [
            AgentCapability(**cap_dict) for cap_dict in (agent_model.capabilities or [])
        ]

        # 重建配置
        configuration = AgentConfiguration(
            model=agent_model.model,
            temperature=agent_model.temperature,
            max_tokens=agent_model.max_tokens,
            top_p=agent_model.top_p,
            frequency_penalty=agent_model.frequency_penalty,
            presence_penalty=agent_model.presence_penalty,
            timeout=agent_model.timeout,
            max_tool_calls=agent_model.max_tool_calls,
            enable_memory=agent_model.enable_memory,
            memory_size=agent_model.memory_size
        )

        return AgentRegistry(
            id=agent_model.id,
            name=agent_model.name,
            display_name=agent_model.display_name,
            description=agent_model.description,
            agent_type=agent_model.agent_type,
            status=agent_model.status,
            version=agent_model.version,
            personality=personality,
            capabilities=capabilities,
            configuration=configuration,
            system_prompt=agent_model.system_prompt,
            user_prompt_template=agent_model.user_prompt_template,
            available_tools=agent_model.available_tools or [],
            required_permissions=agent_model.required_permissions or [],
            tags=agent_model.tags or [],
            category=agent_model.category,
            author=agent_model.author,
            created_by=agent_model.created_by,
            created_at=agent_model.created_at,
            updated_at=agent_model.updated_at,
            published_at=agent_model.published_at,
            usage_count=agent_model.usage_count,
            success_rate=agent_model.success_rate,
            average_execution_time=agent_model.average_execution_time
        )

    async def _update_agent_statistics(self, agent_id: str, execution_time: float, success: bool):
        """更新智能体统计信息"""
        try:
            agent_model = self.db.query(AgentRegistryModel).filter_by(id=agent_id).first()
            if agent_model:
                # 更新使用次数
                agent_model.usage_count += 1

                # 更新平均执行时间
                total_time = agent_model.average_execution_time * (agent_model.usage_count - 1) + execution_time
                agent_model.average_execution_time = total_time / agent_model.usage_count

                # 更新成功率
                if success:
                    success_count = agent_model.success_rate * (agent_model.usage_count - 1) + 1
                    agent_model.success_rate = success_count / agent_model.usage_count
                else:
                    success_count = agent_model.success_rate * (agent_model.usage_count - 1)
                    agent_model.success_rate = success_count / agent_model.usage_count

                self.db.commit()

        except Exception as e:
            logger.error(f"更新智能体统计失败: {str(e)}")

    async def update_agent_status(self, agent_id: str, status: AgentStatus, updated_by: str):
        """更新智能体状态"""
        try:
            agent_model = self.db.query(AgentRegistryModel).filter_by(id=agent_id).first()
            if not agent_model:
                raise ValueError("智能体不存在")

            agent_model.status = status
            agent_model.updated_at = datetime.now()
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise

    async def get_agent_statistics(self, agent_id: str, days: int) -> Dict[str, Any]:
        """获取智能体统计信息"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            # 获取执行记录统计
            executions = self.db.query(AgentExecutionRecordModel).filter(
                and_(
                    AgentExecutionRecordModel.agent_id == agent_id,
                    AgentExecutionRecordModel.start_time >= start_date
                )
            ).all()

            total_executions = len(executions)
            successful_executions = sum(1 for ex in executions if ex.success)
            failed_executions = total_executions - successful_executions

            total_execution_time = sum(ex.execution_time or 0 for ex in executions)
            total_tokens = sum(ex.tokens_used or 0 for ex in executions)

            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_execution_time": total_execution_time / total_executions if total_executions > 0 else 0,
                "total_tokens_used": total_tokens,
                "average_tokens_per_execution": total_tokens / total_executions if total_executions > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取智能体统计失败: {str(e)}")
            raise

    async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """检查智能体健康状态"""
        try:
            agent = await self.get_agent(agent_id)
            if not agent:
                return {
                    "status": "error",
                    "message": "智能体不存在"
                }

            # 检查最近的执行记录
            recent_executions = self.db.query(AgentExecutionRecordModel).filter(
                and_(
                    AgentExecutionRecordModel.agent_id == agent_id,
                    AgentExecutionRecordModel.start_time >= datetime.now() - timedelta(hours=24)
                )
            ).limit(10).all()

            recent_failures = [ex for ex in recent_executions if not ex.success]
            failure_rate = len(recent_failures) / len(recent_executions) if recent_executions else 0

            if agent.status != AgentStatus.ACTIVE:
                health_status = "inactive"
            elif failure_rate > 0.5:
                health_status = "degraded"
            elif failure_rate > 0.1:
                health_status = "warning"
            else:
                health_status = "healthy"

            return {
                "status": health_status,
                "agent_status": agent.status.value,
                "recent_executions": len(recent_executions),
                "recent_failures": len(recent_failures),
                "failure_rate": failure_rate,
                "last_execution": recent_executions[0].start_time.isoformat() if recent_executions else None
            }

        except Exception as e:
            logger.error(f"检查智能体健康状态失败: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def test_agent(self, agent_id: str, test_input: AgentNodeInput, user_id: str) -> Dict[str, Any]:
        """测试智能体"""
        try:
            # 创建简单的测试执行请求
            request = ExecuteAgentRequest(
                agent_id=agent_id,
                input_data=test_input,
                stream=False
            )

            # 执行测试
            result = await self.execute_agent(agent_id, request, user_id)

            return {
                "success": True,
                "test_result": {
                    "execution_id": result.execution_id,
                    "output_content": result.output_data.content[:500] if result.output_data else "",
                    "execution_time": result.output_data.execution_time if result.output_data else 0,
                    "tokens_used": result.output_data.tokens_used if result.output_data else 0
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_agent_categories(self) -> List[str]:
        """获取所有智能体分类"""
        try:
            categories = self.db.query(AgentRegistryModel.category).distinct().all()
            return [cat[0] for cat in categories if cat[0]]

        except Exception as e:
            logger.error(f"获取智能体分类失败: {str(e)}")
            raise

    async def create_agent_node(self, agent_id: str, workflow_id: str, node_data: Dict[str, Any], user_id: str) -> str:
        """创建智能体节点"""
        try:
            node_id = str(uuid.uuid4())

            node_model = AgentNodeModel(
                id=node_id,
                workflow_id=workflow_id,
                agent_id=agent_id,
                node_name=node_data.get("name", f"Agent-{agent_id[:8]}"),
                description=node_data.get("description"),
                position=node_data.get("position"),
                size=node_data.get("size"),
                style=node_data.get("style"),
                input_mapping=node_data.get("input_mapping", {}),
                output_mapping=node_data.get("output_mapping", {}),
                retry_count=node_data.get("retry_count", 3),
                retry_delay=node_data.get("retry_delay", 5),
                enable_streaming=node_data.get("enable_streaming", False),
                context_window_size=node_data.get("context_window_size", 10),
                preserve_conversation=node_data.get("preserve_conversation", True),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.db.add(node_model)
            self.db.commit()

            return node_id

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建智能体节点失败: {str(e)}")
            raise

    async def list_agent_nodes(self, agent_id: str, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取智能体节点列表"""
        try:
            query = self.db.query(AgentNodeModel).filter_by(agent_id=agent_id)

            if workflow_id:
                query = query.filter_by(workflow_id=workflow_id)

            nodes = query.all()

            return [
                {
                    "id": node.id,
                    "workflow_id": node.workflow_id,
                    "agent_id": node.agent_id,
                    "node_name": node.node_name,
                    "description": node.description,
                    "position": node.position,
                    "size": node.size,
                    "style": node.style,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat()
                }
                for node in nodes
            ]

        except Exception as e:
            logger.error(f"获取智能体节点列表失败: {str(e)}")
            raise

    async def get_execution_history(
        self,
        agent_id: str,
        page: int = 1,
        page_size: int = 20,
        state: Optional[AgentExecutionState] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """获取执行历史"""
        try:
            query = self.db.query(AgentExecutionRecordModel).filter_by(agent_id=agent_id)

            if state:
                query = query.filter(AgentExecutionRecordModel.state == state)

            if start_time:
                query = query.filter(AgentExecutionRecordModel.start_time >= start_time)

            if end_time:
                query = query.filter(AgentExecutionRecordModel.end_time <= end_time)

            total = query.count()

            offset = (page - 1) * page_size
            records = query.order_by(desc(AgentExecutionRecordModel.start_time)).offset(offset).limit(page_size).all()

            return {
                "executions": [
                    {
                        "id": record.id,
                        "execution_id": record.execution_id,
                        "state": record.state.value,
                        "start_time": record.start_time.isoformat(),
                        "end_time": record.end_time.isoformat() if record.end_time else None,
                        "execution_time": record.execution_time,
                        "success": record.success,
                        "tokens_used": record.tokens_used,
                        "error_message": record.error_message
                    }
                    for record in records
                ],
                "total": total,
                "page": page,
                "page_size": page_size
            }

        except Exception as e:
            logger.error(f"获取执行历史失败: {str(e)}")
            raise