"""
智能体标准化协议
定义智能体通信的标准接口和数据格式
"""
from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional, Dict
from enum import Enum
from datetime import datetime
import json
import uuid


class AgentStatus(str, Enum):
    """智能体状态"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Artifact:
    """标准化输出物"""
    artifact_id: str
    artifact_type: str  # "data", "text", "file", "model", etc.
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ExecutionMetadata:
    """执行元数据"""
    execution_id: str
    agent_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    retry_count: int = 0
    error_count: int = 0
    
    def to_dict(self):
        return {
            "execution_id": self.execution_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "retry_count": self.retry_count,
            "error_count": self.error_count
        }


@dataclass
class StandardTask:
    """标准化任务"""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "input_data": self.input_data,
            "context": self.context,
            "priority": self.priority.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class StandardResult:
    """标准化智能体结果"""
    success: bool
    output: Any
    artifacts: List[Artifact] = field(default_factory=list)
    execution_metadata: Optional[ExecutionMetadata] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    confidence: float = 1.0
    quality_score: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "success": self.success,
            "output": self.output,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "execution_metadata": self.execution_metadata.to_dict() if self.execution_metadata else None,
            "error": self.error,
            "error_code": self.error_code,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "next_actions": self.next_actions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandardResult":
        """从字典创建StandardResult"""
        artifacts = []
        if data.get("artifacts"):
            for a_data in data["artifacts"]:
                if isinstance(a_data, dict):
                    artifacts.append(Artifact(
                        artifact_id=a_data.get("artifact_id", str(uuid.uuid4())),
                        artifact_type=a_data.get("artifact_type", "data"),
                        content=a_data.get("content"),
                        metadata=a_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(a_data["created_at"]) if a_data.get("created_at") else datetime.utcnow()
                    ))
        
        execution_metadata = None
        if data.get("execution_metadata"):
            em_data = data["execution_metadata"]
            if isinstance(em_data, dict):
                if em_data.get("start_time"):
                    em_data["start_time"] = datetime.fromisoformat(em_data["start_time"])
                if em_data.get("end_time"):
                    em_data["end_time"] = datetime.fromisoformat(em_data["end_time"])
                execution_metadata = ExecutionMetadata(**em_data)
        
        return cls(
            success=data.get("success", False),
            output=data.get("output"),
            artifacts=artifacts,
            execution_metadata=execution_metadata,
            error=data.get("error"),
            error_code=data.get("error_code"),
            confidence=data.get("confidence", 1.0),
            quality_score=data.get("quality_score"),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            next_actions=data.get("next_actions", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentCapabilities:
    """智能体能力描述"""
    agent_id: str
    agent_name: str
    capabilities: Dict[str, str]  # capability_name -> description
    supported_task_types: List[str]
    supported_input_formats: List[str]
    supported_output_formats: List[str]
    max_concurrent_tasks: int = 1
    estimated_execution_time: Optional[float] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "capabilities": self.capabilities,
            "supported_task_types": self.supported_task_types,
            "supported_input_formats": self.supported_input_formats,
            "supported_output_formats": self.supported_output_formats,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "estimated_execution_time": self.estimated_execution_time,
            "resource_requirements": self.resource_requirements,
            "metadata": self.metadata
        }
    
    async def can_handle(self, task: StandardTask) -> bool:
        """检查是否能处理给定任务"""
        return task.task_type in self.supported_task_types


@dataclass
class CollaborationRequest:
    """智能体协作请求"""
    request_id: str
    from_agent_id: str
    to_agent_id: str
    request_type: str  # "data_request", "capability_request", "validation_request", etc.
    description: str
    required_data: Optional[Dict[str, Any]] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "request_id": self.request_id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "request_type": self.request_type,
            "description": self.description,
            "required_data": self.required_data,
            "priority": self.priority.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CollaborationResponse:
    """智能体协作响应"""
    response_id: str
    request_id: str
    from_agent_id: str
    to_agent_id: str
    accepted: bool
    result: Optional[StandardResult] = None
    reason: Optional[str] = None
    alternative_suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "accepted": self.accepted,
            "result": self.result.to_dict() if self.result else None,
            "reason": self.reason,
            "alternative_suggestions": self.alternative_suggestions,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

