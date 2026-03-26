"""
工具配置管理API路由
提供工具配置、凭据管理、版本管理等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body
from typing import Dict, Any, Optional
import logging

from ..services.tool_service import ToolService
from ..dependencies.database import get_db
from shared_libs.luminaos_common.common.logger import setup_logger
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tools", tags=["工具配置管理"])
logger = setup_logger(__name__)


def get_tool_service(db: Session = Depends(get_db)) -> ToolService:
    """获取工具服务"""
    from ..tools import tool_registry  # 使用全局单例实例
    return ToolService(db, tool_registry=tool_registry)


@router.get(
    "/{tool_name}/config",
    summary="获取工具配置",
    description="获取工具的完整配置信息",
    responses={
        200: {"description": "工具配置"},
        404: {"description": "工具不存在"}
    }
)
async def get_tool_config(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工具配置"""
    try:
        service = get_tool_service(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        config = service.get_tool_config(str(tool.id))
        
        return {
            "tool_id": str(tool.id),
            "tool_name": tool_name,
            "config": config,
            "parameters": tool.parameters or {},
            "version": tool.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool config: {str(e)}"
        )


@router.put(
    "/{tool_name}/config",
    summary="更新工具配置",
    description="更新工具的配置信息",
    responses={
        200: {"description": "配置更新成功"},
        404: {"description": "工具不存在"}
    }
)
async def update_tool_config(
    tool_name: str = Path(..., description="工具名称"),
    config: Dict[str, Any] = Body(..., description="配置更新"),
    merge: bool = Query(True, description="是否合并配置"),
    db: Session = Depends(get_db),
    changed_by: Optional[str] = None  # 可以从认证中间件获取
) -> Dict[str, Any]:
    """更新工具配置"""
    try:
        service = get_tool_service(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        success = service.update_tool_config(
            tool_id=str(tool.id),
            config=config,
            merge=merge
        )
        
        if success:
            # 记录配置变更审计
            from ..core.audit import AuditLogger
            audit_logger = AuditLogger(db)
            audit_logger.log_config_change(
                tool_id=str(tool.id),
                tool_name=tool_name,
                changed_by=changed_by,
                config_changes=config
            )
        
        return {
            "success": success,
            "message": "Tool config updated successfully" if success else "Failed to update tool config",
            "tool_name": tool_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating tool config: {str(e)}"
        )


@router.put(
    "/{tool_name}/credentials",
    summary="设置工具凭据",
    description="设置工具的认证凭据（加密存储）",
    responses={
        200: {"description": "凭据设置成功"},
        404: {"description": "工具不存在"}
    }
)
async def set_tool_credentials(
    tool_name: str = Path(..., description="工具名称"),
    credential_key: str = Query(..., description="凭据键名"),
    credential_value: Dict[str, Any] = Body(..., description="凭据值"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """设置工具凭据"""
    try:
        service = get_tool_service(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        success = service.set_credentials(
            tool_id=str(tool.id),
            credential_key=credential_key,
            credential_value=credential_value
        )
        
        return {
            "success": success,
            "message": "Credentials set successfully" if success else "Failed to set credentials",
            "tool_name": tool_name,
            "credential_key": credential_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting credentials: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error setting credentials: {str(e)}"
        )


@router.get(
    "/{tool_name}/version",
    summary="获取工具版本",
    description="获取工具的版本信息",
    responses={
        200: {"description": "版本信息"},
        404: {"description": "工具不存在"}
    }
)
async def get_tool_version(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工具版本"""
    try:
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return {
            "tool_id": str(tool.id),
            "tool_name": tool_name,
            "version": tool.version,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool version: {str(e)}"
        )


@router.put(
    "/{tool_name}/version",
    summary="更新工具版本",
    description="更新工具的版本号",
    responses={
        200: {"description": "版本更新成功"},
        404: {"description": "工具不存在"}
    }
)
async def update_tool_version(
    tool_name: str = Path(..., description="工具名称"),
    new_version: str = Query(..., description="新版本号"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新工具版本"""
    try:
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        success = tool_repo.update_tool_version(str(tool.id), new_version)
        
        if success:
            db.commit()
        
        return {
            "success": success,
            "message": "Tool version updated successfully" if success else "Failed to update tool version",
            "tool_name": tool_name,
            "old_version": tool.version,
            "new_version": new_version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool version: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating tool version: {str(e)}"
        )









