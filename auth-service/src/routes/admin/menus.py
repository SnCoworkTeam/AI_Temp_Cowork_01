"""
菜单管理API
将菜单权限配置存储到 system_configs 中
"""
from typing import Any, Dict, List
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...dependencies.database import get_db
from ...middleware.permission_middleware import require_admin

# 引入数据库模型
from database.src.models.system_models import SystemConfig, ConfigCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/menus", tags=["菜单管理"])

MENU_CONFIG_KEY = "menu_permissions_config"


class MenuConfigPayload(BaseModel):
    config: List[Dict[str, Any]]


class MenuConfigResponse(BaseModel):
    config: List[Dict[str, Any]]


@router.get("", response_model=MenuConfigResponse)
async def get_menu_config(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取菜单权限配置"""
    try:
        record = db.query(SystemConfig).filter(SystemConfig.key == MENU_CONFIG_KEY).first()
        if record and record.value:
            try:
                config = json.loads(record.value)
            except json.JSONDecodeError:
                logger.warning("Menu config JSON decode failed, returning empty config")
                config = []
        else:
            config = []

        if not isinstance(config, list):
            config = []

        return MenuConfigResponse(config=config)
    except Exception as e:
        logger.error(f"Failed to load menu config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load menu config: {str(e)}"
        )


@router.put("", response_model=MenuConfigResponse)
async def save_menu_config(
    payload: MenuConfigPayload,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """保存菜单权限配置"""
    try:
        data = payload.config or []
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Menu config must be a list"
            )

        record = db.query(SystemConfig).filter(SystemConfig.key == MENU_CONFIG_KEY).first()
        value = json.dumps(data, ensure_ascii=False)

        if record:
            record.value = value
            record.value_type = "json"
            record.category = ConfigCategory.SYSTEM
            record.description = "Menu permissions configuration"
            record.is_public = False
        else:
            record = SystemConfig(
                key=MENU_CONFIG_KEY,
                value=value,
                value_type="json",
                category=ConfigCategory.SYSTEM,
                description="Menu permissions configuration",
                is_public=False,
            )
            db.add(record)

        db.commit()
        return MenuConfigResponse(config=data)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save menu config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save menu config: {str(e)}"
        )
