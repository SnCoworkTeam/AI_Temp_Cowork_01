"""
提示词模板管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

# 尝试从database模块导入，如果失败则使用metadata-service的数据库
try:
    import sys
    import os
    # 优先使用 database 模块，确保 core 和 models 来自 /app/database/src 而不是 /app/src/core
    db_src_path = os.path.join(os.path.dirname(__file__), '../../../../database/src')
    sys.path.insert(0, db_src_path)
    sys.path.insert(0, '/app/database/src')
    from core.database import get_db
    from models.prompt_template import PromptTemplate, PromptTemplateVersion
except ImportError:
    # 如果导入失败，使用metadata-service的数据库连接
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('DB_USER', 'ai_user')}:{os.getenv('DB_PASSWORD', 'ai_password')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'ai_platform')}"
    )
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    # 尝试从database模块导入，如果失败则跳过
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../database/src'))
        sys.path.insert(0, '/app/database/src')
        from models.prompt_template import PromptTemplate, PromptTemplateVersion
    except ImportError:
        # 如果导入失败，使用None作为占位符
        PromptTemplate = None
        PromptTemplateVersion = None
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["prompts"])


# Pydantic模型
class PromptExample(BaseModel):
    """提示词示例"""
    user: str
    assistant: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PromptTemplateCreate(BaseModel):
    """创建提示词模板请求"""
    name: str = Field(..., description="提示词名称")
    category: str = Field(..., description="任务分类")
    description: Optional[str] = Field(None, description="描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    examples: Optional[List[PromptExample]] = Field(default_factory=list, description="Few-Shot示例")
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(2000, ge=100, le=8000, description="最大token数")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: float = Field(0.0, ge=0.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(0.0, ge=0.0, le=2.0, description="存在惩罚")
    stop_sequences: Optional[List[str]] = Field(default_factory=list, description="停止序列")
    output_format: Optional[Dict[str, Any]] = Field(None, description="输出格式定义")
    dynamic_placeholders: Optional[List[str]] = Field(default_factory=list, description="动态占位符列表")
    is_active: bool = Field(True, description="是否激活")
    created_by: Optional[str] = Field(None, description="创建人")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展元数据")


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板请求"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    examples: Optional[List[PromptExample]] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=0.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=0.0, le=2.0)
    stop_sequences: Optional[List[str]] = None
    output_format: Optional[Dict[str, Any]] = None
    dynamic_placeholders: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptTemplateResponse(BaseModel):
    """提示词模板响应"""
    id: int
    name: str
    category: str
    description: Optional[str]
    system_prompt: Optional[str]
    examples: Optional[List[Dict[str, Any]]]
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: Optional[List[str]]
    output_format: Optional[Dict[str, Any]]
    dynamic_placeholders: Optional[List[str]]
    version: int
    is_active: bool
    created_by: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptTestRequest(BaseModel):
    """测试提示词请求"""
    user_input: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class PromptTestResponse(BaseModel):
    """测试提示词响应"""
    prompt_text: str = Field(..., description="生成的完整提示词")
    estimated_tokens: Optional[int] = Field(None, description="预估token数")
    validation_result: Optional[Dict[str, Any]] = Field(None, description="验证结果")


@router.get("", response_model=List[PromptTemplateResponse])
async def list_prompts(
    category: Optional[str] = Query(None, description="任务分类筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（名称或描述）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """列出所有提示词模板"""
    try:
        if not PromptTemplate:
            logger.warning("PromptTemplate model not available")
            return []
        query = db.query(PromptTemplate)
        
        # 筛选条件
        filters = []
        if category:
            filters.append(PromptTemplate.category == category)
        if is_active is not None:
            filters.append(PromptTemplate.is_active == is_active)
        if search:
            filters.append(
                or_(
                    PromptTemplate.name.ilike(f"%{search}%"),
                    PromptTemplate.description.ilike(f"%{search}%")
                )
            )
        
        if filters:
            query = query.filter(and_(*filters))
        
        # 分页
        prompts = query.order_by(PromptTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 转换为响应格式（处理metadata_字段）
        result = []
        for prompt in prompts:
            try:
                if prompt is None:
                    continue
                prompt_dict = {
                    "id": getattr(prompt, "id", None),
                    "name": getattr(prompt, "name", ""),
                    "category": getattr(prompt, "category", ""),
                    "description": getattr(prompt, "description", None),
                    "system_prompt": getattr(prompt, "system_prompt", None),
                    "examples": getattr(prompt, "examples", None) or [],
                    "temperature": getattr(prompt, "temperature", 0.3),
                    "max_tokens": getattr(prompt, "max_tokens", 2000),
                    "top_p": getattr(prompt, "top_p", 0.9),
                    "frequency_penalty": getattr(prompt, "frequency_penalty", 0.0),
                    "presence_penalty": getattr(prompt, "presence_penalty", 0.0),
                    "stop_sequences": getattr(prompt, "stop_sequences", None) or [],
                    "output_format": getattr(prompt, "output_format", None),
                    "dynamic_placeholders": getattr(prompt, "dynamic_placeholders", None) or [],
                    "version": getattr(prompt, "version", 1),
                    "is_active": getattr(prompt, "is_active", True),
                    "created_by": getattr(prompt, "created_by", None),
                    "metadata": (
                        getattr(prompt, "metadata_", None)
                        if isinstance(getattr(prompt, "metadata_", None), (dict, list))
                        else {}
                    ),
                    "created_at": getattr(prompt, "created_at", None),
                    "updated_at": getattr(prompt, "updated_at", None),
                }
                result.append(prompt_dict)
            except Exception as e:
                logger.warning(f"Failed to convert prompt {getattr(prompt, 'id', 'unknown')}: {e}")
                continue
        
        return result
    except Exception as e:
        # 如果表不存在或其他错误，返回空列表
        logger.warning(f"Failed to list prompts: {e}")
        return []


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """获取单个提示词模板"""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    # 转换为响应格式（处理metadata_字段）
    prompt_dict = prompt.to_dict()
    if "metadata_" in prompt_dict:
        prompt_dict["metadata"] = prompt_dict.pop("metadata_", {})
    
    return prompt_dict


@router.post("", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt(
    prompt_data: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """创建新的提示词模板"""
    # 检查名称是否已存在
    existing = db.query(PromptTemplate).filter(PromptTemplate.name == prompt_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="提示词名称已存在")
    
    # 转换examples
    examples_json = None
    if prompt_data.examples:
        examples_json = [ex.dict() for ex in prompt_data.examples]
    
    # 创建提示词模板
    prompt = PromptTemplate(
        name=prompt_data.name,
        category=prompt_data.category,
        description=prompt_data.description,
        system_prompt=prompt_data.system_prompt,
        examples=examples_json,
        temperature=prompt_data.temperature,
        max_tokens=prompt_data.max_tokens,
        top_p=prompt_data.top_p,
        frequency_penalty=prompt_data.frequency_penalty,
        presence_penalty=prompt_data.presence_penalty,
        stop_sequences=prompt_data.stop_sequences,
        output_format=prompt_data.output_format,
        dynamic_placeholders=prompt_data.dynamic_placeholders,
        is_active=prompt_data.is_active,
        created_by=prompt_data.created_by,
        metadata_=prompt_data.metadata,
        version=1
    )
    
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    # 创建版本历史
    version = PromptTemplateVersion(
        template_id=prompt.id,
        version=1,
        system_prompt=prompt.system_prompt,
        examples=examples_json,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        change_reason="初始版本",
        changed_by=prompt_data.created_by
    )
    db.add(version)
    db.commit()
    
    return prompt


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    prompt_id: int,
    prompt_data: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """更新提示词模板"""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    # 保存旧版本到版本历史
    old_version = PromptTemplateVersion(
        template_id=prompt.id,
        version=prompt.version,
        system_prompt=prompt.system_prompt,
        examples=prompt.examples,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        change_reason="更新前版本",
        changed_by=None
    )
    db.add(old_version)
    
    # 更新字段
    update_data = prompt_data.model_dump(exclude_unset=True)
    
    # 处理examples
    if "examples" in update_data and update_data["examples"] is not None:
        update_data["examples"] = [ex.dict() if isinstance(ex, PromptExample) else ex for ex in update_data["examples"]]
    
    # 处理metadata字段（转换为metadata_）
    if "metadata" in update_data:
        update_data["metadata_"] = update_data.pop("metadata")
    
    for key, value in update_data.items():
        setattr(prompt, key, value)
    
    # 版本号递增
    prompt.version += 1
    
    db.commit()
    db.refresh(prompt)
    
    return prompt


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: int,
    soft_delete: bool = Query(True, description="是否软删除（设为非激活）"),
    db: Session = Depends(get_db)
):
    """删除提示词模板"""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    if soft_delete:
        # 软删除：设为非激活
        prompt.is_active = False
        db.commit()
    else:
        # 硬删除：直接删除
        db.delete(prompt)
        db.commit()
    
    return None


@router.get("/{prompt_id}/versions", response_model=List[Dict[str, Any]])
async def get_prompt_versions(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """获取提示词模板的版本历史"""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    versions = db.query(PromptTemplateVersion).filter(
        PromptTemplateVersion.template_id == prompt_id
    ).order_by(PromptTemplateVersion.version.desc()).all()
    
    return [v.to_dict() for v in versions]


@router.post("/{prompt_id}/test", response_model=PromptTestResponse)
async def test_prompt(
    prompt_id: int,
    test_request: PromptTestRequest,
    db: Session = Depends(get_db)
):
    """测试提示词效果"""
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    # 构建完整提示词（这里简化处理，实际应该使用PromptEngine）
    prompt_text = ""
    if prompt.system_prompt:
        prompt_text += prompt.system_prompt + "\n\n"
    
    # 添加Few-Shot示例
    if prompt.examples:
        for example in prompt.examples:
            if isinstance(example, dict):
                prompt_text += f"用户: {example.get('user', '')}\n"
                prompt_text += f"助手: {example.get('assistant', '')}\n\n"
    
    # 添加用户输入
    prompt_text += f"用户输入: {test_request.user_input}\n"
    
    # 添加上下文
    if test_request.context:
        prompt_text += f"上下文: {json.dumps(test_request.context, ensure_ascii=False, indent=2)}\n"
    
    # 估算token数（简单估算：1 token ≈ 4字符）
    estimated_tokens = len(prompt_text) // 4
    
    return PromptTestResponse(
        prompt_text=prompt_text,
        estimated_tokens=estimated_tokens,
        validation_result={"status": "success", "message": "提示词构建成功"}
    )


@router.get("/categories/list", response_model=List[str])
async def list_categories(db: Session = Depends(get_db)):
    """获取所有任务分类列表"""
    try:
        if not PromptTemplate:
            logger.warning("PromptTemplate model not available")
            return []
        categories = db.query(PromptTemplate.category).distinct().all()
        result = []
        for cat in categories:
            try:
                # cat 可能是 sqlalchemy Row/RowMapping/tuple
                if isinstance(cat, (list, tuple)):
                    value = cat[0] if cat else None
                elif hasattr(cat, "__getitem__"):
                    try:
                        value = cat[0]
                    except Exception:
                        value = str(cat)
                else:
                    value = str(cat)
                if value:
                    result.append(value)
            except Exception:
                continue
        return result
    except Exception as e:
        # 如果表不存在，返回空列表
        logger.warning(f"Failed to fetch categories: {e}")
        return []

