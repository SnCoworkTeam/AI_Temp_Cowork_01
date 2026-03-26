"""
动态工作流API路由
支持流式输出思考过程和执行过程
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json

from ..core.dynamic_execution_engine import DynamicExecutionEngine
from ..core.agents.state_manager import InMemoryStateStore

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局执行引擎实例（启用学习和状态持久化）
# 注意：需要在startup事件中调用initialize()来注册智能体
# 使用延迟初始化，避免在模块导入时执行
_dynamic_execution_engine = None

def get_dynamic_execution_engine() -> DynamicExecutionEngine:
    """获取动态执行引擎实例（单例模式）"""
    global _dynamic_execution_engine
    if _dynamic_execution_engine is None:
        _dynamic_execution_engine = DynamicExecutionEngine(
            enable_learning=True,
            enable_state_persistence=True,
            state_store=InMemoryStateStore()  # 生产环境可以替换为DatabaseStateStore
        )
    return _dynamic_execution_engine

# 为了向后兼容，保留dynamic_execution_engine变量
# 但使用函数获取，确保正确初始化
dynamic_execution_engine = None  # 将在startup事件中初始化


class DynamicWorkflowRequest(BaseModel):
    """动态工作流请求"""
    user_input: str = Field(..., description="用户输入")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    stream: bool = Field(True, description="是否流式输出")
    execution_id: Optional[str] = Field(None, description="执行ID（用于恢复）")
    resume: bool = Field(False, description="是否恢复执行")


@router.post("/dynamic-workflow/execute")
async def execute_dynamic_workflow(request: DynamicWorkflowRequest):
    """
    执行动态工作流（支持流式输出）
    
    流式输出包括：
    - 思考过程：请求分析、网络设计、验证优化
    - 执行过程：每层执行、每个智能体执行状态
    - 最终结果：合成结果
    """
    
    async def generate_stream():
        """生成流式输出"""
        try:
            logger.info(f"Starting dynamic workflow execution for: {request.user_input[:100]}")
            engine = get_dynamic_execution_engine()
            
            # 确保引擎已初始化
            if not engine._agents_registered:
                logger.info("Engine not initialized, initializing now...")
                await engine.initialize()
            
            logger.info("Starting workflow execution...")
            chunk_count = 0
            async for chunk in engine.execute_dynamic_workflow(
                user_input=request.user_input,
                context=request.context,
                stream=request.stream,
                execution_id=request.execution_id,
                resume=request.resume
            ):
                chunk_count += 1
                chunk_type = chunk.get('type', 'unknown')
                logger.debug(f"Yielding chunk {chunk_count}: {chunk_type}")
                
                # 验证错误chunk的完整性
                if chunk_type == 'error':
                    if not chunk.get('message') and not chunk.get('error'):
                        logger.warning(f"Error chunk {chunk_count} has empty message and error fields: {chunk}")
                        # 确保错误chunk有有效的错误信息
                        if not chunk.get('message'):
                            chunk['message'] = chunk.get('error') or '执行过程中发生未知错误'
                        if not chunk.get('error'):
                            chunk['error'] = chunk.get('message') or '执行过程中发生未知错误'
                
                # 格式化输出
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            logger.info(f"Workflow execution completed, sent {chunk_count} chunks")
                
        except Exception as e:
            logger.error(f"Dynamic workflow execution failed: {e}", exc_info=True)
            # 确保错误消息不为空
            error_msg = str(e) if e and str(e) else "动态工作流执行过程中发生未知错误"
            error_type = type(e).__name__ if e else "UnknownError"
            error_chunk = {
                "type": "error",
                "stage": "execution",
                "message": f"执行失败：{error_msg}",
                "error": error_msg,
                "error_type": error_type
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/dynamic-workflow/design")
async def design_workflow(request: DynamicWorkflowRequest):
    """
    仅设计工作流（不执行）
    """
    try:
        engine = get_dynamic_execution_engine()
        design_result = None
        async for chunk in engine.workflow_designer.design_for_request(
            request.user_input,
            request.context,
            stream=False
        ):
            if chunk.get("type") == "design_complete":
                design_result = chunk.get("design")
                break
        
        if not design_result:
            raise HTTPException(status_code=500, detail="Failed to design workflow")
        
        return {
            "success": True,
            "design": design_result
        }
        
    except Exception as e:
        logger.error(f"Workflow design failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

