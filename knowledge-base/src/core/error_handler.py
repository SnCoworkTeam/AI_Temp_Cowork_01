"""
错误处理和重试机制
支持自动重试、错误详情记录、部分成功处理
"""
import logging
import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """错误类型"""
    NETWORK = "network"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ErrorDetail:
    """错误详情"""
    error_type: ErrorType
    message: str
    code: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retryable: bool = True


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 1.0  # 秒
    max_delay: float = 60.0  # 秒
    exponential_base: float = 2.0
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK,
        ErrorType.EMBEDDING,
        ErrorType.STORAGE
        # 注意：PARSING 错误默认不重试，因为通常是文件格式问题或文件太大
    ])


class RetryHandler:
    """重试处理器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        error_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        执行函数并自动重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            error_context: 错误上下文
            **kwargs: 函数关键字参数
        
        Returns:
            函数执行结果
        """
        last_error = None
        delay = self.config.initial_delay
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                error_detail = self._create_error_detail(e, error_context, attempt)
                
                # 检查是否可重试
                if not self._should_retry(error_detail, attempt):
                    logger.error(f"Non-retryable error after {attempt} attempts: {error_detail.message}")
                    raise
                
                if attempt < self.config.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {error_detail.message}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.exponential_base, self.config.max_delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} attempts failed: {error_detail.message}")
        
        # 所有重试都失败
        raise last_error
    
    def _should_retry(self, error_detail: ErrorDetail, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.config.max_retries:
            return False
        
        if not error_detail.retryable:
            return False
        
        if error_detail.error_type not in self.config.retryable_errors:
            return False
        
        return True
    
    def _create_error_detail(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]],
        attempt: int
    ) -> ErrorDetail:
        """创建错误详情"""
        import traceback
        
        error_type = self._classify_error(error)
        
        return ErrorDetail(
            error_type=error_type,
            message=str(error),
            code=type(error).__name__,
            stack_trace=traceback.format_exc(),
            context={
                **(context or {}),
                "attempt": attempt + 1,
                "max_retries": self.config.max_retries
            },
            retryable=self._is_retryable_error(error)
        )
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        error_name = type(error).__name__.lower()
        error_msg = str(error).lower()
        
        # 超时错误优先分类为解析错误（如果是文档解析超时）
        if "timeout" in error_msg and ("parsing" in error_msg or "document" in error_msg):
            return ErrorType.PARSING
        elif "network" in error_name or "connection" in error_msg or "timeout" in error_msg:
            return ErrorType.NETWORK
        elif "parse" in error_name or "parsing" in error_msg:
            return ErrorType.PARSING
        elif "embedding" in error_name or "embedding" in error_msg:
            return ErrorType.EMBEDDING
        elif "storage" in error_name or "database" in error_msg or "disk" in error_msg:
            return ErrorType.STORAGE
        elif "validation" in error_name or "invalid" in error_msg:
            return ErrorType.VALIDATION
        else:
            return ErrorType.UNKNOWN
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_type = self._classify_error(error)
        return error_type in self.config.retryable_errors


class PartialSuccessHandler:
    """部分成功处理器"""
    
    @staticmethod
    def handle_partial_success(
        results: List[Any],
        errors: List[ErrorDetail],
        total_items: int
    ) -> Dict[str, Any]:
        """
        处理部分成功的情况
        
        Args:
            results: 成功的结果列表
            errors: 错误列表
            total_items: 总项目数
        
        Returns:
            处理结果摘要
        """
        success_count = len(results)
        error_count = len(errors)
        
        return {
            "total": total_items,
            "success": success_count,
            "failed": error_count,
            "success_rate": success_count / total_items if total_items > 0 else 0.0,
            "results": results,
            "errors": [
                {
                    "type": err.error_type.value,
                    "message": err.message,
                    "code": err.code,
                    "context": err.context
                }
                for err in errors
            ]
        }



