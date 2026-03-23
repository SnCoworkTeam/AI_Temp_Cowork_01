"""
统一错误代码定义

为所有服务提供标准化的错误代码体系
"""
from enum import Enum


class ErrorCode(str, Enum):
    """标准错误代码"""

    # 1xx - 一般错误
    INTERNAL_ERROR = "ERR_001"
    SERVICE_UNAVAILABLE = "ERR_002"
    TIMEOUT = "ERR_003"

    # 4xx - 客户端错误
    VALIDATION_ERROR = "ERR_400"
    AUTHENTICATION_REQUIRED = "ERR_401"
    AUTHENTICATION_FAILED = "ERR_401_FAILED"
    TOKEN_EXPIRED = "ERR_401_EXPIRED"
    AUTHORIZATION_ERROR = "ERR_403"
    RESOURCE_NOT_FOUND = "ERR_404"
    METHOD_NOT_ALLOWED = "ERR_405"
    CONFLICT_ERROR = "ERR_409"
    UNPROCESSABLE_ENTITY = "ERR_422"
    RATE_LIMIT_EXCEEDED = "ERR_429"

    # 5xx - 服务器错误
    DATABASE_ERROR = "ERR_500_DB"
    EXTERNAL_SERVICE_ERROR = "ERR_500_EXT"

    # 业务错误 - 数据库相关
    DB_CONNECTION_FAILED = "ERR_DB_001"
    DB_INTEGRITY_ERROR = "ERR_DB_002"
    DB_UNIQUE_VIOLATION = "ERR_DB_003"
    DB_FOREIGN_KEY_VIOLATION = "ERR_DB_004"
    DB_TRANSACTION_ERROR = "ERR_DB_005"

    # 业务错误 - 认证相关
    USER_NOT_FOUND = "ERR_AUTH_001"
    INVALID_CREDENTIALS = "ERR_AUTH_002"
    ACCOUNT_DISABLED = "ERR_AUTH_003"
    ACCOUNT_LOCKED = "ERR_AUTH_004"
    WEAK_PASSWORD = "ERR_AUTH_005"
    SSO_ERROR = "ERR_AUTH_SSO"

    # 业务错误 - 工作流相关
    WORKFLOW_NOT_FOUND = "ERR_WF_001"
    WORKFLOW_EXECUTION_FAILED = "ERR_WF_002"
    WORKFLOW_NODE_ERROR = "ERR_WF_003"
    WORKFLOW_TIMEOUT = "ERR_WF_004"

    # 业务错误 - MCP工具相关
    TOOL_NOT_FOUND = "ERR_TOOL_001"
    TOOL_EXECUTION_FAILED = "ERR_TOOL_002"
    TOOL_TIMEOUT = "ERR_TOOL_003"

    # 业务错误 - 知识库相关
    DOCUMENT_NOT_FOUND = "ERR_KB_001"
    DOCUMENT_UPLOAD_FAILED = "ERR_KB_002"
    SEARCH_FAILED = "ERR_KB_003"
    VECTOR_ERROR = "ERR_KB_004"


# 错误代码到HTTP状态码的映射
ERROR_CODE_TO_HTTP_STATUS = {
    # 1xx
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT: 504,

    # 4xx
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.AUTHENTICATION_FAILED: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.AUTHORIZATION_ERROR: 403,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.CONFLICT_ERROR: 409,
    ErrorCode.UNPROCESSABLE_ENTITY: 422,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,

    # 5xx
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.EXTERNAL_SERVICE_ERROR: 502,

    # 数据库
    ErrorCode.DB_CONNECTION_FAILED: 503,
    ErrorCode.DB_INTEGRITY_ERROR: 409,
    ErrorCode.DB_UNIQUE_VIOLATION: 409,
    ErrorCode.DB_FOREIGN_KEY_VIOLATION: 422,
    ErrorCode.DB_TRANSACTION_ERROR: 500,

    # 认证
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.ACCOUNT_DISABLED: 403,
    ErrorCode.ACCOUNT_LOCKED: 403,
    ErrorCode.WEAK_PASSWORD: 422,
    ErrorCode.SSO_ERROR: 502,

    # 工作流
    ErrorCode.WORKFLOW_NOT_FOUND: 404,
    ErrorCode.WORKFLOW_EXECUTION_FAILED: 500,
    ErrorCode.WORKFLOW_NODE_ERROR: 500,
    ErrorCode.WORKFLOW_TIMEOUT: 504,

    # MCP工具
    ErrorCode.TOOL_NOT_FOUND: 404,
    ErrorCode.TOOL_EXECUTION_FAILED: 500,
    ErrorCode.TOOL_TIMEOUT: 504,

    # 知识库
    ErrorCode.DOCUMENT_NOT_FOUND: 404,
    ErrorCode.DOCUMENT_UPLOAD_FAILED: 500,
    ErrorCode.SEARCH_FAILED: 500,
    ErrorCode.VECTOR_ERROR: 500,
}


# 错误代码的用户友好消息
ERROR_CODE_MESSAGES = {
    ErrorCode.INTERNAL_ERROR: "An internal server error occurred",
    ErrorCode.VALIDATION_ERROR: "Validation error",
    ErrorCode.AUTHENTICATION_FAILED: "Authentication failed",
    ErrorCode.AUTHORIZATION_ERROR: "Access denied",
    ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
    ErrorCode.CONFLICT_ERROR: "Resource conflict",
    ErrorCode.DB_INTEGRITY_ERROR: "Data integrity constraint violation",
    ErrorCode.DB_UNIQUE_VIOLATION: "Duplicate entry",
    ErrorCode.DB_FOREIGN_KEY_VIOLATION: "Referenced resource does not exist",
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.INVALID_CREDENTIALS: "Invalid username or password",
    ErrorCode.WORKFLOW_NOT_FOUND: "Workflow not found",
    ErrorCode.TOOL_NOT_FOUND: "Tool not found",
    ErrorCode.DOCUMENT_NOT_FOUND: "Document not found",
}


def get_http_status(error_code: ErrorCode) -> int:
    """获取错误代码对应的HTTP状态码"""
    return ERROR_CODE_TO_HTTP_STATUS.get(error_code, 500)


def get_error_message(error_code: ErrorCode, default: str = None) -> str:
    """获取错误代码的用户友好消息"""
    return ERROR_CODE_MESSAGES.get(error_code, default or "An error occurred")
