"""
性能分析器
分析执行历史，优化智能体选择
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExecutionRecord:
    """执行记录"""
    
    def __init__(
        self,
        execution_id: str,
        user_input: str,
        network_design: Dict[str, Any],
        agent_results: Dict[str, Any],
        execution_time: float,
        success: bool,
        created_at: datetime
    ):
        self.execution_id = execution_id
        self.user_input = user_input
        self.network_design = network_design
        self.agent_results = agent_results
        self.execution_time = execution_time
        self.success = success
        self.created_at = created_at


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.execution_history: List[ExecutionRecord] = []
    
    def add_execution_record(self, record: ExecutionRecord):
        """添加执行记录"""
        self.execution_history.append(record)
        # 保持最近1000条记录
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def analyze_agent_performance(
        self,
        agent_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        分析智能体性能
        
        Args:
            agent_id: 智能体ID
            time_window: 时间窗口（可选）
            
        Returns:
            性能指标
        """
        records = self._filter_records(time_window)
        
        agent_executions = []
        for record in records:
            if agent_id in record.agent_results:
                agent_result = record.agent_results[agent_id]
                if isinstance(agent_result, dict):
                    execution_metadata = agent_result.get("execution_metadata") or agent_result.get("result", {}).get("execution_metadata")
                    if execution_metadata:
                        agent_executions.append({
                            "execution_time": execution_metadata.get("execution_time", 0),
                            "success": agent_result.get("execution_success", False) or agent_result.get("success", False),
                            "created_at": record.created_at
                        })
        
        if not agent_executions:
            return {
                "agent_id": agent_id,
                "execution_count": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        successful = [e for e in agent_executions if e["success"]]
        avg_time = sum(e["execution_time"] for e in agent_executions) / len(agent_executions)
        
        return {
            "agent_id": agent_id,
            "execution_count": len(agent_executions),
            "success_count": len(successful),
            "failure_count": len(agent_executions) - len(successful),
            "success_rate": len(successful) / len(agent_executions) if agent_executions else 0.0,
            "average_execution_time": avg_time,
            "min_execution_time": min(e["execution_time"] for e in agent_executions),
            "max_execution_time": max(e["execution_time"] for e in agent_executions)
        }
    
    def analyze_network_pattern_performance(
        self,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析网络模式性能
        
        Args:
            pattern: 网络模式（智能体组合）
            
        Returns:
            性能指标
        """
        # 匹配相似的模式
        similar_records = []
        for record in self.execution_history:
            if self._patterns_match(record.network_design, pattern):
                similar_records.append(record)
        
        if not similar_records:
            return {
                "pattern": pattern,
                "execution_count": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        successful = [r for r in similar_records if r.success]
        avg_time = sum(r.execution_time for r in similar_records) / len(similar_records)
        
        return {
            "pattern": pattern,
            "execution_count": len(similar_records),
            "success_count": len(successful),
            "success_rate": len(successful) / len(similar_records) if similar_records else 0.0,
            "average_execution_time": avg_time
        }
    
    def find_best_pattern_for_request(
        self,
        user_input: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        为请求找到最佳执行模式
        
        Args:
            user_input: 用户输入
            limit: 返回数量限制
            
        Returns:
            最佳模式列表
        """
        # 简单的相似度匹配（可以改进为语义相似度）
        similar_records = []
        for record in self.execution_history:
            if record.success:
                # 简单的关键词匹配
                similarity = self._calculate_similarity(user_input, record.user_input)
                if similarity > 0.3:  # 相似度阈值
                    similar_records.append((similarity, record))
        
        # 按相似度排序
        similar_records.sort(key=lambda x: x[0], reverse=True)
        
        # 提取模式
        patterns = []
        for similarity, record in similar_records[:limit]:
            patterns.append({
                "similarity": similarity,
                "pattern": record.network_design,
                "performance": {
                    "execution_time": record.execution_time,
                    "success": record.success
                }
            })
        
        return patterns
    
    def _filter_records(self, time_window: Optional[timedelta]) -> List[ExecutionRecord]:
        """过滤记录"""
        if not time_window:
            return self.execution_history
        
        cutoff = datetime.utcnow() - time_window
        return [r for r in self.execution_history if r.created_at >= cutoff]
    
    def _patterns_match(
        self,
        pattern1: Dict[str, Any],
        pattern2: Dict[str, Any]
    ) -> bool:
        """检查两个模式是否匹配"""
        # 简单的匹配逻辑：检查智能体类型是否相同
        agents1 = {a.get("agent_type") for a in pattern1.get("agents", [])}
        agents2 = {a.get("agent_type") for a in pattern2.get("agents", [])}
        return agents1 == agents2
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        # 简单的关键词重叠度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        successful = [r for r in self.execution_history if r.success]
        avg_time = sum(r.execution_time for r in self.execution_history) / len(self.execution_history)
        
        # 按智能体统计
        agent_stats = defaultdict(lambda: {"count": 0, "success": 0, "total_time": 0.0})
        for record in self.execution_history:
            for agent_id, result in record.agent_results.items():
                agent_stats[agent_id]["count"] += 1
                if isinstance(result, dict) and (result.get("execution_success") or result.get("success")):
                    agent_stats[agent_id]["success"] += 1
                if isinstance(result, dict):
                    metadata = result.get("execution_metadata") or result.get("result", {}).get("execution_metadata")
                    if metadata and isinstance(metadata, dict):
                        agent_stats[agent_id]["total_time"] += metadata.get("execution_time", 0)
        
        agent_performance = {}
        for agent_id, stats in agent_stats.items():
            agent_performance[agent_id] = {
                "execution_count": stats["count"],
                "success_rate": stats["success"] / stats["count"] if stats["count"] > 0 else 0.0,
                "average_execution_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0.0
            }
        
        return {
            "total_executions": len(self.execution_history),
            "success_count": len(successful),
            "failure_count": len(self.execution_history) - len(successful),
            "success_rate": len(successful) / len(self.execution_history) if self.execution_history else 0.0,
            "average_execution_time": avg_time,
            "agent_performance": agent_performance
        }


