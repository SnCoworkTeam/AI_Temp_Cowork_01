"""共享通用工具模块"""
from .logger import setup_logger, get_logger, LoggerAdapter, LogLevel
from .error_handler import create_error_response, AppError, handle_exception
from .api_client import ApiClient
from .http_client import HTTPClient, HTTPClientError, TypedHTTPClient
from .config import (
    BaseConfig,
    ServiceConfig,
    DatabaseConfig,
    RedisConfig,
    CORSConfig,
    AIConfig,
    AppConfig,
    get_config,
    get_service_config,
    get_redis_config,
    get_database_config
)

__all__ = [
    # Logger
    'setup_logger',
    'get_logger',
    'LoggerAdapter',
    'LogLevel',
    # Error Handler
    'create_error_response',
    'AppError',
    'handle_exception',
    # HTTP Clients
    'ApiClient',
    'HTTPClient',
    'HTTPClientError',
    'TypedHTTPClient',
    # Config
    'BaseConfig',
    'ServiceConfig',
    'DatabaseConfig',
    'RedisConfig',
    'CORSConfig',
    'AIConfig',
    'AppConfig',
    'get_config',
    'get_service_config',
    'get_redis_config',
    'get_database_config',
]
