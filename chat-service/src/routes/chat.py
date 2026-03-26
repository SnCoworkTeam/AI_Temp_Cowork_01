"""
聊天API路由 - 处理AI对话
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import time

# 导入database模块（通过sys.path设置）
import sys
from pathlib import Path
from typing import Generator
from sqlalchemy.orm import Session

project_root = Path(__file__).parent.parent.parent.parent
_database_src = str(project_root / "database" / "src")
if _database_src not in sys.path:
    sys.path.insert(0, _database_src)

from database.src.core.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（FastAPI依赖）
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
from models.chat_models import MessageRole, MessageStatus
from luminaos_common.schemas.chat_schemas import ChatRequest, ChatResponse
from ..services.conversation_service import ConversationService

router = APIRouter()
logger = logging.getLogger("chat-service")


def get_current_user_id():
    """
    获取当前用户ID
    TODO: 集成认证服务，从JWT token中获取用户ID
    """
    return "test-user-id"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    与AI助手对话

    如果提供了conversation_id，则在该对话中添加消息
    如果没有提供，则创建新对话
    """
    service = ConversationService(db)
    start_time = time.time()

    # 如果没有提供conversation_id，创建新对话
    if not request.conversation_id:
        from luminaos_common.schemas.chat_schemas import ConversationCreate
        conversation = service.create_conversation(
            user_id,
            ConversationCreate(
                title=request.message[:50] if len(request.message) > 50 else request.message,
                description="AI助手对话"
            )
        )
        conversation_id = conversation.id
    else:
        conversation_id = request.conversation_id

    # 添加用户消息
    user_message = service.add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=request.message,
        metadata=request.metadata
    )

    # 创建AI响应消息（先标记为处理中）
    ai_message = service.add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=MessageRole.ASSISTANT,
        content="",  # 初始为空
        status=MessageStatus.PROCESSING,
        model=request.model or "default"
    )

    # 调用agent-service处理消息
    try:
        import httpx
        import os
        
        agent_service_url = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
        
        # 获取对话历史
        conversation_history = service.get_messages(conversation_id, user_id, limit=10)
        history_list = [
            {
                "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                "content": msg.content
            }
            for msg in conversation_history
        ]
        
        # 调用agent-service
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{agent_service_url}/api/v1/chat/intelligent",
                json={
                    "message": request.message,
                    "conversation_history": history_list,
                    "user_context": {
                        "user_id": user_id,
                        "session_id": conversation_id
                    },
                    "session_id": conversation_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response_content = result.get("output", "抱歉，无法生成回复。")
                if result.get("error"):
                    ai_response_content = f"{ai_response_content}\n\n错误: {result.get('error')}"
            else:
                logger.error(f"Agent service error: {response.status_code}, {response.text}")
                ai_response_content = f"抱歉，AI服务暂时不可用。错误代码: {response.status_code}"
    except Exception as e:
        logger.error(f"Failed to call agent-service: {str(e)}", exc_info=True)
        # 降级到简单回复
        ai_response_content = f"收到您的消息：{request.message}\n\nAI助手功能正在处理中，请稍候..."
    
    execution_time = int((time.time() - start_time) * 1000)

    # 更新AI消息
    from ..repositories.conversation_repository import MessageRepository
    message_repo = MessageRepository(db)
    ai_message_updated = message_repo.create(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=ai_response_content,
        status=MessageStatus.COMPLETED,
        model=request.model or "default",
        tokens_used=len(ai_response_content),  # 模拟token计数
        execution_time=execution_time,
        metadata={"simulated": True}
    )

    # 删除临时的processing消息
    message_repo.delete(ai_message.id)

    # 生成建议的后续问题
    suggestions = [
        "告诉我更多细节",
        "有什么其他建议吗？",
        "能否解释一下？"
    ]

    from luminaos_common.schemas.chat_schemas import Message as MessageSchema
    return ChatResponse(
        conversation_id=conversation_id,
        message=MessageSchema(**service._message_to_dict(ai_message_updated)),
        suggestions=suggestions
    )


@router.get("/chat/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取对话历史"""
    service = ConversationService(db)
    return service.get_conversation(conversation_id, user_id, include_messages=True)
