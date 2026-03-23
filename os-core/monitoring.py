"""
监控和可观测性模块
提供性能监控、指标收集、告警等功能
"""
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """指标数据"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class PerformanceMetric:
    """性能指标"""
    operation: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: List[Metric] = []
        self._performance_metrics: List[PerformanceMetric] = []
        self._lock = Lock()
        self._max_metrics = 10000  # 最大保存指标数
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: Optional[str] = None):
        """记录指标"""
        with self._lock:
            metric = Metric(
                name=name,
                value=value,
                tags=tags or {},
                unit=unit
            )
            self._metrics.append(metric)
            
            # 限制指标数量
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def record_performance(self, operation: str, duration_ms: float, success: bool, metadata: Optional[Dict[str, Any]] = None):
        """记录性能指标"""
        with self._lock:
            perf_metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                metadata=metadata or {}
            )
            self._performance_metrics.append(perf_metric)
            
            # 限制性能指标数量
            if len(self._performance_metrics) > self._max_metrics:
                self._performance_metrics = self._performance_metrics[-self._max_metrics:]
    
    def get_metrics(self, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None, limit: int = 100) -> List[Metric]:
        """获取指标"""
        with self._lock:
            metrics = self._metrics.copy()
        
        # 过滤
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if tags:
            for key, value in tags.items():
                metrics = [m for m in metrics if m.tags.get(key) == value]
        
        # 排序（最新的在前）
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        
        return metrics[:limit]
    
    def get_performance_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计"""
        with self._lock:
            perf_metrics = self._performance_metrics.copy()
        
        # 过滤
        if operation:
            perf_metrics = [m for m in perf_metrics if m.operation == operation]
        
        if not perf_metrics:
            return {
                "count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "success_rate": 0
            }
        
        durations = [m.duration_ms for m in perf_metrics]
        successes = [m for m in perf_metrics if m.success]
        
        return {
            "count": len(perf_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "success_rate": len(successes) / len(perf_metrics) * 100
        }
    
    def clear_metrics(self):
        """清除所有指标"""
        with self._lock:
            self._metrics.clear()
            self._performance_metrics.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self._lock:
            metrics = self._metrics.copy()
            perf_metrics = self._performance_metrics.copy()
        
        # 按操作类型统计性能
        perf_by_operation = defaultdict(list)
        for pm in perf_metrics:
            perf_by_operation[pm.operation].append(pm)
        
        operation_stats = {}
        for op, pms in perf_by_operation.items():
            durations = [m.duration_ms for m in pms]
            successes = [m for m in pms if m.success]
            operation_stats[op] = {
                "count": len(pms),
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "success_rate": len(successes) / len(pms) * 100 if pms else 0
            }
        
        # 按指标名称统计
        metrics_by_name = defaultdict(list)
        for m in metrics:
            metrics_by_name[m.name].append(m.value)
        
        metrics_summary = {}
        for name, values in metrics_by_name.items():
            metrics_summary[name] = {
                "count": len(values),
                "avg": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0
            }
        
        return {
            "total_metrics": len(metrics),
            "total_performance_metrics": len(perf_metrics),
            "operation_stats": operation_stats,
            "metrics_summary": metrics_summary
        }


class PerformanceMonitor:
    """性能监控器（上下文管理器）"""
    
    def __init__(self, collector: MetricsCollector, operation: str, metadata: Optional[Dict[str, Any]] = None):
        self.collector = collector
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        
        self.collector.record_performance(
            operation=self.operation,
            duration_ms=duration_ms,
            success=success,
            metadata=self.metadata
        )
        
        return False  # 不抑制异常


# 全局指标收集器实例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def monitor_performance(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """性能监控装饰器/上下文管理器"""
    return PerformanceMonitor(get_metrics_collector(), operation, metadata)

