"""
工具执行审计
记录执行审计和合规记录
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_execution(
        self,
        execution_id: str,
        tool_id: str,
        tool_name: str,
        executed_by: Optional[str],
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录执行审计日志"""
        try:
            # 使用AuditLog表记录审计信息
            from database.src.models.system_models import AuditLog, AuditAction
            
            executed_by_uuid = None
            if executed_by:
                try:
                    executed_by_uuid = UUID(executed_by)
                except ValueError:
                    pass
            
            audit_log = AuditLog(
                user_id=executed_by_uuid,
                action=AuditAction.EXECUTE,
                resource_type="mcp_tool",
                resource_id=tool_id,
                details={
                    "execution_id": execution_id,
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result_preview": str(result)[:500] if result else None,  # 只保存结果预览
                    "success": success,
                    "execution_time": execution_time,
                    "error_message": error_message
                },
                result="success" if success else "failure",
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=f"/api/tools/{tool_name}/execute",
                request_method="POST",
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging execution audit: {str(e)}", exc_info=True)
            self.db.rollback()
    
    def log_tool_registration(
        self,
        tool_id: str,
        tool_name: str,
        registered_by: Optional[str],
        action: str = "register"  # "register" or "unregister"
    ):
        """记录工具注册审计日志"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            registered_by_uuid = None
            if registered_by:
                try:
                    registered_by_uuid = UUID(registered_by)
                except ValueError:
                    pass
            
            audit_action = AuditAction.CREATE if action == "register" else AuditAction.DELETE
            
            audit_log = AuditLog(
                user_id=registered_by_uuid,
                action=audit_action,
                resource_type="mcp_tool",
                resource_id=tool_id,
                details={
                    "tool_name": tool_name,
                    "action": action
                },
                result="success",
                request_path=f"/api/tools/register",
                request_method="POST" if action == "register" else "DELETE",
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging tool registration audit: {str(e)}", exc_info=True)
            self.db.rollback()
    
    def log_config_change(
        self,
        tool_id: str,
        tool_name: str,
        changed_by: Optional[str],
        config_changes: Dict[str, Any]
    ):
        """记录配置变更审计日志"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            changed_by_uuid = None
            if changed_by:
                try:
                    changed_by_uuid = UUID(changed_by)
                except ValueError:
                    pass
            
            audit_log = AuditLog(
                user_id=changed_by_uuid,
                action=AuditAction.UPDATE,
                resource_type="mcp_tool_config",
                resource_id=tool_id,
                details={
                    "tool_name": tool_name,
                    "config_changes": config_changes
                },
                result="success",
                request_path=f"/api/tools/{tool_name}/config",
                request_method="PUT",
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging config change audit: {str(e)}", exc_info=True)
            self.db.rollback()

