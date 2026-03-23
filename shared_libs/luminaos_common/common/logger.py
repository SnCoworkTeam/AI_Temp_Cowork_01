"""
统一日志配置
提供统一的日志格式、级别和输出
"""
import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class StandardFormatter(logging.Formatter):
    """标准日志格式化器"""
    
    def __init__(self, use_colors: bool = False):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 时间戳
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 日志级别颜色（如果启用）
        if self.use_colors:
            colors = {
                'DEBUG': '\033[36m',    # 青色
                'INFO': '\033[32m',      # 绿色
                'WARNING': '\033[33m',   # 黄色
                'ERROR': '\033[31m',     # 红色
                'CRITICAL': '\033[35m',  # 紫色
            }
            reset = '\033[0m'
            level_color = colors.get(record.levelname, '')
            level = f"{level_color}{record.levelname}{reset}"
        else:
            level = record.levelname
        
        # 格式化消息
        message = f"[{timestamp}] {level:8s} | {record.name:20s} | {record.getMessage()}"
        
        # 添加异常信息
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_type: str = "standard",
    log_file: Optional[str] = None,
    use_colors: bool = True,
    json_format: bool = False
) -> logging.Logger:
    """
    设置统一的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 格式类型 ("standard", "json", "detailed")
        log_file: 日志文件路径（可选）
        use_colors: 是否使用颜色（仅标准格式）
        json_format: 是否使用JSON格式
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level or "INFO", logging.INFO)
    logger.setLevel(log_level)
    
    # 创建格式化器
    if json_format or format_type == "json":
        formatter = JSONFormatter()
    elif format_type == "detailed":
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = StandardFormatter(use_colors=use_colors)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志传播到根记录器
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器（使用默认配置）
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器
    """
    return setup_logger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，支持额外字段"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """处理日志消息，添加额外字段"""
        extra = kwargs.get('extra', {})
        if not hasattr(extra, 'extra_fields'):
            extra['extra_fields'] = {}
        extra['extra_fields'].update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs
