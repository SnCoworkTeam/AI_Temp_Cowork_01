"""
对话管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

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
from luminaos_common.schemas.chat_schemas import (
    ConversationCreate, ConversationUpdate, Conversation,
    ConversationWithMessages, ConversationListResponse,
    MessageCreate, Message
)
from ..services.conversation_service import ConversationService

router = APIRouter()
from fastapi import Request


def get_current_user_id():
    """
    获取当前用户ID
    从请求头中获取用户ID（由API Gateway认证后传递）
    """
    # 这里应该从认证middleware中获取用户ID
    # API Gateway 会在请求头中传递 x-user-id
    return "test-user-id"


async def get_user_from_header(request: Request) -> str:
    """
    从请求头获取用户ID
    API Gateway 会在请求头中传递 x-user-id 或Authorization
    """
    # 优先从 x-user-id 头获取（API Gateway 传递的用户ID）
    user_id = request.headers.get('x-user-id')
    if user_id:
        return user_id
    
    # 如果没有 x-user-id，尝试从 Authorization 获取
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        # 这里可以解析 JWT token 获取用户ID
        # 暂时返回测试用户ID
        return "test-user-id"
    
    return "test-user-id"


@router.post("/conversations", response_model=Conversation, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    request: Request = None
):
    """创建新对话"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    return service.create_conversation(user_id, data)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    include_archived: bool = Query(False, description="是否包含已归档的对话"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """获取用户的对话列表"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    conversations, total = service.get_user_conversations(
        user_id, include_archived, page, page_size
    )
    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True, description="是否包含消息列表"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """获取对话详情"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    return service.get_conversation(conversation_id, user_id, include_messages)


@router.patch("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    request: Request = None
):
    """更新对话"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    return service.update_conversation(conversation_id, user_id, data)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    request: Request = None
):
    """删除对话"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    service.delete_conversation(conversation_id, user_id)
    return None


@router.post("/conversations/{conversation_id}/messages", response_model=Message, status_code=201)
async def add_message(
    conversation_id: str,
    data: MessageCreate,
    db: Session = Depends(get_db),
    request: Request = None
):
    """向对话添加消息"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    return service.add_message(
        conversation_id, user_id, data.role, data.content,
        metadata=data.metadata
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[Message])
async def get_messages(
    conversation_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="限制返回的消息数量"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """获取对话的消息列表"""
    user_id = await get_user_from_header(request) if request else "test-user-id"
    service = ConversationService(db)
    return service.get_messages(conversation_id, user_id, limit)
