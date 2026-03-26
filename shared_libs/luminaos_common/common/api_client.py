"""
跨服务API客户端
"""
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP API客户端"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        初始化API客户端
        
        Args:
            base_url: 基础URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = headers or {}
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """GET请求"""
        return await self._request('GET', endpoint, params=params, headers=headers)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """POST请求"""
        return await self._request('POST', endpoint, json=data, headers=headers)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """PUT请求"""
        return await self._request('PUT', endpoint, json=data, headers=headers)
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """DELETE请求"""
        return await self._request('DELETE', endpoint, headers=headers)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: 端点路径
            **kwargs: 其他请求参数
        
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {**self.default_headers, **kwargs.pop('headers', {})}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {url}: {str(e)}")
            raise


