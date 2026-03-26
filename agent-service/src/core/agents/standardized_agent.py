"""
标准化智能体基类
实现标准化的智能体接口和通信协议
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .protocols import (
    StandardTask, StandardResult, AgentCapabilities,
    CollaborationRequest, CollaborationResponse,
    AgentStatus, ExecutionMetadata, Artifact, TaskPriority
)

logger = logging.getLogger(__name__)


class StandardizedAgent(ABC):
    """标准化智能体基类"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Dict[str, str],
        supported_task_types: List[str],
        supported_input_formats: List[str] = None,
        supported_output_formats: List[str] = None
    ):
        """
        初始化标准化智能体
        
        Args:
            agent_id: 智能体ID
            name: 智能体名称
            description: 智能体描述
            capabilities: 能力字典
            supported_task_types: 支持的任务类型
            supported_input_formats: 支持的输入格式
            supported_output_formats: 支持的输出格式
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.supported_task_types = supported_task_types or []
        self.supported_input_formats = supported_input_formats or ["dict", "json"]
        self.supported_output_formats = supported_output_formats or ["dict", "json"]
        
        self.status = AgentStatus.IDLE
        self.current_task: Optional[StandardTask] = None
        self.execution_history: List[ExecutionMetadata] = []
        self.collaboration_handlers: Dict[str, callable] = {}
        
        # 注册默认协作处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的协作处理器"""
        self.collaboration_handlers = {
            "data_request": self._handle_data_request,
            "capability_request": self._handle_capability_request,
            "validation_request": self._handle_validation_request,
        }
    
    @abstractmethod
    async def analyze_task(
        self,
        task: StandardTask
    ) -> Dict[str, Any]:
        """
        分析任务（智能体特定的分析逻辑）
        
        Args:
            task: 标准化任务
            
        Returns:
            分析结果字典
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        task: StandardTask
    ) -> StandardResult:
        """
        执行任务（标准化接口）
        
        Args:
            task: 标准化任务
            
        Returns:
            标准化结果
        """
        pass
    
    async def execute_with_tracking(
        self,
        task: StandardTask
    ) -> StandardResult:
        """
        执行任务（带跟踪）
        
        Args:
            task: 标准化任务
            
        Returns:
            标准化结果（包含执行元数据）
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.status = AgentStatus.EXECUTING
        self.current_task = task
        
        execution_metadata = ExecutionMetadata(
            execution_id=execution_id,
            agent_id=self.agent_id,
            agent_name=self.name,
            start_time=start_time
        )
        
        try:
            # 执行任务
            result = await self.execute(task)
            
            # 更新执行元数据
            end_time = datetime.utcnow()
            execution_metadata.end_time = end_time
            execution_metadata.execution_time = (end_time - start_time).total_seconds()
            
            # 将执行元数据添加到结果
            result.execution_metadata = execution_metadata
            
            # 记录执行历史
            self.execution_history.append(execution_metadata)
            
            self.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
            
            return result
            
        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            execution_metadata.end_time = end_time
            execution_metadata.execution_time = (end_time - start_time).total_seconds()
            execution_metadata.error_count = 1
            
            self.status = AgentStatus.FAILED
            
            return StandardResult(
                success=False,
                output=None,
                execution_metadata=execution_metadata,
                error=str(e),
                error_code="EXECUTION_ERROR"
            )
        
        finally:
            self.current_task = None
            if self.status == AgentStatus.EXECUTING:
                self.status = AgentStatus.IDLE
    
    def get_capabilities(self) -> AgentCapabilities:
        """获取智能体能力描述"""
        return AgentCapabilities(
            agent_id=self.agent_id,
            agent_name=self.name,
            capabilities=self.capabilities,
            supported_task_types=self.supported_task_types,
            supported_input_formats=self.supported_input_formats,
            supported_output_formats=self.supported_output_formats
        )
    
    async def can_handle(self, task: StandardTask) -> bool:
        """检查是否能处理给定任务"""
        return task.task_type in self.supported_task_types
    
    async def handle_collaboration_request(
        self,
        request: CollaborationRequest
    ) -> CollaborationResponse:
        """
        处理协作请求
        
        Args:
            request: 协作请求
            
        Returns:
            协作响应
        """
        response_id = str(uuid.uuid4())
        
        # 检查是否有对应的处理器
        handler = self.collaboration_handlers.get(request.request_type)
        if not handler:
            return CollaborationResponse(
                response_id=response_id,
                request_id=request.request_id,
                from_agent_id=self.agent_id,
                to_agent_id=request.from_agent_id,
                accepted=False,
                reason=f"Unsupported request type: {request.request_type}"
            )
        
        try:
            # 调用处理器
            result = await handler(request)
            
            return CollaborationResponse(
                response_id=response_id,
                request_id=request.request_id,
                from_agent_id=self.agent_id,
                to_agent_id=request.from_agent_id,
                accepted=True,
                result=result
            )
            
        except Exception as e:
            logger.error(f"Collaboration request handling failed: {e}", exc_info=True)
            return CollaborationResponse(
                response_id=response_id,
                request_id=request.request_id,
                from_agent_id=self.agent_id,
                to_agent_id=request.from_agent_id,
                accepted=False,
                reason=str(e)
            )
    
    async def request_collaboration(
        self,
        target_agent: "StandardizedAgent",
        request_type: str,
        description: str,
        required_data: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> CollaborationResponse:
        """
        向其他智能体请求协作
        
        Args:
            target_agent: 目标智能体
            request_type: 请求类型
            description: 请求描述
            required_data: 所需数据
            priority: 优先级
            
        Returns:
            协作响应
        """
        request = CollaborationRequest(
            request_id=str(uuid.uuid4()),
            from_agent_id=self.agent_id,
            to_agent_id=target_agent.agent_id,
            request_type=request_type,
            description=description,
            required_data=required_data,
            priority=priority
        )
        
        return await target_agent.handle_collaboration_request(request)
    
    async def _handle_data_request(self, request: CollaborationRequest) -> StandardResult:
        """处理数据请求（默认实现，子类可覆盖）"""
        return StandardResult(
            success=False,
            output=None,
            error="Data request handler not implemented",
            error_code="NOT_IMPLEMENTED"
        )
    
    async def _handle_capability_request(self, request: CollaborationRequest) -> StandardResult:
        """处理能力请求（默认实现，子类可覆盖）"""
        capabilities = self.get_capabilities()
        return StandardResult(
            success=True,
            output=capabilities.to_dict()
        )
    
    async def _handle_validation_request(self, request: CollaborationRequest) -> StandardResult:
        """处理验证请求（默认实现，子类可覆盖）"""
        return StandardResult(
            success=False,
            output=None,
            error="Validation request handler not implemented",
            error_code="NOT_IMPLEMENTED"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task.task_id if self.current_task else None,
            "execution_count": len(self.execution_history),
            "last_execution": self.execution_history[-1].to_dict() if self.execution_history else None
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        if not self.execution_history:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "execution_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "average_execution_time": 0.0
            }
        
        successful = [e for e in self.execution_history if e.error_count == 0]
        failed = [e for e in self.execution_history if e.error_count > 0]
        
        avg_time = sum(e.execution_time for e in self.execution_history) / len(self.execution_history)
        
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "execution_count": len(self.execution_history),
            "success_count": len(successful),
            "failure_count": len(failed),
            "success_rate": len(successful) / len(self.execution_history) if self.execution_history else 0.0,
            "average_execution_time": avg_time,
            "total_execution_time": sum(e.execution_time for e in self.execution_history)
        }

