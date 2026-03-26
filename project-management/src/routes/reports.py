"""
周报管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db

router = APIRouter()


@router.get("/")
async def list_reports(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取周报列表"""
    # TODO: 实现周报列表
    return {"items": [], "total": 0}

