"""
文件监控模块 - 只读监控代码变更
"""
import asyncio
import logging
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class CodeChangeHandler(FileSystemEventHandler):
    """代码变更处理器（只读监控）"""
    
    def __init__(self, callback: Callable[[str], None], exclude_patterns: Set[str] = None):
        """
        初始化处理器
        
        Args:
            callback: 文件变更时的回调函数
            exclude_patterns: 排除的文件模式
        """
        super().__init__()
        self.callback = callback
        self.exclude_patterns = exclude_patterns or set()
        self.debounce_tasks: dict[str, asyncio.Task] = {}
        self.debounce_delay = 2.0  # 防抖延迟（秒）
    
    def should_ignore(self, file_path: str) -> bool:
        """判断是否应该忽略文件"""
        path_lower = file_path.lower()
        
        # 默认排除模式
        default_patterns = {
            "node_modules", ".git", "__pycache__", "*.log",
            ".pytest_cache", "venv", ".next", "dist", "build",
            ".coverage", ".env", ".idea", ".vscode", ".cursor"
        }
        
        all_patterns = self.exclude_patterns | default_patterns
        
        for pattern in all_patterns:
            if pattern in path_lower:
                return True
        
        # 排除隐藏文件和临时文件
        path_obj = Path(file_path)
        if path_obj.name.startswith('.'):
            return True
        
        return False
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改时触发"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # 跳过不需要监控的文件
        if self.should_ignore(file_path):
            return
        
        logger.debug(f"检测到文件变更: {file_path}")
        
        # 防抖处理：取消之前的任务
        if file_path in self.debounce_tasks:
            try:
                self.debounce_tasks[file_path].cancel()
            except:
                pass
        
        # 使用线程安全的方式创建任务
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有运行中的事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 创建新的延迟任务
        if loop.is_running():
            task = asyncio.create_task(
                self.handle_change_after_delay(file_path)
            )
            self.debounce_tasks[file_path] = task
        else:
            # 如果事件循环未运行，使用线程执行
            import threading
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(self.handle_change_after_delay(file_path))
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
    
    def on_created(self, event: FileSystemEvent):
        """文件创建时触发"""
        self.on_modified(event)
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除时触发"""
        self.on_modified(event)
    
    async def handle_change_after_delay(self, file_path: str):
        """延迟处理变更（防抖）"""
        try:
            await asyncio.sleep(self.debounce_delay)
            
            # 再次检查文件是否仍然存在（可能被删除）
            if Path(file_path).exists():
                logger.info(f"处理文件变更: {file_path}")
                await self.callback(file_path)
        except asyncio.CancelledError:
            logger.debug(f"取消处理文件变更: {file_path}")
        except Exception as e:
            logger.error(f"处理文件变更时出错: {file_path}, 错误: {e}")


class FileMonitor:
    """文件监控器"""
    
    def __init__(self, watch_path: str, callback: Callable[[str], None], exclude_patterns: Set[str] = None):
        """
        初始化文件监控器
        
        Args:
            watch_path: 监控的路径
            callback: 文件变更时的回调函数
            exclude_patterns: 排除的文件模式
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.exclude_patterns = exclude_patterns or set()
        self.observer: Observer = None
        self.is_running = False
    
    def start(self):
        """启动文件监控"""
        if self.is_running:
            logger.warning("文件监控已在运行")
            return
        
        if not self.watch_path.exists():
            logger.error(f"监控路径不存在: {self.watch_path}")
            return
        
        try:
            event_handler = CodeChangeHandler(self.callback, self.exclude_patterns)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.watch_path), recursive=True)
            self.observer.start()
            self.is_running = True
            logger.info(f"文件监控已启动: {self.watch_path}")
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            raise
    
    def stop(self):
        """停止文件监控"""
        if not self.is_running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_running = False
        logger.info("文件监控已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()




