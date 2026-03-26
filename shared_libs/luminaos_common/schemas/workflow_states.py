"""
工作流状态定义 - 共享库
所有服务使用统一的状态定义，确保数据一致性
"""

from typing import TypedDict, Any, Optional, List, Dict, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


class WorkflowStateTypedDict(TypedDict, total=False):
    """工作流状态类型定义（用于类型提示）"""
    # 必需字段
    input_data: Dict[str, Any]
    node_results: Dict[str, Any]
    execution_history: List[Dict[str, Any]]
    
    # 可选字段
    current_node: Optional[str]
    error: Optional[str]
    final_result: Optional[Any]
    metadata: Dict[str, Any]
    execution_context: Dict[str, Any]
    thread_id: Optional[str]
    workflow_id: Optional[str]
    execution_id: Optional[str]
    start_time: Optional[float]


class WorkflowStateModel(BaseModel):
    """工作流状态模型（用于验证和序列化）"""
    # 必需字段
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="节点执行结果")
    execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="执行历史记录")
    
    # 可选字段
    current_node: Optional[str] = Field(default=None, description="当前节点ID")
    error: Optional[str] = Field(default=None, description="错误信息")
    final_result: Optional[Any] = Field(default=None, description="最终结果")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    thread_id: Optional[str] = Field(default=None, description="执行线程ID")
    workflow_id: Optional[str] = Field(default=None, description="工作流ID")
    execution_id: Optional[str] = Field(default=None, description="执行ID")
    start_time: Optional[float] = Field(default=None, description="开始时间戳")
    
    # Pydantic v2 配置
    model_config = ConfigDict(
        extra="allow",  # 允许额外字段用于动态扩展
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
        validate_assignment=True
    )
    
    def to_typed_dict(self) -> Dict[str, Any]:
        """转换为类型化字典"""
        return self.model_dump()
    
    @classmethod
    def create_initial_state(
        cls, 
        workflow_id: str, 
        input_data: Dict[str, Any] = None,
        thread_id: Optional[str] = None
    ) -> 'WorkflowStateModel':
        """创建初始状态"""
        if thread_id is None:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        return cls(
            input_data=input_data or {},
            node_results={},
            execution_history=[],
            metadata={
                "workflow_id": workflow_id,
                "start_time": datetime.utcnow().isoformat(),
                "thread_id": thread_id
            },
            execution_context={},
            workflow_id=workflow_id,
            thread_id=thread_id
        )


# 兼容性类型别名（LangGraph需要字典类型）
WorkflowState = Dict[str, Any]


def validate_workflow_state(state: Dict[str, Any]) -> bool:
    """验证工作流状态结构"""
    try:
        # 检查必需字段
        required_fields = ['input_data', 'node_results', 'execution_history']
        for field in required_fields:
            if field not in state:
                return False
        
        # 验证数据类型
        if not isinstance(state.get('input_data', {}), dict):
            return False
        if not isinstance(state.get('node_results', {}), dict):
            return False
        if not isinstance(state.get('execution_history', []), list):
            return False
        
        # 尝试使用Pydantic模型验证（如果可能）
        try:
            WorkflowStateModel(**state)
        except Exception:
            # 如果Pydantic验证失败，但基本字段存在，仍然返回True
            pass
        
        return True
    except Exception:
        return False


def create_workflow_state(
    workflow_id: str,
    input_data: Dict[str, Any] = None,
    thread_id: Optional[str] = None,
    **extra_fields
) -> WorkflowStateModel:
    """创建标准的工作流状态"""
    state = WorkflowStateModel.create_initial_state(workflow_id, input_data, thread_id)
    
    # 添加额外字段
    for key, value in extra_fields.items():
        setattr(state, key, value)
    
    return state


# 特定工作流的状态扩展
class AgentWorkflowState(WorkflowStateModel):
    """智能体工作流专用状态"""
    agent_id: Optional[str] = Field(default=None, description="智能体ID")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")
    
    @classmethod
    def create_agent_state(
        cls,
        workflow_id: str,
        agent_id: str,
        input_data: Dict[str, Any] = None,
        thread_id: Optional[str] = None
    ) -> 'AgentWorkflowState':
        """创建智能体工作流初始状态"""
        base_state = WorkflowStateModel.create_initial_state(workflow_id, input_data, thread_id)
        base_dict = base_state.model_dump()
        # 添加agent特定字段
        base_dict['agent_id'] = agent_id
        base_dict['conversation_history'] = []
        base_dict['user_context'] = {}
        return cls(**base_dict)


class MCPWorkflowState(WorkflowStateModel):
    """MCP工具工作流专用状态"""
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list, description="工具执行记录")
    available_tools: List[Dict[str, Any]] = Field(default_factory=list, description="可用工具列表")
    
    def record_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        success: bool = True,
        execution_time: Optional[float] = None
    ):
        """记录工具执行"""
        execution_record = {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": execution_time
        }
        self.tool_executions.append(execution_record)


# 导出常用函数和类
__all__ = [
    "WorkflowStateTypedDict",
    "WorkflowStateModel", 
    "WorkflowState",
    "validate_workflow_state",
    "create_workflow_state",
    "AgentWorkflowState",
    "MCPWorkflowState"
]

