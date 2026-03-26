"""
JoyAgent Adapter Service Models

Data models for JoyAgent integration with the enterprise platform.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """JoyAgent task types"""
    QUERY = "query"
    REPORT_GENERATION = "report_generation"
    CODE_GENERATION = "code_generation"
    PPT_GENERATION = "ppt_generation"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    WORKFLOW_EXECUTION = "workflow_execution"
    CUSTOM = "custom"


class AgentMode(str, Enum):
    """JoyAgent execution modes"""
    REACT = "react"
    PLAN_AND_EXECUTE = "plan_and_execute"
    AUTO = "auto"


class JoyAgentTaskRequest(BaseModel):
    """Request model for creating a JoyAgent task"""
    query: str = Field(..., description="User query or task description")
    task_type: TaskType = Field(default=TaskType.QUERY, description="Type of task")
    mode: AgentMode = Field(default=AgentMode.AUTO, description="Agent execution mode")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task context")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task parameters")
    timeout: Optional[int] = Field(default=300, description="Task timeout in seconds")
    priority: int = Field(default=5, description="Task priority (1-10)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "生成一个关于最近美元和黄金走势的分析报告",
                "task_type": "report_generation",
                "mode": "auto",
                "parameters": {
                    "output_format": "pdf",
                    "include_charts": True,
                    "time_period": "30d"
                }
            }
        }


class JoyAgentTaskResponse(BaseModel):
    """Response model for JoyAgent task"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Task execution status")
    result: Optional[Any] = Field(default=None, description="Task execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    progress: int = Field(default=0, description="Task progress percentage (0-100)")
    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JoyAgentTaskList(BaseModel):
    """List of JoyAgent tasks with pagination"""
    tasks: List[JoyAgentTaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class JoyAgentCapability(BaseModel):
    """JoyAgent capability definition"""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    type: TaskType = Field(..., description="Task type this capability handles")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Required parameters")
    enabled: bool = Field(default=True, description="Whether capability is enabled")


class JoyAgentStatus(BaseModel):
    """JoyAgent service status"""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="JoyAgent version")
    uptime: int = Field(..., description="Service uptime in seconds")
    active_tasks: int = Field(..., description="Number of active tasks")
    total_tasks: int = Field(..., description="Total tasks processed")
    capabilities: List[JoyAgentCapability] = Field(..., description="Available capabilities")
    last_health_check: datetime = Field(..., description="Last health check timestamp")


class IntegrationContext(BaseModel):
    """Context for platform integration"""
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    workflow_id: Optional[str] = Field(default=None, description="Related workflow ID")
    metadata_id: Optional[str] = Field(default=None, description="Related metadata ID")
    knowledge_context: Optional[Dict[str, Any]] = Field(default=None, description="Knowledge base context")
    mcp_tools: Optional[List[str]] = Field(default=None, description="Available MCP tools")


class WorkflowIntegrationRequest(BaseModel):
    """Request for workflow integration with JoyAgent"""
    workflow_id: str = Field(..., description="Workflow identifier")
    step_name: str = Field(..., description="Workflow step name")
    joyagent_task: JoyAgentTaskRequest = Field(..., description="JoyAgent task configuration")
    integration_context: IntegrationContext = Field(..., description="Integration context")
    callback_url: Optional[str] = Field(default=None, description="Callback URL for results")


class KnowledgeEnhancementRequest(BaseModel):
    """Request for knowledge enhancement using JoyAgent"""
    query: str = Field(..., description="Knowledge query")
    knowledge_base_id: Optional[str] = Field(default=None, description="Knowledge base identifier")
    enhancement_type: str = Field(default="analysis", description="Type of enhancement")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Enhancement parameters")


class MCPToolIntegrationRequest(BaseModel):
    """Request for MCP tool integration with JoyAgent"""
    tool_name: str = Field(..., description="MCP tool name")
    action: str = Field(..., description="Tool action to perform")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    joyagent_context: Optional[Dict[str, Any]] = Field(default=None, description="JoyAgent context")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Service metrics")


class ConfigurationResponse(BaseModel):
    """Service configuration response"""
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    joyagent_version: str = Field(..., description="JoyAgent version")
    capabilities: List[JoyAgentCapability] = Field(..., description="Available capabilities")
    configuration: Dict[str, Any] = Field(..., description="Service configuration")
    integration_status: Dict[str, str] = Field(..., description="Integration status")