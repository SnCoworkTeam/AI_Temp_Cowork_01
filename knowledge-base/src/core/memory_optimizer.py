"""
内存优化器
用于降低文档处理过程中的内存占用
"""
import logging
import gc
import os
import psutil
from typing import List, Any, Optional, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MemoryOptimizer:
    """内存优化器"""

    def __init__(self, max_memory_mb: int = 1024):  # 增加到1GB，但通过批次大小控制实际使用
        """
        初始化内存优化器

        Args:
            max_memory_mb: 最大内存使用量(MB)
        """
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())

    def get_memory_usage_mb(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    def check_memory_threshold(self, threshold_percent: float = 0.8) -> bool:
        """
        检查是否超过内存阈值

        Args:
            threshold_percent: 阈值百分比 (0-1)

        Returns:
            是否超过阈值
        """
        current_mb = self.get_memory_usage_mb()
        threshold_mb = self.max_memory_mb * threshold_percent
        return current_mb > threshold_mb

    def force_gc(self):
        """强制垃圾回收"""
        gc.collect()
        logger.debug(f"GC completed. Memory usage: {self.get_memory_usage_mb():.2f} MB")

    @contextmanager
    def memory_monitor(self, operation_name: str):
        """
        内存监控上下文管理器

        Args:
            operation_name: 操作名称
        """
        start_memory = self.get_memory_usage_mb()
        logger.info(f"[{operation_name}] Starting. Memory: {start_memory:.2f} MB")

        try:
            yield
        finally:
            end_memory = self.get_memory_usage_mb()
            delta = end_memory - start_memory
            logger.info(f"[{operation_name}] Completed. Memory: {end_memory:.2f} MB (Δ {delta:+.2f} MB)")

            # 如果内存增长超过50MB，触发GC（更敏感）
            if delta > 50:
                logger.warning(f"Large memory increase detected: {delta:.2f} MB. Running GC...")
                self.force_gc()

    def calculate_optimal_batch_size(
        self,
        item_count: int,
        default_batch_size: int = 50,
        min_batch_size: int = 10,
        max_batch_size: int = 100
    ) -> int:
        """
        根据当前内存使用情况计算最优批次大小

        Args:
            item_count: 项目总数
            default_batch_size: 默认批次大小
            min_batch_size: 最小批次大小
            max_batch_size: 最大批次大小

        Returns:
            最优批次大小
        """
        current_memory = self.get_memory_usage_mb()
        available_memory = self.max_memory_mb - current_memory

        # 如果可用内存充足，使用默认批次大小
        if available_memory > 300:
            return min(default_batch_size, max_batch_size)

        # 如果可用内存较少，减小批次大小
        if available_memory < 150:
            batch_size = min_batch_size
        else:
            # 线性调整批次大小（更保守）
            ratio = available_memory / 300
            batch_size = int(min_batch_size + (default_batch_size - min_batch_size) * ratio * 0.8)  # 乘以0.8更保守

        logger.info(
            f"Calculated optimal batch size: {batch_size} "
            f"(available memory: {available_memory:.2f} MB)"
        )

        return max(min_batch_size, min(batch_size, max_batch_size))


class StreamingProcessor:
    """流式处理器 - 用于大文件处理"""

    @staticmethod
    def process_in_chunks(
        items: List[Any],
        processor: Callable,
        batch_size: int = 50,
        memory_optimizer: Optional[MemoryOptimizer] = None
    ) -> List[Any]:
        """
        分块处理大量数据

        Args:
            items: 待处理的项目列表
            processor: 处理函数
            batch_size: 批次大小
            memory_optimizer: 内存优化器

        Returns:
            处理结果列表
        """
        results = []
        total = len(items)

        # 动态调整批次大小
        if memory_optimizer:
            batch_size = memory_optimizer.calculate_optimal_batch_size(
                total, batch_size
            )

        for i in range(0, total, batch_size):
            batch = items[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

            # 处理批次
            batch_results = processor(batch)
            results.extend(batch_results)

            # 检查内存并清理
            if memory_optimizer:
                if memory_optimizer.check_memory_threshold(0.7):
                    logger.warning("Memory threshold reached, forcing GC...")
                    memory_optimizer.force_gc()

        return results

    @staticmethod
    async def process_in_chunks_async(
        items: List[Any],
        processor: Callable,
        batch_size: int = 50,
        memory_optimizer: Optional[MemoryOptimizer] = None
    ) -> List[Any]:
        """
        异步分块处理大量数据

        Args:
            items: 待处理的项目列表
            processor: 异步处理函数
            batch_size: 批次大小
            memory_optimizer: 内存优化器

        Returns:
            处理结果列表
        """
        import asyncio

        results = []
        total = len(items)

        # 动态调整批次大小
        if memory_optimizer:
            batch_size = memory_optimizer.calculate_optimal_batch_size(
                total, batch_size
            )

        for i in range(0, total, batch_size):
            batch = items[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

            # 异步处理批次
            batch_results = await processor(batch)
            results.extend(batch_results)

            # 检查内存并清理
            if memory_optimizer:
                if memory_optimizer.check_memory_threshold(0.7):
                    logger.warning("Memory threshold reached, forcing GC...")
                    memory_optimizer.force_gc()
                    # 给事件循环一点时间
                    await asyncio.sleep(0.1)

        return results


# 全局内存优化器实例
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer(max_memory_mb: int = None) -> MemoryOptimizer:
    """
    获取内存优化器单例

    Args:
        max_memory_mb: 最大内存使用量(MB)

    Returns:
        内存优化器实例
    """
    global _memory_optimizer

    if _memory_optimizer is None:
        # 从环境变量读取配置
        default_max_memory = int(os.getenv("MAX_MEMORY_MB", "512"))
        _memory_optimizer = MemoryOptimizer(
            max_memory_mb=max_memory_mb or default_max_memory
        )

    return _memory_optimizer
