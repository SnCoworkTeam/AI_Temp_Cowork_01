"""
用户行为模式分析
从执行历史中提取用户行为模式
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, func

logger = logging.getLogger(__name__)


class UserPattern:
    """用户行为模式"""
    
    def __init__(
        self,
        frequent_intents: List[Dict[str, Any]],
        preferred_services: List[Dict[str, Any]],
        time_patterns: Dict[str, Any],
        success_patterns: Dict[str, Any]
    ):
        self.frequent_intents = frequent_intents
        self.preferred_services = preferred_services
        self.time_patterns = time_patterns
        self.success_patterns = success_patterns
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "frequent_intents": self.frequent_intents,
            "preferred_services": self.preferred_services,
            "time_patterns": self.time_patterns,
            "success_patterns": self.success_patterns
        }


class UserPatternAnalyzer:
    """用户行为模式分析器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _extract_frequent_intents(
        self,
        history: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """提取频繁使用的意图"""
        intent_counts = {}
        
        for record in history:
            intent_type = record.get("intent_analysis", {}).get("task_type")
            if intent_type:
                intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
        
        # 排序并返回
        sorted_intents = sorted(
            intent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"intent_type": intent, "count": count, "frequency": count / len(history)}
            for intent, count in sorted_intents[:limit]
        ]
    
    def _extract_preferred_services(
        self,
        history: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """提取偏好的服务"""
        service_counts = {}
        
        for record in history:
            routing = record.get("routing_decision", {})
            target_service = routing.get("target_service")
            if target_service:
                service_counts[target_service] = service_counts.get(target_service, 0) + 1
        
        # 排序并返回
        sorted_services = sorted(
            service_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"service": service, "count": count, "frequency": count / len(history)}
            for service, count in sorted_services[:limit]
        ]
    
    def _extract_time_patterns(
        self,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取时间模式"""
        hour_counts = {}
        day_counts = {}
        
        for record in history:
            timestamp_str = record.get("orchestration_metadata", {}).get("execution_timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hour = timestamp.hour
                    day = timestamp.strftime('%A')
                    
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    day_counts[day] = day_counts.get(day, 0) + 1
                except Exception as e:
                    logger.debug(f"Failed to parse timestamp: {e}")
        
        # 找出最活跃的时间段
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        
        return {
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "hour_distribution": hour_counts,
            "day_distribution": day_counts
        }
    
    def _extract_success_patterns(
        self,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取成功模式"""
        total = len(history)
        if total == 0:
            return {"success_rate": 0.0, "total": 0}
        
        successful = sum(1 for record in history if record.get("success", False))
        success_rate = successful / total if total > 0 else 0.0
        
        # 按意图类型统计成功率
        intent_success = {}
        for record in history:
            intent_type = record.get("intent_analysis", {}).get("task_type")
            if intent_type:
                if intent_type not in intent_success:
                    intent_success[intent_type] = {"total": 0, "success": 0}
                intent_success[intent_type]["total"] += 1
                if record.get("success", False):
                    intent_success[intent_type]["success"] += 1
        
        intent_success_rates = {
            intent: data["success"] / data["total"] if data["total"] > 0 else 0.0
            for intent, data in intent_success.items()
        }
        
        return {
            "success_rate": success_rate,
            "total": total,
            "successful": successful,
            "intent_success_rates": intent_success_rates
        }
    
    async def analyze_user_patterns(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> Optional[UserPattern]:
        """
        分析用户行为模式
        
        Args:
            user_id: 用户ID
            days: 分析最近多少天的数据
            limit: 最多分析多少条记录
            
        Returns:
            用户行为模式
        """
        try:
            # 从agent-service的执行历史中获取数据
            # 这里需要调用agent-service的API或直接查询数据库
            # 假设有一个executions表存储执行记录
            
            # 由于agent-service使用内存存储，这里先返回None
            # 实际实现需要agent-service提供API或使用共享数据库
            
            logger.debug(f"Analyzing patterns for user {user_id} (last {days} days)")
            
            # TODO: 从agent-service获取执行历史
            # 这里先返回空模式，实际需要集成agent-service的API
            return UserPattern(
                frequent_intents=[],
                preferred_services=[],
                time_patterns={},
                success_patterns={"success_rate": 0.0, "total": 0}
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze user patterns: {e}", exc_info=True)
            return None
    
    def analyze_patterns_from_history(
        self,
        history: List[Dict[str, Any]]
    ) -> UserPattern:
        """
        从历史记录中分析模式（辅助方法）
        
        Args:
            history: 执行历史记录列表
            
        Returns:
            用户行为模式
        """
        if not history:
            return UserPattern(
                frequent_intents=[],
                preferred_services=[],
                time_patterns={},
                success_patterns={"success_rate": 0.0, "total": 0}
            )
        
        return UserPattern(
            frequent_intents=self._extract_frequent_intents(history),
            preferred_services=self._extract_preferred_services(history),
            time_patterns=self._extract_time_patterns(history),
            success_patterns=self._extract_success_patterns(history)
        )


def get_user_pattern_analyzer(db: Session) -> UserPatternAnalyzer:
    """获取用户模式分析器实例"""
    return UserPatternAnalyzer(db)


