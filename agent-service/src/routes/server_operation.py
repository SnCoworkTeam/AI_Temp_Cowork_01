"""
服务器操作智能体API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from ..core.agents.server_operation_agent import ServerOperationAgent
# LLMIntegration 不再需要，ServerOperationAgent 使用 deepseek_llm
# from ..core.llm_integration import LLMIntegration
from ..core.service_clients import ServiceClients

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/server-operation", tags=["server-operation"])


# 请求模型
class ServerOperationRequest(BaseModel):
    """服务器操作请求"""
    user_request: str  # 用户请求内容
    project_id: Optional[str] = None  # 项目ID（可选）
    context: Optional[Dict[str, Any]] = None  # 上下文信息（可选）
    auto_execute: bool = True  # 是否自动执行


class ServerOperationResponse(BaseModel):
    """服务器操作响应"""
    success: bool
    plan: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str


# 依赖注入：获取智能体实例
def get_server_operation_agent() -> ServerOperationAgent:
    """获取服务器操作智能体实例"""
    # 从配置或环境变量读取SSH配置
    import os

    ssh_config = {
        "host": os.getenv("SSH_HOST", "43.143.139.197"),
        "username": os.getenv("SSH_USERNAME", "ubuntu"),
        "private_key_path": os.getenv("SSH_PRIVATE_KEY_PATH", "/opt/enterprise-ai-platform/enterprise_ai_platform.pem"),
        "base_workdir": os.getenv("SSH_BASE_WORKDIR", "/opt/enterprise-ai-platform"),
        "port": int(os.getenv("SSH_PORT", "22")),
        "connection_timeout": int(os.getenv("SSH_CONNECTION_TIMEOUT", "30"))
    }

    # 创建智能体（使用默认的deepseek_llm）
    agent = ServerOperationAgent(
        ssh_config=ssh_config
    )

    return agent


@router.post("/execute", response_model=ServerOperationResponse)
async def execute_server_operation(
    request: ServerOperationRequest,
    agent: ServerOperationAgent = Depends(get_server_operation_agent)
):
    """
    执行服务器操作

    根据用户请求生成执行计划并执行服务器命令
    """
    try:
        logger.info(f"收到服务器操作请求: {request.user_request[:100]}...")

        # 处理请求
        result = await agent.process_request(
            user_request=request.user_request,
            project_id=request.project_id,
            context=request.context,
            auto_execute=request.auto_execute
        )

        if "error" in result:
            return ServerOperationResponse(
                success=False,
                error=result["error"],
                message="处理请求时发生错误"
            )

        # 构建响应
        execution_result = result.get("execution_result")
        success = execution_result.get("success", False) if execution_result else False

        return ServerOperationResponse(
            success=success,
            plan=result.get("plan"),
            execution_result=execution_result,
            message=execution_result.get("summary", "操作完成") if execution_result else "计划已生成"
        )

    except Exception as e:
        logger.error(f"执行服务器操作失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/plan", response_model=ServerOperationResponse)
async def generate_plan(
    request: ServerOperationRequest,
    agent: ServerOperationAgent = Depends(get_server_operation_agent)
):
    """
    仅生成执行计划，不执行

    用于预览和确认执行计划
    """
    try:
        logger.info(f"生成执行计划请求: {request.user_request[:100]}...")

        # 只生成计划，不执行
        plan = await agent.generate_plan(
            user_request=request.user_request,
            context=request.context
        )

        from ..core.agents.server_operation_agent import ExecutionPlan
        plan_dict = {
            "plan_name": plan.plan_name,
            "description": plan.description,
            "execution_mode": plan.execution_mode,
            "commands": plan.commands,
            "expected_outcomes": plan.expected_outcomes,
            "rollback_commands": plan.rollback_commands
        }

        return ServerOperationResponse(
            success=True,
            plan=plan_dict,
            message="执行计划生成成功"
        )

    except Exception as e:
        logger.error(f"生成执行计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成计划失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "server-operation-agent"
    }

