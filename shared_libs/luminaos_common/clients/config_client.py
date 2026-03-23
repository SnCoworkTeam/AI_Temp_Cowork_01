"""
配置中心客户端
统一从配置中心读取配置，避免硬编码
"""
import httpx
import logging
import os
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigClient:
    """配置中心客户端"""
    
    def __init__(self, config_center_url: Optional[str] = None):
        # 优先使用传入的URL，然后环境变量，最后根据环境判断默认值
        if config_center_url:
            self.config_center_url = config_center_url
        else:
            env_url = os.getenv("CONFIG_CENTER_URL")
            if env_url:
                self.config_center_url = env_url
            else:
                # 默认值：本地开发环境使用localhost，Docker环境使用服务名
                # 尝试检测是否在Docker环境中（通过检查常见的环境变量）
                if os.getenv("DOCKER_CONTAINER") or os.path.exists("/.dockerenv"):
                    self.config_center_url = "http://config-center:8090"
                else:
                    self.config_center_url = "http://localhost:8090"
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 60  # 缓存60秒
    
    async def get_config(
        self, 
        key: str, 
        environment: str = "default",
        use_cache: bool = True
    ) -> Optional[Any]:
        """
        获取配置
        
        Args:
            key: 配置键
            environment: 环境（default, dev, test, prod）
            use_cache: 是否使用缓存
            
        Returns:
            配置值，如果不存在返回None
        """
        cache_key = f"{environment}:{key}"
        
        # 检查缓存
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            response = await self.http_client.get(
                f"{self.config_center_url}/api/config/{key}",
                params={"environment": environment}
            )
            
            if response.status_code == 200:
                config_data = response.json()
                value = config_data.get("value")
                
                # 缓存配置
                if use_cache:
                    self._cache[cache_key] = value
                
                return value
            elif response.status_code == 404:
                logger.warning(f"Config not found: {key} in environment {environment}")
                return None
            else:
                logger.error(f"Failed to get config {key}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting config {key} from config center: {e}")
            return None
    
    async def get_all_configs(self, environment: str = "default") -> Dict[str, Any]:
        """
        获取所有配置（扁平化）
        
        Args:
            environment: 环境
            
        Returns:
            配置字典
        """
        try:
            response = await self.http_client.get(
                f"{self.config_center_url}/api/configs/all",
                params={"environment": environment}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get all configs: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting all configs from config center: {e}")
            return {}
    
    async def get_llm_config(self, environment: str = "default") -> Dict[str, Any]:
        """
        获取LLM配置
        
        Returns:
            {
                "api_key": str,
                "base_url": str,
                "model": str,
                "temperature": float,
                "max_tokens": int
            }
        """
        configs = await self.get_all_configs(environment)
        
        # 从配置中心读取，如果没有则返回None（不允许硬编码默认值）
        llm_config = {
            "api_key": configs.get("llm.api_key"),
            "base_url": configs.get("llm.base_url"),
            "model": configs.get("llm.model") or configs.get("llm.default_model"),
            "temperature": configs.get("llm.temperature", 0.7),
            "max_tokens": configs.get("llm.max_tokens", 4096),
        }
        
        return llm_config
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
    
    async def close(self):
        """关闭客户端"""
        await self.http_client.aclose()


# 全局配置客户端实例
_config_client: Optional[ConfigClient] = None


def get_config_client() -> ConfigClient:
    """获取配置客户端实例（单例）"""
    global _config_client
    if _config_client is None:
        _config_client = ConfigClient()
    return _config_client




