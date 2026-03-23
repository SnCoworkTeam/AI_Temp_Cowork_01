"""
AI服务 - 集成DeepSeek模型
"""
import httpx
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("chat-service")


class DeepSeekService:
    """DeepSeek AI服务"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set, AI features will be limited")

        # 确保base_url以正确的格式结尾
        if not self.base_url.endswith("/v1"):
            if self.base_url.endswith("/"):
                self.base_url += "v1"
            else:
                self.base_url += "/v1"

    async def generate_response(
        self,
        messages: list,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用DeepSeek API生成响应

        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            model: 使用的模型名称
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            响应字典，包含content, model, tokens_used等信息
        """
        if not self.api_key:
            return {
                "content": "抱歉，AI服务暂时不可用。请联系管理员检查API配置。",
                "model": "fallback",
                "tokens_used": 0,
                "error": "API key not configured"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model or self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"Calling DeepSeek API: {self.base_url}/chat/completions")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    choice = result["choices"][0]

                    return {
                        "content": choice["message"]["content"],
                        "model": result.get("model", model or self.model),
                        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                        "finish_reason": choice.get("finish_reason"),
                        "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": result.get("usage", {}).get("completion_tokens", 0)
                    }
                else:
                    error_msg = f"DeepSeek API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "content": "抱歉，AI服务暂时遇到问题，请稍后再试。",
                        "model": "error",
                        "tokens_used": 0,
                        "error": error_msg
                    }

        except httpx.TimeoutException:
            error_msg = "DeepSeek API request timeout"
            logger.error(error_msg)
            return {
                "content": "抱歉，AI响应超时，请稍后再试。",
                "model": "timeout",
                "tokens_used": 0,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"DeepSeek API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "content": "抱歉，AI服务遇到技术问题，请稍后再试。",
                "model": "error",
                "tokens_used": 0,
                "error": error_msg
            }

    async def generate_chat_response(
        self,
        user_message: str,
        conversation_history: Optional[list] = None,
        system_prompt: Optional[str] = None,
        use_knowledge_base: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成聊天响应

        Args:
            user_message: 用户消息
            conversation_history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 系统提示
            use_knowledge_base: 是否使用知识库（TODO: 待实现）

        Returns:
            响应字典
        """
        # 构建消息列表
        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # 默认系统提示
            default_system = """你是一个智能AI助手，基于企业AI平台为用户提供帮助。请遵循以下原则：
1. 友好、专业且有帮助
2. 如果不确定答案，请诚实说明
3. 提供清晰、结构化的回答
4. 如果需要更多信息，请主动询问"""
            messages.append({"role": "system", "content": default_system})

        # 添加对话历史（限制长度以避免token超限）
        if conversation_history:
            # 只保留最近的10轮对话
            recent_history = conversation_history[-20:]  # 10轮 = 20条消息（用户+助手）
            messages.extend(recent_history)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        # TODO: 如果use_knowledge_base=True，这里应该先搜索知识库，
        # 然后将相关信息添加到system prompt中
        if use_knowledge_base:
            logger.info("Knowledge base integration not yet implemented")

        # 调用DeepSeek API
        return await self.generate_response(messages, **kwargs)

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        return {
            "api_key_configured": bool(self.api_key),
            "api_key_preview": f"{self.api_key[:10]}..." if self.api_key else None,
            "base_url": self.base_url,
            "model": self.model,
            "status": "configured" if self.api_key else "not_configured"
        }
