"""
实时元数据查询API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.realtime_metadata_engine import RealtimeMetadataEngine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 配置日志格式
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RealtimeMetadataRequest(BaseModel):
    """实时元数据查询请求"""
    user_input: str = Field(..., description="用户输入")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    use_cache: bool = Field(True, description="是否使用缓存")
    limit_per_type: int = Field(5, ge=1, le=20, description="每种类型的返回数量限制")


def get_metadata_engine(db: Session = Depends(get_db)) -> RealtimeMetadataEngine:
    """获取元数据引擎"""
    return RealtimeMetadataEngine(db)


@router.post(
    "/realtime-query",
    summary="实时元数据查询",
    description="并行查询多种元数据源并聚合结果，用于意图识别和执行编排",
    tags=["Metadata"]
)
async def realtime_metadata_query(
    request: RealtimeMetadataRequest,
    engine: RealtimeMetadataEngine = Depends(get_metadata_engine)
) -> Dict[str, Any]:
    """
    实时元数据查询
    
    并行查询数据资产、AI模型、业务实体、工作流等元数据，
    并聚合结果用于意图识别和执行编排。
    """
    try:
        metadata = await engine.get_execution_metadata(
            user_input=request.user_input,
            context=request.context,
            use_cache=request.use_cache,
            limit_per_type=request.limit_per_type
        )
        
        return {
            "success": True,
            "metadata": metadata.to_dict(),
            "query": request.user_input
        }
    except Exception as e:
        logger.error(f"Failed to query realtime metadata: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query realtime metadata: {str(e)}"
        )


@router.get(
    "/realtime-query",
    summary="实时元数据查询（GET方式）",
    description="GET方式的实时元数据查询，便于测试",
    tags=["Metadata"]
)
async def realtime_metadata_query_get(
    user_input: str = Query(..., description="用户输入"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    limit_per_type: int = Query(5, ge=1, le=20, description="每种类型的返回数量限制"),
    engine: RealtimeMetadataEngine = Depends(get_metadata_engine)
) -> Dict[str, Any]:
    """GET方式的实时元数据查询"""
    try:
        context = {}
        if user_id:
            context["user_id"] = user_id
        if session_id:
            context["session_id"] = session_id
        
        metadata = await engine.get_execution_metadata(
            user_input=user_input,
            context=context,
            use_cache=use_cache,
            limit_per_type=limit_per_type
        )
        
        return {
            "success": True,
            "metadata": metadata.to_dict(),
            "query": user_input
        }
    except Exception as e:
        logger.error(f"Failed to query realtime metadata: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query realtime metadata: {str(e)}"
        )

