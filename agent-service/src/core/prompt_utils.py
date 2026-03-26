"""
提示词工具函数
提供便捷的提示词获取方法，统一管理所有提示词
"""
import logging
from typing import Optional
from .prompt_engine.template_manager import TemplateManager
from ..models.prompt_models import PromptTemplateConfig

logger = logging.getLogger(__name__)

# 全局模板管理器实例
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """获取全局模板管理器实例（单例模式）"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


def get_system_prompt(template_name: str, fallback: Optional[str] = None) -> str:
    """
    获取系统提示词
    
    Args:
        template_name: 模板名称（如 "metadata_agent", "data_query_agent" 等）
        fallback: 如果模板不存在，使用的后备提示词
    
    Returns:
        系统提示词字符串
    """
    try:
        template_manager = get_template_manager()
        template = template_manager.get_template_by_name(template_name)
        
        if template and template.system_prompt:
            return template.system_prompt
        
        if fallback:
            logger.warning(f"Template '{template_name}' not found, using fallback")
            return fallback
        
        logger.error(f"Template '{template_name}' not found and no fallback provided")
        return f"你是一个AI助手，负责处理{template_name}相关任务。"
    except Exception as e:
        logger.error(f"Failed to get system prompt for '{template_name}': {e}")
        return fallback or f"你是一个AI助手，负责处理{template_name}相关任务。"


def get_template_config(template_name: str) -> Optional[PromptTemplateConfig]:
    """
    获取完整的模板配置
    
    Args:
        template_name: 模板名称
    
    Returns:
        模板配置对象，如果不存在则返回None
    """
    try:
        template_manager = get_template_manager()
        return template_manager.get_template_by_name(template_name)
    except Exception as e:
        logger.error(f"Failed to get template config for '{template_name}': {e}")
        return None


def format_prompt(template_name: str, **kwargs) -> str:
    """
    格式化提示词（支持动态占位符）
    
    Args:
        template_name: 模板名称
        **kwargs: 动态参数（用于替换占位符）
    
    Returns:
        格式化后的提示词
    """
    try:
        template = get_template_config(template_name)
        if not template:
            return get_system_prompt(template_name)
        
        prompt = template.system_prompt
        
        # 替换动态占位符
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    except Exception as e:
        logger.error(f"Failed to format prompt for '{template_name}': {e}")
        return get_system_prompt(template_name)

