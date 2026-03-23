"""
意图识别性能监控
监控缓存命中率、识别延迟等指标
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time_ms: float = 0.0
    metadata_retrieval_time_ms: float = 0.0
    llm_time_ms: float = 0.0
    classification_time_ms: float = 0.0
    errors: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def avg_time_ms(self) -> float:
        """平均耗时（毫秒）"""
        return (self.total_time_ms / self.total_requests) if self.total_requests > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        """错误率"""
        return (self.errors / self.total_requests * 100) if self.total_requests > 0 else 0.0


class IntentPerformanceMonitor:
    """意图识别性能监控器"""
    
    def __init__(self, window_size: int = 100):
        """
        初始化性能监控器
        
        Args:
            window_size: 滑动窗口大小（保留最近N次请求的详细数据）
        """
        self.window_size = window_size
        self.metrics = PerformanceMetrics()
        self.recent_requests = deque(maxlen=window_size)
        self.lock = Lock()
        
        # 按任务类型统计
        self.task_type_stats = defaultdict(lambda: {
            "count": 0,
            "total_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        })
    
    def record_request(
        self,
        user_input: str,
        task_type: str,
        elapsed_time_ms: float,
        cache_hit: bool = False,
        metadata_time_ms: Optional[float] = None,
        llm_time_ms: Optional[float] = None,
        classification_time_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        记录一次请求
        
        Args:
            user_input: 用户输入
            task_type: 任务类型
            elapsed_time_ms: 总耗时（毫秒）
            cache_hit: 是否缓存命中
            metadata_time_ms: 元数据检索耗时
            llm_time_ms: LLM理解耗时
            classification_time_ms: 分类耗时
            success: 是否成功
            error: 错误信息（如果有）
        """
        with self.lock:
            self.metrics.total_requests += 1
            
            if cache_hit:
                self.metrics.cache_hits += 1
            else:
                self.metrics.cache_misses += 1
            
            if success:
                self.metrics.total_time_ms += elapsed_time_ms
                
                if metadata_time_ms:
                    self.metrics.metadata_retrieval_time_ms += metadata_time_ms
                if llm_time_ms:
                    self.metrics.llm_time_ms += llm_time_ms
                if classification_time_ms:
                    self.metrics.classification_time_ms += classification_time_ms
                
                # 按任务类型统计
                stats = self.task_type_stats[task_type]
                stats["count"] += 1
                stats["total_time_ms"] += elapsed_time_ms
                if cache_hit:
                    stats["cache_hits"] += 1
                else:
                    stats["cache_misses"] += 1
            else:
                self.metrics.errors += 1
            
            # 记录最近请求
            self.recent_requests.append({
                "timestamp": datetime.now(),
                "user_input": user_input[:50],  # 只保留前50个字符
                "task_type": task_type,
                "elapsed_time_ms": elapsed_time_ms,
                "cache_hit": cache_hit,
                "success": success,
                "error": error
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self.lock:
            return {
                "total_requests": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_rate": self.metrics.cache_hit_rate,
                "avg_time_ms": self.metrics.avg_time_ms,
                "total_time_ms": self.metrics.total_time_ms,
                "metadata_retrieval_time_ms": self.metrics.metadata_retrieval_time_ms,
                "llm_time_ms": self.metrics.llm_time_ms,
                "classification_time_ms": self.metrics.classification_time_ms,
                "errors": self.metrics.errors,
                "error_rate": self.metrics.error_rate,
                "last_reset": self.metrics.last_reset.isoformat(),
                "task_type_stats": dict(self.task_type_stats)
            }
    
    def get_recent_requests(self, limit: int = 10) -> list:
        """获取最近的请求记录"""
        with self.lock:
            return list(self.recent_requests)[-limit:]
    
    def reset(self):
        """重置指标"""
        with self.lock:
            self.metrics = PerformanceMetrics()
            self.recent_requests.clear()
            self.task_type_stats.clear()
            logger.info("Performance metrics reset")
    
    def get_summary(self) -> str:
        """获取性能摘要（字符串格式）"""
        metrics = self.get_metrics()
        return f"""
性能监控摘要:
  总请求数: {metrics['total_requests']}
  缓存命中率: {metrics['cache_hit_rate']:.1f}% ({metrics['cache_hits']}/{metrics['cache_hits'] + metrics['cache_misses']})
  平均耗时: {metrics['avg_time_ms']:.2f}ms
  元数据检索耗时: {metrics['metadata_retrieval_time_ms']:.2f}ms
  LLM理解耗时: {metrics['llm_time_ms']:.2f}ms
  分类耗时: {metrics['classification_time_ms']:.2f}ms
  错误率: {metrics['error_rate']:.1f}% ({metrics['errors']}/{metrics['total_requests']})
"""


# 全局监控器实例
_performance_monitor = None


def get_performance_monitor() -> IntentPerformanceMonitor:
    """获取性能监控器实例（单例）"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = IntentPerformanceMonitor()
    return _performance_monitor


