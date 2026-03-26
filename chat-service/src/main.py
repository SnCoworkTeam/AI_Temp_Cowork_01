"""
Chat Service - AI助手对话管理服务
提供对话创建、消息发送、历史管理等功能
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

# 添加shared_libs和database到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_libs"))
# database模块路径：先添加database目录（用于database.xxx导入），再添加database/src（用于直接导入）
_database_root = str(Path(__file__).parent.parent.parent / "database")
_database_src = str(Path(__file__).parent.parent.parent / "database" / "src")
if _database_root not in sys.path:
    sys.path.insert(0, _database_root)
if _database_src not in sys.path:
    sys.path.insert(0, _database_src)

from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import AppError, create_error_response

# 导入路由
from .routes import conversations, chat

# 设置日志
logger = setup_logger("chat-service")

# 创建FastAPI应用
app = FastAPI(
    title="Chat Service",
    description="AI助手对话管理服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """处理应用自定义异常"""
    logger.error(f"Application error: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "请求数据验证失败",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return create_error_response(
        status_code=500,
        message="Internal server error",
        details="服务器内部错误" # 生产环境不应暴露详细错误信息
    )


# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "chat-service",
        "version": "1.0.0"
    }


# 注册路由
app.include_router(conversations.router, prefix="/api/v1", tags=["Conversations"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Chat Service starting up...")
    logger.info("Chat Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Chat Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
