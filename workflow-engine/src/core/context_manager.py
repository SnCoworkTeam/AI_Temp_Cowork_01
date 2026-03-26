"""
上下文管理器
提供智能体上下文的持久化、加载和清理功能
"""
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, delete, func

from shared_libs.luminaos_common.schemas.agent_schemas import (
    AgentContext,
    ConversationMessage,
    ConversationRole,
    AgentExecutionState
)
from database.src.models.agent_models import (
    AgentContextModel,
    ConversationMessageModel
)

logger = logging.getLogger(__name__)


class ContextManager:
    """统一的上下文管理器"""
    
    def __init__(self, db_session: Session):
        """
        初始化上下文管理器
        
        Args:
            db_session: SQLAlchemy数据库会话
        """
        self.db = db_session
    
    def get_or_create_context(
        self,
        conversation_id: str,
        agent_id: str,
        node_id: str
    ) -> AgentContext:
        """
        获取或创建上下文
        
        Args:
            conversation_id: 对话ID
            agent_id: 智能体ID
            node_id: 节点ID
            
        Returns:
            AgentContext对象
        """
        try:
            # 查找现有上下文
            context_model = self.db.query(AgentContextModel).filter(
                and_(
                    AgentContextModel.conversation_id == conversation_id,
                    AgentContextModel.agent_id == agent_id,
                    AgentContextModel.node_id == node_id
                )
            ).first()
            
            if context_model:
                # 加载现有上下文
                return self._convert_model_to_schema(context_model)
            else:
                # 创建新上下文
                new_context = AgentContext(
                    conversation_id=conversation_id,
                    agent_id=agent_id,
                    node_id=node_id,
                    messages=[],
                    current_state=AgentExecutionState.PENDING,
                    variables={},
                    shared_memory={},
                    execution_count=0,
                    total_tokens=0,
                    total_execution_time=0.0,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                # 保存新上下文
                self.save_context(new_context)
                return new_context
                
        except Exception as e:
            logger.error(f"获取或创建上下文失败: {e}")
            # 返回一个默认上下文
            return AgentContext(
                conversation_id=conversation_id,
                agent_id=agent_id,
                node_id=node_id
            )
    
    def save_context(self, context: AgentContext) -> bool:
        """
        保存上下文到数据库
        
        Args:
            context: AgentContext对象
            
        Returns:
            是否成功
        """
        try:
            # 查找现有上下文
            context_model = self.db.query(AgentContextModel).filter(
                and_(
                    AgentContextModel.conversation_id == context.conversation_id,
                    AgentContextModel.agent_id == context.agent_id,
                    AgentContextModel.node_id == context.node_id
                )
            ).first()
            
            if context_model:
                # 更新现有上下文
                context_model.current_state = context.current_state.value
                context_model.variables = context.variables
                context_model.shared_memory = context.shared_memory
                context_model.execution_count = context.execution_count
                context_model.total_tokens = context.total_tokens
                context_model.total_execution_time = context.total_execution_time
                context_model.updated_at = datetime.now()
                
                # 更新过期时间（如果设置了）
                if context.expires_at:
                    context_model.expires_at = context.expires_at
                
                context_id = context_model.id
            else:
                # 创建新上下文
                context_id = str(uuid.uuid4())
                context_model = AgentContextModel(
                    id=context_id,
                    conversation_id=context.conversation_id,
                    agent_id=context.agent_id,
                    node_id=context.node_id,
                    current_state=context.current_state.value,
                    variables=context.variables,
                    shared_memory=context.shared_memory,
                    execution_count=context.execution_count,
                    total_tokens=context.total_tokens,
                    total_execution_time=context.total_execution_time,
                    created_at=context.created_at or datetime.now(),
                    updated_at=datetime.now(),
                    expires_at=context.expires_at
                )
                self.db.add(context_model)
                # 刷新以获取ID
                self.db.flush()
            
            # 保存对话消息
            self._save_messages(context_id, context.conversation_id, context.messages)
            
            self.db.commit()
            logger.debug(
                f"上下文已保存: conversation_id={context.conversation_id}, "
                f"agent_id={context.agent_id}, node_id={context.node_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"保存上下文失败: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def load_context(
        self,
        conversation_id: str,
        agent_id: str,
        node_id: str
    ) -> Optional[AgentContext]:
        """
        从数据库加载上下文
        
        Args:
            conversation_id: 对话ID
            agent_id: 智能体ID
            node_id: 节点ID
            
        Returns:
            AgentContext对象，如果不存在则返回None
        """
        try:
            context_model = self.db.query(AgentContextModel).filter(
                and_(
                    AgentContextModel.conversation_id == conversation_id,
                    AgentContextModel.agent_id == agent_id,
                    AgentContextModel.node_id == node_id
                )
            ).first()
            
            if context_model:
                return self._convert_model_to_schema(context_model)
            return None
            
        except Exception as e:
            logger.error(f"加载上下文失败: {e}", exc_info=True)
            return None
    
    def load_context_by_conversation_id(self, conversation_id: str) -> List[AgentContext]:
        """
        根据对话ID加载所有相关上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            AgentContext列表
        """
        try:
            context_models = self.db.query(AgentContextModel).filter(
                AgentContextModel.conversation_id == conversation_id
            ).all()
            
            return [self._convert_model_to_schema(model) for model in context_models]
            
        except Exception as e:
            logger.error(f"加载上下文列表失败: {e}", exc_info=True)
            return []
    
    def update_context(
        self,
        context: AgentContext,
        update_messages: bool = True
    ) -> bool:
        """
        更新上下文（保存的别名方法）
        
        Args:
            context: AgentContext对象
            update_messages: 是否更新消息列表
            
        Returns:
            是否成功
        """
        if not update_messages:
            # 如果不需要更新消息，只更新其他字段
            try:
                context_model = self.db.query(AgentContextModel).filter(
                    and_(
                        AgentContextModel.conversation_id == context.conversation_id,
                        AgentContextModel.agent_id == context.agent_id,
                        AgentContextModel.node_id == context.node_id
                    )
                ).first()
                
                if context_model:
                    context_model.current_state = context.current_state.value
                    context_model.variables = context.variables
                    context_model.shared_memory = context.shared_memory
                    context_model.execution_count = context.execution_count
                    context_model.total_tokens = context.total_tokens
                    context_model.total_execution_time = context.total_execution_time
                    context_model.updated_at = datetime.now()
                    self.db.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"更新上下文失败: {e}", exc_info=True)
                self.db.rollback()
                return False
        else:
            return self.save_context(context)
    
    def delete_context(
        self,
        conversation_id: str,
        agent_id: str,
        node_id: str
    ) -> bool:
        """
        删除上下文
        
        Args:
            conversation_id: 对话ID
            agent_id: 智能体ID
            node_id: 节点ID
            
        Returns:
            是否成功
        """
        try:
            context_model = self.db.query(AgentContextModel).filter(
                and_(
                    AgentContextModel.conversation_id == conversation_id,
                    AgentContextModel.agent_id == agent_id,
                    AgentContextModel.node_id == node_id
                )
            ).first()
            
            if context_model:
                # 删除关联的消息（通过cascade会自动删除）
                self.db.delete(context_model)
                self.db.commit()
                logger.info(
                    f"上下文已删除: conversation_id={conversation_id}, "
                    f"agent_id={agent_id}, node_id={node_id}"
                )
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除上下文失败: {e}", exc_info=True)
            self.db.rollback()
            return False
    
    def cleanup_old_contexts(self, older_than_days: int = 30) -> int:
        """
        清理旧上下文
        
        Args:
            older_than_days: 清理多少天前的上下文（默认30天）
            
        Returns:
            清理的上下文数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            # 查找需要清理的上下文
            old_contexts = self.db.query(AgentContextModel).filter(
                AgentContextModel.updated_at < cutoff_date
            ).all()
            
            count = len(old_contexts)
            
            if count > 0:
                # 删除旧上下文（关联的消息会通过cascade自动删除）
                for context in old_contexts:
                    self.db.delete(context)
                self.db.commit()
                logger.info(f"清理了 {count} 个旧上下文（超过 {older_than_days} 天）")
            
            return count
            
        except Exception as e:
            logger.error(f"清理旧上下文失败: {e}", exc_info=True)
            self.db.rollback()
            return 0
    
    def cleanup_expired_contexts(self) -> int:
        """
        清理已过期的上下文
        
        Returns:
            清理的上下文数量
        """
        try:
            now = datetime.now()
            
            # 查找已过期的上下文
            expired_contexts = self.db.query(AgentContextModel).filter(
                and_(
                    AgentContextModel.expires_at.isnot(None),
                    AgentContextModel.expires_at < now
                )
            ).all()
            
            count = len(expired_contexts)
            
            if count > 0:
                # 删除过期上下文
                for context in expired_contexts:
                    self.db.delete(context)
                self.db.commit()
                logger.info(f"清理了 {count} 个过期上下文")
            
            return count
            
        except Exception as e:
            logger.error(f"清理过期上下文失败: {e}", exc_info=True)
            self.db.rollback()
            return 0
    
    def _save_messages(
        self,
        context_id: str,
        conversation_id: str,
        messages: List[ConversationMessage]
    ):
        """
        保存对话消息
        
        Args:
            context_id: 上下文ID
            conversation_id: 对话ID
            messages: 消息列表
        """
        try:
            # 删除旧消息（如果需要完全替换）
            # 注意：这里可以选择保留历史消息或替换
            # 为了简化，我们选择替换策略：删除所有旧消息，然后添加新消息
            
            # 删除该上下文的所有旧消息
            self.db.query(ConversationMessageModel).filter(
                ConversationMessageModel.context_id == context_id
            ).delete()
            
            # 添加新消息
            for msg in messages:
                message_model = ConversationMessageModel(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role=msg.role.value if isinstance(msg.role, ConversationRole) else msg.role,
                    content=msg.content,
                    tool_calls=msg.tool_calls if hasattr(msg, 'tool_calls') else [],
                    message_metadata=msg.metadata if hasattr(msg, 'metadata') else {},
                    timestamp=msg.timestamp if hasattr(msg, 'timestamp') else datetime.now(),
                    context_id=context_id
                )
                self.db.add(message_model)
                
        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)
            raise
    
    def _convert_model_to_schema(self, context_model: AgentContextModel) -> AgentContext:
        """
        将数据库模型转换为Pydantic模型
        
        Args:
            context_model: AgentContextModel对象
            
        Returns:
            AgentContext对象
        """
        # 加载关联的消息
        messages = []
        for msg_model in context_model.messages:
            messages.append(ConversationMessage(
                role=ConversationRole(msg_model.role),
                content=msg_model.content,
                tool_calls=msg_model.tool_calls or [],
                metadata=msg_model.message_metadata or {},
                timestamp=msg_model.timestamp
            ))
        
        # 转换执行状态
        try:
            current_state = AgentExecutionState(context_model.current_state)
        except ValueError:
            current_state = AgentExecutionState.PENDING
        
        return AgentContext(
            conversation_id=context_model.conversation_id,
            agent_id=context_model.agent_id,
            node_id=context_model.node_id,
            messages=messages,
            current_state=current_state,
            variables=context_model.variables or {},
            shared_memory=context_model.shared_memory or {},
            execution_count=context_model.execution_count or 0,
            total_tokens=context_model.total_tokens or 0,
            total_execution_time=context_model.total_execution_time or 0.0,
            created_at=context_model.created_at,
            updated_at=context_model.updated_at,
            expires_at=context_model.expires_at
        )
    
    def get_context_statistics(
        self,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> dict:
        """
        获取上下文统计信息
        
        Args:
            agent_id: 智能体ID（可选）
            conversation_id: 对话ID（可选）
            
        Returns:
            统计信息字典
        """
        try:
            query = self.db.query(AgentContextModel)
            
            if agent_id:
                query = query.filter(AgentContextModel.agent_id == agent_id)
            if conversation_id:
                query = query.filter(AgentContextModel.conversation_id == conversation_id)
            
            total_contexts = query.count()
            
            # 计算总消息数
            total_messages = self.db.query(ConversationMessageModel).count()
            
            # 计算平均执行时间
            avg_execution_time = self.db.query(
                func.avg(AgentContextModel.total_execution_time)
            ).scalar() or 0.0
            
            # 计算总token使用量
            total_tokens = self.db.query(
                func.sum(AgentContextModel.total_tokens)
            ).scalar() or 0
            
            return {
                "total_contexts": total_contexts,
                "total_messages": total_messages,
                "average_execution_time": float(avg_execution_time),
                "total_tokens": int(total_tokens)
            }
            
        except Exception as e:
            logger.error(f"获取上下文统计失败: {e}", exc_info=True)
            return {
                "total_contexts": 0,
                "total_messages": 0,
                "average_execution_time": 0.0,
                "total_tokens": 0
            }

