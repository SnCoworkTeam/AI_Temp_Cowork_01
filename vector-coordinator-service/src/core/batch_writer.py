"""
批量写入管理器
实现实时+批量结合的持久化策略
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class BatchWriter:
    """批量写入管理器"""
    
    def __init__(
        self,
        write_interval: int = 120,  # 批量写入间隔（秒）
        batch_size: int = 100,  # 批量写入大小
        write_callback = None  # 写入回调函数
    ):
        """
        初始化批量写入管理器
        
        Args:
            write_interval: 批量写入间隔（秒）
            batch_size: 批量写入大小
            write_callback: 写入回调函数（async function(items: List[Dict]) -> bool）
        """
        self.write_interval = write_interval
        self.batch_size = batch_size
        self.write_callback = write_callback
        
        # 写入队列
        self.write_queue: deque = deque()
        self.last_write_time = datetime.now()
        
        # 后台任务
        self._background_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动后台批量写入任务"""
        if self._running:
            return
        
        self._running = True
        self._background_task = asyncio.create_task(self._batch_write_loop())
        logger.info("Batch writer started")
    
    async def stop(self):
        """停止后台任务并执行最后一次写入"""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        # 执行最后一次写入
        await self._flush()
        logger.info("Batch writer stopped")
    
    async def add_item(
        self,
        item: Dict[str, Any],
        priority: str = "normal"  # realtime, normal, batch
    ):
        """
        添加项目到写入队列
        
        Args:
            item: 要写入的项目
            priority: 优先级（realtime: 立即写入, normal: 批量写入, batch: 批量写入）
        """
        if priority == "realtime" and self.write_callback:
            # 实时写入
            try:
                success = await self.write_callback([item])
                if success:
                    logger.debug(f"Realtime write successful: {item.get('entity_uri', 'unknown')}")
                    return
            except Exception as e:
                logger.warning(f"Realtime write failed: {e}, adding to batch queue")
        
        # 添加到批量队列
        self.write_queue.append({
            "item": item,
            "priority": priority,
            "added_at": datetime.now()
        })
        
        # 如果队列达到批量大小，立即触发写入
        if len(self.write_queue) >= self.batch_size:
            await self._flush()
    
    async def _batch_write_loop(self):
        """后台批量写入循环"""
        while self._running:
            try:
                await asyncio.sleep(self.write_interval)
                
                # 检查是否需要写入
                time_since_last_write = (datetime.now() - self.last_write_time).total_seconds()
                if time_since_last_write >= self.write_interval and len(self.write_queue) > 0:
                    await self._flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch write loop error: {e}", exc_info=True)
    
    async def _flush(self):
        """执行批量写入"""
        if not self.write_callback or len(self.write_queue) == 0:
            return
        
        # 获取批量项目
        items_to_write = []
        batch_count = min(self.batch_size, len(self.write_queue))
        
        for _ in range(batch_count):
            if len(self.write_queue) > 0:
                entry = self.write_queue.popleft()
                items_to_write.append(entry["item"])
        
        if items_to_write:
            try:
                success = await self.write_callback(items_to_write)
                if success:
                    self.last_write_time = datetime.now()
                    logger.info(f"Batch write successful: {len(items_to_write)} items")
                else:
                    # 写入失败，重新加入队列
                    for item in items_to_write:
                        self.write_queue.append({
                            "item": item,
                            "priority": "batch",
                            "added_at": datetime.now()
                        })
            except Exception as e:
                logger.error(f"Batch write failed: {e}", exc_info=True)
                # 写入失败，重新加入队列
                for item in items_to_write:
                    self.write_queue.append({
                        "item": item,
                        "priority": "batch",
                        "added_at": datetime.now()
                    })
    
    def get_stats(self) -> Dict[str, Any]:
        """获取批量写入统计信息"""
        return {
            "queue_size": len(self.write_queue),
            "last_write_time": self.last_write_time.isoformat() if self.last_write_time else None,
            "write_interval": self.write_interval,
            "batch_size": self.batch_size,
            "running": self._running
        }







