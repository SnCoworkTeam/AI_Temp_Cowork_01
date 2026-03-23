"""
AI客户端 - 从配置中心读取配置，直接调用LLM API
支持OpenAI兼容的API格式（包括DeepSeek）
"""
import httpx
import logging
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared_libs"))

try:
    from luminaos_common.clients.config_client import get_config_client
    CONFIG_CLIENT_AVAILABLE = True
except ImportError:
    CONFIG_CLIENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class AIClient:
    """AI客户端 - 从配置中心读取配置，调用LLM API"""
    
    def __init__(self):
        self.config_client = None
        self.api_key = None
        self.base_url = None
        self.default_model = None
        
        # 初始化配置客户端
        if CONFIG_CLIENT_AVAILABLE:
            try:
                self.config_client = get_config_client()
            except Exception as e:
                logger.warning(f"Failed to initialize config client: {e}")
        
        # 从配置中心加载配置（同步方式，启动时）
        self._load_config()
        
        if not self.api_key:
            logger.error(
                "LLM API Key 未配置，AI功能将无法使用。"
                "请在配置中心设置 llm.api_key 或在环境变量中设置 OPENAI_API_KEY"
            )
        
        logger.info(
            f"AIClient 初始化完成: "
            f"base_url={self.base_url or 'NOT CONFIGURED'}, "
            f"model={self.default_model or 'NOT CONFIGURED'}, "
            f"api_key={'已配置' if self.api_key else '未配置'}"
        )
    
    async def _load_config_async(self):
        """异步加载配置（从配置中心）"""
        if not self.config_client:
            return
        
        try:
            llm_config = await self.config_client.get_llm_config()
            
            if llm_config.get("api_key"):
                self.api_key = llm_config["api_key"]
            if llm_config.get("base_url"):
                base_url_raw = llm_config["base_url"].rstrip("/")
                if not base_url_raw.endswith("/v1"):
                    self.base_url = f"{base_url_raw}/v1"
                else:
                    self.base_url = base_url_raw
            if llm_config.get("model"):
                self.default_model = llm_config["model"]
            
            logger.info(f"AIClient config loaded from config center: model={self.default_model}, base_url={self.base_url}")
        except Exception as e:
            logger.error(f"Failed to load config from config center: {e}")
            # 降级到环境变量
            self._load_config_from_env()
    
    def _load_config(self):
        """同步加载配置（优先从配置中心，降级到环境变量）"""
        if self.config_client:
            # 尝试异步加载
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._load_config_async())
                else:
                    loop.run_until_complete(self._load_config_async())
            except RuntimeError:
                self._load_config_from_env()
        else:
            self._load_config_from_env()
    
    def _load_config_from_env(self):
        """从环境变量加载配置（降级方案）"""
        logger.warning("Using environment variables for LLM config (config center not available)")
        self.api_key = os.getenv("OPENAI_API_KEY")
        base_url_raw = os.getenv("LLM_BASE_URL", "").rstrip("/")
        if base_url_raw:
            if not base_url_raw.endswith("/v1"):
                self.base_url = f"{base_url_raw}/v1"
            else:
                self.base_url = base_url_raw
        self.default_model = os.getenv("LLM_MODEL")
        
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables or config center")
        if not self.base_url:
            logger.error("LLM_BASE_URL not found in environment variables or config center")
        if not self.default_model:
            logger.error("LLM_MODEL not found in environment variables or config center")
        
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: int = 2000,
                            **kwargs) -> Dict[str, Any]:
        """
        调用DeepSeek聊天补全API（非流式）
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置的模型
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他API参数
            
        Returns:
            包含响应内容的字典，格式为:
            {
                "content": str,
                "role": str,
                "usage": dict,
                "model": str,
                "finish_reason": str
            }
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                }
                
                # 添加其他参数
                payload.update(kwargs)
                
                logger.info(f"调用AI API: {self.base_url}, 模型: {payload['model']}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                usage = result.get('usage', {})
                logger.info(
                    f"AI API调用成功，使用token: "
                    f"prompt={usage.get('prompt_tokens', 0)}, "
                    f"completion={usage.get('completion_tokens', 0)}, "
                    f"total={usage.get('total_tokens', 0)}"
                )
                
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "role": result["choices"][0]["message"]["role"],
                    "usage": usage,
                    "model": result.get("model"),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }
                
        except httpx.TimeoutException:
            logger.error("AI API请求超时")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"AI API HTTP错误: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise

    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式调用DeepSeek API（用于实时输出）
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置的模型
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他API参数
            
        Yields:
            包含流式响应内容的字典，格式为:
            {
                "content": str,  # 增量内容
                "role": str,
                "finish_reason": Optional[str],  # 完成时为 "stop" 等
                "usage": Optional[dict]  # 完成时包含token使用统计
            }
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model or self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
                
                # 添加其他参数
                payload.update(kwargs)
                
                logger.info(f"流式调用AI API: {self.base_url}, 模型: {payload['model']}")
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # SSE格式: "data: {...}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 "data: " 前缀
                            
                            # 流结束标记
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                
                                # 提取增量内容
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    yield {
                                        "content": content,
                                        "role": delta.get("role", "assistant"),
                                        "finish_reason": None,
                                        "usage": None
                                    }
                                
                                # 检查是否完成
                                finish_reason = chunk_data.get("choices", [{}])[0].get("finish_reason")
                                if finish_reason:
                                    # 发送完成信号
                                    usage = chunk_data.get("usage")
                                    yield {
                                        "content": "",
                                        "role": "assistant",
                                        "finish_reason": finish_reason,
                                        "usage": usage
                                    }
                                    break
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"解析流式响应JSON失败: {e}, 数据: {data_str}")
                                continue
                                
        except httpx.TimeoutException:
            logger.error("AI API流式请求超时")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"AI API流式HTTP错误: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"AI API流式调用失败: {str(e)}")
            raise

