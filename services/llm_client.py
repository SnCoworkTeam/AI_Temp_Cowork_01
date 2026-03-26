"""
健壮的DeepSeek LLM客户端
支持多层级调用，自动降级
支持流式输出（阶段2）
"""
import httpx
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CUSTOM = "custom"


class RobustDeepSeekClient:
    """
    健壮的DeepSeek客户端
    支持多种调用方式，自动降级
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
        timeout: float = 10.0,
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        self.timeout = timeout
        self.temperature = temperature
        
        # 清理base_url
        self.base_url = self.base_url.rstrip("/v1").rstrip("/")
        
        # 初始化策略：优先直接HTTP，降级到LangChain
        self.use_direct_http = True
        self.langchain_client = None
        self.http_client = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化客户端（多层级）"""
        # 策略1: 直接HTTP客户端（优先）
        try:
            self.http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            logger.info("HTTP客户端初始化成功（直接调用模式）")
        except Exception as e:
            logger.warning(f"HTTP客户端初始化失败: {e}")
            self.use_direct_http = False
        
        # 策略2: LangChain客户端（降级）
        if not self.use_direct_http or not self.api_key:
            try:
                from langchain_openai import ChatOpenAI
                self.langchain_client = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
                logger.info("LangChain客户端初始化成功（降级模式）")
            except Exception as e:
                logger.warning(f"LangChain客户端初始化失败: {e}")
                self.langchain_client = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全（多层级调用）
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数（temperature, max_tokens等）
        
        Returns:
            Dict: API响应
        """
        if not self.api_key:
            raise RuntimeError("API密钥未设置")
        
        # 策略1: 直接HTTP调用（优先）
        if self.use_direct_http and self.http_client:
            try:
                return await self._chat_completion_http(messages, **kwargs)
            except Exception as e:
                logger.warning(f"直接HTTP调用失败: {e}，降级到LangChain")
                self.use_direct_http = False
        
        # 策略2: LangChain调用（降级）
        if self.langchain_client:
            try:
                return await self._chat_completion_langchain(messages, **kwargs)
            except Exception as e:
                logger.error(f"LangChain调用失败: {e}")
                raise RuntimeError(f"所有LLM调用方式都失败: {e}")
        
        raise RuntimeError("没有可用的LLM客户端")
    
    async def _chat_completion_http(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """直接HTTP调用DeepSeek API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }
        
        # DeepSeek特殊参数（如果支持）
        if kwargs.get("reasoning", False):
            payload["reasoning"] = True
        
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # 提取内容
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return {
                "content": content,
                "raw_response": result,
                "usage": result.get("usage", {})
            }
        else:
            raise ValueError("API响应格式异常")
    
    async def _chat_completion_langchain(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """通过LangChain调用"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # 转换消息格式
        langchain_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        # 调用LLM
        response = await self.langchain_client.ainvoke(langchain_messages)
        
        return {
            "content": response.content,
            "raw_response": {"choices": [{"message": {"content": response.content}}]},
            "usage": {}
        }
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        流式聊天补全（阶段2：LLM分析流式化）
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数（temperature, max_tokens等）
        
        Yields:
            Dict: 流式响应块
        """
        if not self.api_key:
            raise RuntimeError("API密钥未设置")
        
        # 策略1: 直接HTTP流式调用（优先）
        if self.use_direct_http and self.http_client:
            try:
                async for chunk in self._chat_completion_stream_http(messages, **kwargs):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"直接HTTP流式调用失败: {e}，降级到模拟流式")
                self.use_direct_http = False
        
        # 策略2: 降级到批处理+模拟流式
        if self.langchain_client:
            try:
                # 先获取完整响应
                response = await self._chat_completion_langchain(messages, **kwargs)
                content = response.get("content", "")
                
                # 模拟流式输出（分块返回）
                chunk_size = 20  # 每20个字符一块
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    yield {
                        "content": chunk,
                        "role": "assistant",
                        "finish_reason": None if i + chunk_size < len(content) else "stop",
                        "usage": None
                    }
                    await asyncio.sleep(0.05)  # 模拟延迟
                
                # 发送完成标记
                yield {
                    "content": "",
                    "role": "assistant",
                    "finish_reason": "stop",
                    "usage": response.get("usage", {})
                }
                return
            except Exception as e:
                logger.error(f"LangChain流式调用失败: {e}")
                raise RuntimeError(f"所有LLM流式调用方式都失败: {e}")
        
        raise RuntimeError("没有可用的LLM客户端")
    
    async def _chat_completion_stream_http(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """直接HTTP流式调用DeepSeek API"""
        import json
        
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": True  # 启用流式
        }
        
        # DeepSeek特殊参数（如果支持）
        if kwargs.get("reasoning", False):
            payload["reasoning"] = True
        
        try:
            async with self.http_client.stream(
                "POST",
                url,
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
                                # 发送完成标记
                                usage = chunk_data.get("usage", {})
                                yield {
                                    "content": "",
                                    "role": "assistant",
                                    "finish_reason": finish_reason,
                                    "usage": usage
                                }
                                break
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析失败: {e}, 原始数据: {data_str[:100]}")
                            continue
        except Exception as e:
            logger.error(f"HTTP流式调用失败: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        if hasattr(self, "http_client") and self.http_client:
            await self.http_client.aclose()


