"""
流式执行器
支持智能体的流式执行，实时返回执行过程
"""
import logging
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

import sys
from pathlib import Path

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared_libs"))

try:
    from luminaos_common.schemas.stream_schemas import (
        StreamMessage,
        StreamMessageType
    )
except ImportError:
    # 如果导入失败，使用本地定义
    from enum import Enum
    from typing import Any, Optional
    from pydantic import BaseModel, Field
    import time
    
    class StreamMessageType(str, Enum):
        START = "start"
        CHUNK = "chunk"
        STEP = "step"
        PROGRESS = "progress"
        COMPLETE = "complete"
        ERROR = "error"
        CANCEL = "cancel"
    
    class StreamMessage(BaseModel):
        type: StreamMessageType
        data: Optional[Any] = None
        progress: Optional[float] = None
        step: Optional[str] = None
        step_id: Optional[str] = None
        timestamp: float = Field(default_factory=time.time)
        execution_id: Optional[str] = None
        metadata: Optional[dict] = None
from .agent_manager import agent_manager
from .conversation_agent import conversation_agent
from .task_classifier import task_classifier, ExecutionStrategy
from .service_integration import service_integration

logger = logging.getLogger(__name__)


class StreamExecutor:
    """流式执行器"""
    
    def __init__(self):
        pass
    
    async def stream_intelligent_chat(
        self,
        message: str,
        conversation_history: Optional[list] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式智能对话处理
        
        Args:
            message: 用户消息
            conversation_history: 对话历史
            user_context: 用户上下文
            
        Yields:
            SSE格式的流式消息
        """
        execution_id = None
        
        try:
            # 发送开始消息
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.START,
                data={"message": "开始处理请求"},
                progress=0
            ))
            
            # 步骤1: 对话理解
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.STEP,
                step="对话理解",
                step_id="step_1",
                data={"status": "分析中..."},
                progress=10
            ))
            
            intent_analysis = await conversation_agent.understand_conversation(
                message, conversation_history, user_context
            )
            
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.STEP,
                step="对话理解",
                step_id="step_1",
                data={
                    "status": "完成",
                    "task_type": intent_analysis.task_type.value,
                    "confidence": intent_analysis.confidence
                },
                progress=20
            ))
            
            # 步骤2: 任务分类和路由决策
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.STEP,
                step="任务分类",
                step_id="step_2",
                data={"status": "分类中..."},
                progress=30
            ))
            
            available_agents = await agent_manager.list_agents()
            agents_dict = [{"id": a.id, "name": a.name, "capabilities": a.capabilities} for a in available_agents]
            
            routing_decision = await task_classifier.classify_and_route(
                intent_analysis, agents_dict
            )
            
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.STEP,
                step="任务分类",
                step_id="step_2",
                data={
                    "status": "完成",
                    "strategy": routing_decision.strategy.value,
                    "target_service": routing_decision.target_service
                },
                progress=40
            ))
            
            # 步骤3: 执行任务
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.STEP,
                step="执行任务",
                step_id="step_3",
                data={"status": "执行中..."},
                progress=50
            ))
            
            if routing_decision.strategy == ExecutionStrategy.DIRECT_LLM:
                # 直接使用LLM，支持流式输出
                if routing_decision.target_agent_id:
                    async for chunk in self._stream_agent_execution(
                        routing_decision.target_agent_id,
                        message,
                        user_context
                    ):
                        yield chunk
                else:
                    # 使用默认LLM流式输出
                    async for chunk in self._stream_llm_response(message):
                        yield chunk
            else:
                # 使用服务集成层执行
                result = await service_integration.execute_routing_decision(
                    routing_decision,
                    message,
                    user_context
                )
                
                yield self._format_sse_message(StreamMessage(
                    type=StreamMessageType.STEP,
                    step="执行任务",
                    step_id="step_3",
                    data={"status": "完成", "result": result},
                    progress=90
                ))
            
            # 发送完成消息
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.COMPLETE,
                data={"status": "执行完成"},
                progress=100
            ))
            
        except Exception as e:
            logger.error(f"Stream execution failed: {e}", exc_info=True)
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.ERROR,
                data={"error": str(e)},
                progress=0
            ))
    
    async def _stream_agent_execution(
        self,
        agent_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """流式执行智能体"""
        try:
            # 这里可以集成支持流式的LLM客户端
            # 目前先返回非流式结果
            result = await agent_manager.execute_agent(
                agent_id,
                task,
                context
            )
            
            # 模拟流式输出（将结果分块发送）
            if result.get("success") and result.get("output"):
                output = result["output"]
                chunk_size = 50  # 每50个字符一块
                
                for i in range(0, len(output), chunk_size):
                    chunk = output[i:i + chunk_size]
                    yield self._format_sse_message(StreamMessage(
                        type=StreamMessageType.CHUNK,
                        data={"chunk": chunk},
                        progress=50 + (i / len(output)) * 40
                    ))
                    await asyncio.sleep(0.05)  # 模拟延迟
        except Exception as e:
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.ERROR,
                data={"error": str(e)}
            ))
    
    async def _stream_llm_response(self, message: str) -> AsyncGenerator[str, None]:
        """流式LLM响应"""
        try:
            from .llm_integration import deepseek_llm
            
            # 如果LLM支持流式，使用流式接口
            # 目前先返回非流式结果
            response = await deepseek_llm.chat(
                messages=[{"role": "user", "content": message}],
                system_prompt="你是一个有用的AI助手。"
            )
            
            # 模拟流式输出
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield self._format_sse_message(StreamMessage(
                    type=StreamMessageType.CHUNK,
                    data={"chunk": chunk},
                    progress=50 + (i / len(response)) * 40
                ))
                await asyncio.sleep(0.05)
        except Exception as e:
            yield self._format_sse_message(StreamMessage(
                type=StreamMessageType.ERROR,
                data={"error": str(e)}
            ))
    
    def _format_sse_message(self, message: StreamMessage) -> str:
        """
        格式化SSE消息
        
        Args:
            message: 流式消息对象
            
        Returns:
            SSE格式的字符串
        """
        data = message.dict(exclude_none=True)
        json_data = json.dumps(data, ensure_ascii=False)
        return f"data: {json_data}\n\n"


# 全局流式执行器实例
stream_executor = StreamExecutor()

