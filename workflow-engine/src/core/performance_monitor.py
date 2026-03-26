"""
工作流性能监控
收集节点和执行性能指标
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NodePerformanceMetrics:
    """节点性能指标"""
    
    def __init__(self):
        self.node_id: Optional[str] = None
        self.node_type: Optional[str] = None
        self.execution_count: int = 0
        self.total_duration: float = 0.0
        self.avg_duration: float = 0.0
        self.min_duration: float = float('inf')
        self.max_duration: float = 0.0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.success_rate: float = 0.0
        self.last_executed_at: Optional[datetime] = None
    
    def record_execution(
        self,
        duration: float,
        success: bool = True
    ):
        """记录执行"""
        self.execution_count += 1
        self.total_duration += duration
        self.avg_duration = self.total_duration / self.execution_count
        
        if duration < self.min_duration:
            self.min_duration = duration
        if duration > self.max_duration:
            self.max_duration = duration
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        self.success_rate = (self.success_count / self.execution_count) * 100
        self.last_executed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "execution_count": self.execution_count,
            "total_duration": self.total_duration,
            "avg_duration": self.avg_duration,
            "min_duration": self.min_duration if self.min_duration != float('inf') else 0.0,
            "max_duration": self.max_duration,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None
        }


class WorkflowPerformanceMonitor:
    """工作流性能监控器"""
    
    def __init__(self, db: Session):
        self.db = db
        self._node_metrics: Dict[str, NodePerformanceMetrics] = {}
        self._workflow_metrics: Dict[str, Dict[str, Any]] = {}
    
    def record_node_execution(
        self,
        workflow_id: str,
        node_id: str,
        node_type: str,
        duration: float,
        success: bool = True
    ):
        """
        记录节点执行
        
        Args:
            workflow_id: 工作流ID
            node_id: 节点ID
            node_type: 节点类型
            duration: 执行耗时（秒）
            success: 是否成功
        """
        try:
            # 节点级别的指标
            node_key = f"{workflow_id}:{node_id}"
            if node_key not in self._node_metrics:
                metrics = NodePerformanceMetrics()
                metrics.node_id = node_id
                metrics.node_type = node_type
                self._node_metrics[node_key] = metrics
            else:
                metrics = self._node_metrics[node_key]
            
            metrics.record_execution(duration, success)
            
            # 工作流级别的指标
            if workflow_id not in self._workflow_metrics:
                self._workflow_metrics[workflow_id] = {
                    "total_executions": 0,
                    "total_node_executions": 0,
                    "avg_execution_time": 0.0,
                    "nodes": {}
                }
            
            workflow_metrics = self._workflow_metrics[workflow_id]
            workflow_metrics["total_node_executions"] += 1
            
            if node_id not in workflow_metrics["nodes"]:
                workflow_metrics["nodes"][node_id] = {
                    "execution_count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0
                }
            
            node_metrics = workflow_metrics["nodes"][node_id]
            node_metrics["execution_count"] += 1
            node_metrics["total_duration"] += duration
            node_metrics["avg_duration"] = node_metrics["total_duration"] / node_metrics["execution_count"]
            
            # 保存到数据库（定期批量保存）
            self._save_node_metrics_to_db(workflow_id, node_id, metrics)
            
        except Exception as e:
            logger.error(f"Error recording node execution: {str(e)}", exc_info=True)
    
    def record_workflow_execution(
        self,
        workflow_id: str,
        execution_id: str,
        duration: float,
        success: bool = True
    ):
        """
        记录工作流执行
        
        Args:
            workflow_id: 工作流ID
            execution_id: 执行ID
            duration: 执行耗时（秒）
            success: 是否成功
        """
        try:
            if workflow_id not in self._workflow_metrics:
                self._workflow_metrics[workflow_id] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "min_duration": float('inf'),
                    "max_duration": 0.0,
                    "success_rate": 0.0,
                    "last_executed_at": None
                }
            
            metrics = self._workflow_metrics[workflow_id]
            metrics["total_executions"] += 1
            metrics["total_duration"] += duration
            metrics["avg_duration"] = metrics["total_duration"] / metrics["total_executions"]
            
            if duration < metrics.get("min_duration", float('inf')):
                metrics["min_duration"] = duration
            if duration > metrics.get("max_duration", 0.0):
                metrics["max_duration"] = duration
            
            if success:
                metrics["successful_executions"] += 1
            else:
                metrics["failed_executions"] += 1
            
            metrics["success_rate"] = (metrics["successful_executions"] / metrics["total_executions"]) * 100
            metrics["last_executed_at"] = datetime.utcnow().isoformat()
            
            # 保存到数据库
            self._save_workflow_metrics_to_db(workflow_id, metrics)
            
        except Exception as e:
            logger.error(f"Error recording workflow execution: {str(e)}", exc_info=True)
    
    def get_node_metrics(
        self,
        workflow_id: str,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取节点性能指标
        
        Args:
            workflow_id: 工作流ID
            node_id: 节点ID（可选，如果为None则返回所有节点）
        
        Returns:
            节点性能指标字典
        """
        try:
            # 从数据库加载
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            executions = execution_repo.get_by_workflow_id(workflow_id, skip=0, limit=1000)
            
            node_stats: Dict[str, Dict[str, Any]] = {}
            
            for execution in executions:
                if execution.node_results:
                    for node_id_key, result in execution.node_results.items():
                        if node_id and node_id_key != node_id:
                            continue
                        
                        if node_id_key not in node_stats:
                            node_stats[node_id_key] = {
                                "execution_count": 0,
                                "total_duration": 0.0,
                                "success_count": 0,
                                "failure_count": 0
                            }
                        
                        stats = node_stats[node_id_key]
                        stats["execution_count"] += 1
                        
                        if isinstance(result, dict):
                            duration = result.get("duration", 0.0)
                            success = result.get("success", True)
                            stats["total_duration"] += duration
                            
                            if success:
                                stats["success_count"] += 1
                            else:
                                stats["failure_count"] += 1
            
            # 计算平均值
            for node_id_key, stats in node_stats.items():
                if stats["execution_count"] > 0:
                    stats["avg_duration"] = stats["total_duration"] / stats["execution_count"]
                    stats["success_rate"] = (stats["success_count"] / stats["execution_count"]) * 100
            
            return node_stats if not node_id else node_stats.get(node_id, {})
            
        except Exception as e:
            logger.error(f"Error getting node metrics: {str(e)}", exc_info=True)
            return {}
    
    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流性能指标
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            工作流性能指标字典
        """
        try:
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            stats = execution_repo.get_statistics(workflow_id=workflow_id)
            
            # 获取执行时间统计
            executions = execution_repo.get_by_workflow_id(workflow_id, skip=0, limit=1000)
            
            durations = []
            for execution in executions:
                if execution.execution_time:
                    durations.append(execution.execution_time)
            
            metrics = {
                "total_executions": stats.get("total", 0),
                "successful_executions": stats.get("completed", 0),
                "failed_executions": stats.get("failed", 0),
                "running_executions": stats.get("running", 0),
                "success_rate": stats.get("success_rate", 0.0)
            }
            
            if durations:
                metrics["avg_duration"] = sum(durations) / len(durations)
                metrics["min_duration"] = min(durations)
                metrics["max_duration"] = max(durations)
            else:
                metrics["avg_duration"] = 0.0
                metrics["min_duration"] = 0.0
                metrics["max_duration"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}", exc_info=True)
            return {}
    
    def _save_node_metrics_to_db(
        self,
        workflow_id: str,
        node_id: str,
        metrics: NodePerformanceMetrics
    ):
        """保存节点指标到数据库（更新工作流元数据）"""
        try:
            from ..repositories.workflow_repository import WorkflowRepository
            workflow_repo = WorkflowRepository(self.db)
            
            workflow = workflow_repo.get_by_id(workflow_id)
            if workflow:
                if workflow.metadata is None:
                    workflow.metadata = {}
                
                if "node_performance" not in workflow.metadata:
                    workflow.metadata["node_performance"] = {}
                
                workflow.metadata["node_performance"][node_id] = metrics.to_dict()
                self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to save node metrics to DB: {str(e)}")
            self.db.rollback()
    
    def _save_workflow_metrics_to_db(
        self,
        workflow_id: str,
        metrics: Dict[str, Any]
    ):
        """保存工作流指标到数据库（更新工作流元数据）"""
        try:
            from ..repositories.workflow_repository import WorkflowRepository
            workflow_repo = WorkflowRepository(self.db)
            
            workflow = workflow_repo.get_by_id(workflow_id)
            if workflow:
                if workflow.metadata is None:
                    workflow.metadata = {}
                
                workflow.metadata["performance_metrics"] = metrics
                self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to save workflow metrics to DB: {str(e)}")
            self.db.rollback()









