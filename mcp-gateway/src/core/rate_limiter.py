"""
工具调用频率限制器
基于数据库实现频率限制
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RateLimiter:
    """频率限制器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_rate_limit(
        self,
        tool_id: str,
        user_id: Optional[str] = None,
        max_calls_per_minute: Optional[int] = None,
        max_calls_per_hour: Optional[int] = None,
        max_calls_per_day: Optional[int] = None
    ) -> tuple:
        """
        检查是否超过频率限制
        
        Args:
            tool_id: 工具ID
            user_id: 用户ID（可选）
            max_calls_per_minute: 每分钟最大调用次数
            max_calls_per_hour: 每小时最大调用次数
            max_calls_per_day: 每天最大调用次数
        
        Returns:
            (是否允许, 错误消息)
        """
        try:
            from ..repositories.execution_repository import ExecutionRepository
            
            execution_repo = ExecutionRepository(self.db)
            
            now = datetime.utcnow()
            
            # 检查每分钟限制
            if max_calls_per_minute:
                calls_last_minute = execution_repo.get_call_frequency(
                    tool_id,
                    time_window_minutes=1
                )
                if calls_last_minute >= max_calls_per_minute:
                    return False, f"Rate limit exceeded: {calls_last_minute}/{max_calls_per_minute} calls per minute"
            
            # 检查每小时限制
            if max_calls_per_hour:
                calls_last_hour = execution_repo.get_call_frequency(
                    tool_id,
                    time_window_minutes=60
                )
                if calls_last_hour >= max_calls_per_hour:
                    return False, f"Rate limit exceeded: {calls_last_hour}/{max_calls_per_hour} calls per hour"
            
            # 检查每天限制
            if max_calls_per_day:
                calls_last_day = execution_repo.get_call_frequency(
                    tool_id,
                    time_window_minutes=24 * 60
                )
                if calls_last_day >= max_calls_per_day:
                    return False, f"Rate limit exceeded: {calls_last_day}/{max_calls_per_day} calls per day"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}", exc_info=True)
            # 出错时允许执行（fail-open策略）
            return True, None
    
    def get_rate_limit_info(
        self,
        tool_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取频率限制信息"""
        try:
            from ..repositories.execution_repository import ExecutionRepository
            
            execution_repo = ExecutionRepository(self.db)
            
            # 获取工具配置
            from ..repositories.tool_repository import ToolRepository
            tool_repo = ToolRepository(self.db)
            tool = tool_repo.get_by_id(tool_id)
            
            if not tool:
                return {
                    "tool_id": tool_id,
                    "rate_limits": {},
                    "current_usage": {}
                }
            
            config = tool.config or {}
            rate_limits = config.get("rate_limits", {})
            
            # 获取当前使用情况
            current_usage = {
                "calls_last_minute": execution_repo.get_call_frequency(tool_id, 1),
                "calls_last_hour": execution_repo.get_call_frequency(tool_id, 60),
                "calls_last_day": execution_repo.get_call_frequency(tool_id, 24 * 60)
            }
            
            return {
                "tool_id": tool_id,
                "rate_limits": rate_limits,
                "current_usage": current_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {str(e)}", exc_info=True)
            return {
                "tool_id": tool_id,
                "rate_limits": {},
                "current_usage": {}
            }

