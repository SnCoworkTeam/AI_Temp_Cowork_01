"""
提示词模板数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional, List
import json

from .base import BaseModel


class PromptTemplate(BaseModel):
    """提示词模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, index=True, comment="提示词名称")
    category = Column(String(100), nullable=False, index=True, comment="任务分类")
    description = Column(Text, comment="描述")
    
    # 提示词内容
    system_prompt = Column(Text, comment="系统提示词")
    examples = Column(JSON, comment="Few-Shot示例（JSON数组）")
    
    # LLM参数
    temperature = Column(Float, default=0.3, comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大token数")
    top_p = Column(Float, default=0.9, comment="Top-p参数")
    frequency_penalty = Column(Float, default=0.0, comment="频率惩罚")
    presence_penalty = Column(Float, default=0.0, comment="存在惩罚")
    stop_sequences = Column(JSON, comment="停止序列（JSON数组）")
    
    # 输出格式
    output_format = Column(JSON, comment="输出格式定义（JSON对象）")
    dynamic_placeholders = Column(JSON, comment="动态占位符列表（JSON数组）")
    
    # 版本和状态
    version = Column(Integer, default=1, nullable=False, comment="版本号")
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    
    # 元数据
    created_by = Column(String(100), comment="创建人")
    metadata_ = Column("metadata", JSON, comment="扩展元数据（JSON对象）")
    
    # 关联关系
    versions = relationship(
        "PromptTemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        # 处理JSON字段
        if isinstance(result.get("examples"), str):
            try:
                result["examples"] = json.loads(result["examples"])
            except:
                result["examples"] = []
        if isinstance(result.get("stop_sequences"), str):
            try:
                result["stop_sequences"] = json.loads(result["stop_sequences"])
            except:
                result["stop_sequences"] = []
        if isinstance(result.get("output_format"), str):
            try:
                result["output_format"] = json.loads(result["output_format"])
            except:
                result["output_format"] = None
        if isinstance(result.get("dynamic_placeholders"), str):
            try:
                result["dynamic_placeholders"] = json.loads(result["dynamic_placeholders"])
            except:
                result["dynamic_placeholders"] = []
        if isinstance(result.get("metadata"), str):
            try:
                result["metadata"] = json.loads(result["metadata"])
            except:
                result["metadata"] = {}
        # 处理metadata_字段（如果存在）
        if "metadata_" in result:
            result["metadata"] = result.pop("metadata_")
        return result


class PromptTemplateVersion(BaseModel):
    """提示词模板版本历史表"""
    __tablename__ = "prompt_template_versions"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False, index=True, comment="模板ID")
    version = Column(Integer, nullable=False, comment="版本号")
    
    # 提示词内容快照
    system_prompt = Column(Text, comment="系统提示词")
    examples = Column(JSON, comment="Few-Shot示例")
    temperature = Column(Float, comment="温度参数")
    max_tokens = Column(Integer, comment="最大token数")
    
    # 变更信息
    change_reason = Column(Text, comment="变更原因")
    changed_by = Column(String(100), comment="变更人")
    
    # 关联关系
    template = relationship("PromptTemplate", back_populates="versions")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        # 处理JSON字段
        if isinstance(result.get("examples"), str):
            try:
                result["examples"] = json.loads(result["examples"])
            except:
                result["examples"] = []
        return result

