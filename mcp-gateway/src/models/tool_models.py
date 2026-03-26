"""
工具相关数据模型
使用Pydantic进行数据验证和OpenAPI文档生成
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum


class ToolType(str, Enum):
    """工具类型枚举"""
    FUNCTION = "function"
    API = "api"
    SCRIPT = "script"
    WORKFLOW = "workflow"


class ToolStatus(str, Enum):
    """工具状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class ParameterSchema(BaseModel):
    """参数模式定义"""
    type: str = Field(..., description="参数类型", example="string")
    description: Optional[str] = Field(None, description="参数描述")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(False, description="是否必需")
    enum: Optional[List[Any]] = Field(None, description="枚举值列表")
    minimum: Optional[Union[int, float]] = Field(None, description="最小值")
    maximum: Optional[Union[int, float]] = Field(None, description="最大值")
    min_length: Optional[int] = Field(None, description="最小长度")
    max_length: Optional[int] = Field(None, description="最大长度")
    pattern: Optional[str] = Field(None, description="正则表达式模式")


class ToolDefinition(BaseModel):
    """工具定义模型"""
    name: str = Field(
        ...,
        description="工具名称（唯一标识符）",
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_-]+$",
        example="sap_query"
    )
    description: str = Field(
        ...,
        description="工具描述",
        min_length=1,
        max_length=500,
        example="查询SAP系统中的数据"
    )
    version: str = Field(
        default="1.0.0",
        description="工具版本",
        pattern=r"^\d+\.\d+\.\d+$",
        example="1.0.0"
    )
    tool_type: ToolType = Field(
        default=ToolType.FUNCTION,
        description="工具类型"
    )
    status: ToolStatus = Field(
        default=ToolStatus.ACTIVE,
        description="工具状态"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="工具参数定义（JSON Schema格式）",
        example={
            "table": {
                "type": "string",
                "description": "SAP表名",
                "required": True
            },
            "query": {
                "type": "string",
                "description": "查询条件",
                "required": False
            }
        }
    )
    required_parameters: List[str] = Field(
        default_factory=list,
        description="必需参数列表"
    )
    returns: Optional[Dict[str, Any]] = Field(
        None,
        description="返回值定义"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="工具元数据"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证工具名称格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("工具名称只能包含字母、数字、下划线和连字符")
        return v.lower()
    
    @model_validator(mode='after')
    def validate_required_parameters(self):
        """验证必需参数是否在参数定义中存在"""
        if self.required_parameters:
            params = self.parameters
            # 处理JSON Schema格式的parameters
            if isinstance(params, dict) and "properties" in params:
                # JSON Schema格式：参数在properties中
                param_names = set(params.get("properties", {}).keys())
            else:
                # 直接参数字典格式
                param_names = set(params.keys()) if isinstance(params, dict) else set()
            
            for req_param in self.required_parameters:
                if req_param not in param_names:
                    raise ValueError(f"必需参数 '{req_param}' 不在参数定义中")
        return self


class ToolRegisterRequest(BaseModel):
    """工具注册请求"""
    tool: ToolDefinition = Field(..., description="工具定义")
    overwrite: bool = Field(
        default=False,
        description="是否覆盖已存在的工具"
    )


class ToolRegisterResponse(BaseModel):
    """工具注册响应"""
    success: bool = Field(..., description="注册是否成功")
    tool_name: str = Field(..., description="工具名称")
    message: str = Field(..., description="响应消息")
    registered_at: datetime = Field(
        default_factory=datetime.now,
        description="注册时间"
    )


class ToolExecutionRequest(BaseModel):
    """工具执行请求"""
    parameters: Dict[str, Any] = Field(
        ...,
        description="工具执行参数",
        example={"table": "MARA", "query": "MATNR='123456'"}
    )
    timeout: Optional[int] = Field(
        default=30,
        description="执行超时时间（秒）",
        ge=1,
        le=300
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="执行元数据"
    )


class ToolExecutionResponse(BaseModel):
    """工具执行响应"""
    success: bool = Field(..., description="执行是否成功")
    tool_name: str = Field(..., description="工具名称")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    executed_at: datetime = Field(
        default_factory=datetime.now,
        description="执行时间"
    )


class ToolInfo(BaseModel):
    """工具信息响应"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    version: str = Field(..., description="工具版本")
    tool_type: ToolType = Field(..., description="工具类型")
    status: ToolStatus = Field(..., description="工具状态")
    parameters: Dict[str, Any] = Field(..., description="参数定义（JSON Schema格式）")
    required_parameters: List[str] = Field(..., description="必需参数")
    returns: Optional[Dict[str, Any]] = Field(None, description="返回值定义")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    registered_at: Optional[datetime] = Field(None, description="注册时间")
    
    @field_validator("tool_type", mode="before")
    @classmethod
    def validate_tool_type(cls, v):
        """验证并修复tool_type：如果类型不在枚举中，转换为FUNCTION"""
        if isinstance(v, str):
            if v not in ["function", "api", "script", "workflow"]:
                return ToolType.FUNCTION
            return ToolType(v)
        elif isinstance(v, ToolType):
            return v
        return ToolType.FUNCTION


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo] = Field(..., description="工具列表")
    total: int = Field(..., description="工具总数")
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=100, description="每页大小")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="错误发生时间"
    )
