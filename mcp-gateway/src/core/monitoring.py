"""
工具监控和审计
性能指标收集、错误率统计、告警
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ToolMonitor:
    """工具监控器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tool_metrics(
        self,
        tool_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取工具性能指标"""
        try:
            from ..repositories.execution_repository import ExecutionRepository
            from ..repositories.tool_repository import ToolRepository
            
            execution_repo = ExecutionRepository(self.db)
            tool_repo = ToolRepository(self.db)
            
            tool = tool_repo.get_by_id(tool_id)
            if not tool:
                return {
                    "tool_id": tool_id,
                    "error": "Tool not found"
                }
            
            # 获取执行统计
            stats = execution_repo.get_statistics(
                tool_id=tool_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # 获取执行记录计算详细指标
            executions = execution_repo.get_by_tool_id(tool_id, skip=0, limit=1000)
            
            if start_date or end_date:
                filtered_executions = []
                for exec in executions:
                    exec_time = exec.created_at if exec.created_at else exec.start_time
                    if exec_time:
                        if start_date and exec_time < start_date:
                            continue
                        if end_date and exec_time > end_date:
                            continue
                        filtered_executions.append(exec)
                executions = filtered_executions
            
            # 计算性能指标
            execution_times = []
            error_counts = {"total": 0, "timeout": 0, "failed": 0}
            
            for exec in executions:
                if exec.execution_time:
                    execution_times.append(exec.execution_time)
                
                if exec.status.value == "failed":
                    error_counts["failed"] += 1
                    error_counts["total"] += 1
                elif exec.status.value == "timeout":
                    error_counts["timeout"] += 1
                    error_counts["total"] += 1
            
            # 计算分位数
            execution_times_sorted = sorted(execution_times) if execution_times else []
            p50 = execution_times_sorted[len(execution_times_sorted) // 2] if execution_times_sorted else 0.0
            p95 = execution_times_sorted[int(len(execution_times_sorted) * 0.95)] if len(execution_times_sorted) > 0 else 0.0
            p99 = execution_times_sorted[int(len(execution_times_sorted) * 0.99)] if len(execution_times_sorted) > 0 else 0.0
            
            total_executions = len(executions)
            error_rate = (error_counts["total"] / total_executions * 100) if total_executions > 0 else 0.0
            
            return {
                "tool_id": tool_id,
                "tool_name": tool.name,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "statistics": {
                    "total_executions": total_executions,
                    "successful_executions": stats.get("successful", 0),
                    "failed_executions": stats.get("failed", 0),
                    "success_rate": stats.get("success_rate", 0.0),
                    "error_rate": error_rate,
                    "error_breakdown": error_counts
                },
                "performance": {
                    "avg_execution_time": stats.get("avg_duration_seconds", 0.0),
                    "min_execution_time": min(execution_times) if execution_times else 0.0,
                    "max_execution_time": max(execution_times) if execution_times else 0.0,
                    "p50_execution_time": p50,
                    "p95_execution_time": p95,
                    "p99_execution_time": p99
                },
                "call_count": tool.call_count,
                "success_count": tool.success_count,
                "failure_count": tool.failure_count
            }
            
        except Exception as e:
            logger.error(f"Error getting tool metrics: {str(e)}", exc_info=True)
            return {
                "tool_id": tool_id,
                "error": str(e)
            }
    
    def check_alerts(
        self,
        tool_id: str
    ) -> List[Dict[str, Any]]:
        """检查工具告警"""
        try:
            from ..repositories.tool_repository import ToolRepository
            from ..repositories.execution_repository import ExecutionRepository
            
            tool_repo = ToolRepository(self.db)
            execution_repo = ExecutionRepository(self.db)
            
            tool = tool_repo.get_by_id(tool_id)
            if not tool:
                return []
            
            alerts = []
            config = tool.config or {}
            alert_thresholds = config.get("alert_thresholds", {})
            
            # 获取最近1小时的统计
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            stats = execution_repo.get_statistics(
                tool_id=tool_id,
                start_date=one_hour_ago
            )
            
            # 检查错误率
            error_rate_threshold = alert_thresholds.get("error_rate", 10.0)  # 默认10%
            if stats.get("success_rate", 100.0) < (100.0 - error_rate_threshold):
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"Error rate exceeds threshold: {100.0 - stats.get('success_rate', 0.0):.1f}% > {error_rate_threshold}%",
                    "threshold": error_rate_threshold,
                    "current_value": 100.0 - stats.get("success_rate", 0.0)
                })
            
            # 检查平均执行时间
            avg_time_threshold = alert_thresholds.get("avg_execution_time", 5.0)  # 默认5秒
            if stats.get("avg_duration_seconds", 0.0) > avg_time_threshold:
                alerts.append({
                    "type": "high_execution_time",
                    "severity": "warning",
                    "message": f"Average execution time exceeds threshold: {stats.get('avg_duration_seconds', 0.0):.2f}s > {avg_time_threshold}s",
                    "threshold": avg_time_threshold,
                    "current_value": stats.get("avg_duration_seconds", 0.0)
                })
            
            # 检查调用频率异常
            call_frequency = execution_repo.get_call_frequency(tool_id, time_window_minutes=60)
            max_calls_threshold = alert_thresholds.get("max_calls_per_hour", 1000)
            if call_frequency > max_calls_threshold:
                alerts.append({
                    "type": "high_call_frequency",
                    "severity": "info",
                    "message": f"Call frequency exceeds threshold: {call_frequency} calls/hour > {max_calls_threshold}",
                    "threshold": max_calls_threshold,
                    "current_value": call_frequency
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}", exc_info=True)
            return []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统级监控指标"""
        try:
            from ..repositories.tool_repository import ToolRepository
            from ..repositories.execution_repository import ExecutionRepository
            
            tool_repo = ToolRepository(self.db)
            execution_repo = ExecutionRepository(self.db)
            
            # 获取所有工具
            tools = tool_repo.list_tools(skip=0, limit=10000)
            
            # 获取最近24小时的执行统计
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            system_stats = execution_repo.get_statistics(start_date=one_day_ago)
            
            # 统计活跃工具
            active_tools = [t for t in tools if t.status.value == "active"]
            
            # 计算总体成功率
            total_calls = sum(t.call_count for t in tools)
            total_success = sum(t.success_count for t in tools)
            overall_success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0.0
            
            return {
                "total_tools": len(tools),
                "active_tools": len(active_tools),
                "inactive_tools": len(tools) - len(active_tools),
                "total_calls": total_calls,
                "total_success": total_success,
                "total_failures": sum(t.failure_count for t in tools),
                "overall_success_rate": overall_success_rate,
                "recent_24h_stats": system_stats,
                "period": {
                    "start_date": one_day_ago.isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}", exc_info=True)
            return {
                "total_tools": 0,
                "active_tools": 0,
                "error": str(e)
            }

