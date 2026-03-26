"""
LLM集成服务 - 从配置中心读取配置
用于智能任务分解
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
import re

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared_libs"))

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    from luminaos_common.clients.config_client import get_config_client
    CONFIG_CLIENT_AVAILABLE = True
except ImportError:
    CONFIG_CLIENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMIntegration:
    """LLM集成类 - 从配置中心读取配置，用于智能任务分解"""
    
    def __init__(self):
        self.config_client = None
        self.api_key = None
        self.base_url = None
        self.model = None
        self.llm = None
        
        # 初始化配置客户端
        if CONFIG_CLIENT_AVAILABLE:
            try:
                self.config_client = get_config_client()
            except Exception as e:
                logger.warning(f"Failed to initialize config client: {e}")
        
        # 从配置中心加载配置
        self._load_config()
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            self._init_llm()
    
    async def _load_config_async(self):
        """异步加载配置（从配置中心）"""
        if not self.config_client:
            return
        
        try:
            llm_config = await self.config_client.get_llm_config()
            
            if llm_config.get("api_key"):
                self.api_key = llm_config["api_key"]
            if llm_config.get("base_url"):
                self.base_url = llm_config["base_url"]
            if llm_config.get("model"):
                self.model = llm_config["model"]
            
            logger.info(f"LLM config loaded from config center: model={self.model}, base_url={self.base_url}")
            
            # 如果配置已加载且LLM未初始化，重新初始化
            if self.api_key and not self.llm and LANGCHAIN_AVAILABLE:
                self._init_llm()
        except Exception as e:
            logger.error(f"Failed to load config from config center: {e}")
            # 降级到环境变量
            self._load_config_from_env()
    
    def _load_config(self):
        """同步加载配置（优先从配置中心，降级到环境变量）"""
        if self.config_client:
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
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables or config center")
        if not self.base_url:
            logger.error("LLM_BASE_URL not found in environment variables or config center")
        if not self.model:
            logger.error("LLM_MODEL not found in environment variables or config center")
    
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            llm_kwargs = {
                "model": self.model,
                "temperature": 0.3,  # 较低温度以获得更稳定的分解结果
                "api_key": self.api_key,
            }
            
            if self.base_url:
                base_url_clean = self.base_url.rstrip("/v1").rstrip("/")
                llm_kwargs["base_url"] = base_url_clean
            
            self.llm = ChatOpenAI(**llm_kwargs)
            logger.info(f"LLM initialized: model={self.model}, base_url={self.base_url or 'default'}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.llm = None
    
    async def analyze(self, prompt: str) -> str:
        """
        调用LLM进行分析
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM响应文本
        """
        if not self.llm:
            raise RuntimeError("LLM not initialized. Please set OPENAI_API_KEY and LLM_BASE_URL.")
        
        try:
            messages = [
                SystemMessage(content="你是一个专业的任务分解专家，擅长将复杂任务分解为可执行的DAG计划。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            result = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"LLM analysis completed, response length: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            raise Exception(f"LLM analysis error: {str(e)}")
    
    def parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        从LLM响应中解析JSON
        
        Args:
            text: LLM响应文本
            
        Returns:
            解析后的JSON字典
        """
        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试提取纯JSON对象
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = text
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            logger.error(f"Response text: {text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")


