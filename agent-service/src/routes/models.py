"""
模型管理路由
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import logging
import os

router = APIRouter(tags=["模型管理"])
logger = logging.getLogger(__name__)


@router.get("", summary="获取可用模型列表")
async def list_models() -> List[Dict[str, Any]]:
    """
    获取可用模型列表
    
    返回当前配置的DeepSeek模型信息
    """
    return [
        {
            "id": os.getenv("LLM_MODEL", "deepseek-chat"),
            "name": "DeepSeek Chat",
            "provider": "DeepSeek",
            "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
            "temperature_range": [0.0, 2.0],
            "default_temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "available": bool(os.getenv("OPENAI_API_KEY")),
        }
    ]


@router.post("/{model_id}/chat", summary="模型对话")
async def chat_with_model(
    model_id: str,
    messages: List[Dict[str, str]],
    system_prompt: str = None,
    temperature: float = None
) -> Dict[str, Any]:
    """
    使用指定模型进行对话
    
    - **model_id**: 模型ID
    - **messages**: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
    - **system_prompt**: 系统提示词（可选）
    - **temperature**: 温度参数（可选）
    """
    from ..core.llm_integration import deepseek_llm
    
    try:
        response = await deepseek_llm.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        return {
            "model": model_id,
            "response": response,
            "success": True
        }
    except Exception as e:
        logger.error(f"Model chat failed: {str(e)}", exc_info=True)
        return {
            "model": model_id,
            "error": str(e),
            "success": False
        }

