"""
批量处理优化
支持并发处理、优先级队列、资源限制
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ProcessingPriority(int, Enum):
    """处理优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class ProcessingTask:
    """处理任务"""
    task_id: str
    document_id: str
    priority: ProcessingPriority
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        if self.priority != other.priority:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


class BatchProcessor:
    """批量处理器"""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 100
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.queue: List[ProcessingTask] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        self._running = False
    
    async def start(self):
        """启动处理器"""
        self._running = True
        asyncio.create_task(self._process_queue())
        logger.info(f"BatchProcessor started with max_concurrent={self.max_concurrent}")
    
    async def stop(self):
        """停止处理器"""
        self._running = False
        # 等待所有任务完成
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        logger.info("BatchProcessor stopped")
    
    async def add_task(
        self,
        document_id: str,
        func: Callable,
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
        *args,
        **kwargs
    ) -> str:
        """
        添加处理任务
        
        Args:
            document_id: 文档ID
            func: 处理函数
            priority: 优先级
            *args: 函数参数
            **kwargs: 函数关键字参数
        
        Returns:
            任务ID
        """
        async with self._lock:
            if len(self.queue) >= self.max_queue_size:
                raise RuntimeError(f"Queue is full (max_size={self.max_queue_size})")
            
            task_id = str(uuid.uuid4())
            task = ProcessingTask(
                task_id=task_id,
                document_id=document_id,
                priority=priority,
                func=func,
                args=args,
                kwargs=kwargs
            )
            
            # 按优先级插入（保持排序）
            self.queue.append(task)
            self.queue.sort()
            
            logger.info(f"Task {task_id} added to queue (priority={priority.name}, queue_size={len(self.queue)})")
            return task_id
    
    async def _process_queue(self):
        """处理队列"""
        while self._running:
            async with self._lock:
                if not self.queue or len(self.running_tasks) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取下一个任务
                task = self.queue.pop(0)
            
            # 创建处理任务
            processing_task = asyncio.create_task(self._execute_task(task))
            self.running_tasks[task.task_id] = processing_task
    
    async def _execute_task(self, task: ProcessingTask):
        """执行任务"""
        async with self.semaphore:
            task.started_at = datetime.utcnow()
            logger.info(f"Task {task.task_id} started (document_id={task.document_id})")
            
            try:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    result = task.func(*task.args, **task.kwargs)
                
                task.result = result
                task.completed_at = datetime.utcnow()
                logger.info(f"Task {task.task_id} completed successfully")
            except Exception as e:
                task.error = e
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.task_id} failed: {str(e)}", exc_info=True)
            finally:
                async with self._lock:
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": len(self.queue),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent,
            "max_queue_size": self.max_queue_size,
            "queue_by_priority": {
                priority.name: sum(1 for t in self.queue if t.priority == priority)
                for priority in ProcessingPriority
            }
        }
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成"""
        start_time = datetime.utcnow()
        
        while True:
            # 检查运行中的任务
            if task_id in self.running_tasks:
                try:
                    await asyncio.wait_for(self.running_tasks[task_id], timeout=timeout)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Task {task_id} timeout after {timeout}s")
            
            # 检查队列中的任务
            async with self._lock:
                task = next((t for t in self.queue if t.task_id == task_id), None)
                if task:
                    # 任务还在队列中
                    await asyncio.sleep(0.1)
                    continue
                
                # 任务已完成，查找结果
                # 这里需要从已完成任务中查找（实际实现中应该维护已完成任务列表）
                break
            
            if timeout and (datetime.utcnow() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} timeout after {timeout}s")
            
            await asyncio.sleep(0.1)


# 全局批量处理器实例
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor(max_concurrent: int = 5) -> BatchProcessor:
    """获取批量处理器单例"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(max_concurrent=max_concurrent)
    return _batch_processor


