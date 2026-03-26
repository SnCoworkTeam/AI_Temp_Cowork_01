"""
类型安全的HTTP客户端
提供类型化的HTTP请求方法
"""
import httpx
from typing import Dict, Any, Optional, TypeVar, Type, Union
import logging
from datetime import datetime
import asyncio

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class HTTPClientError(Exception):
    """HTTP客户端错误"""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class HTTPClient:
    """类型安全的HTTP客户端"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
        retry_delay: float = 1.0
    ):
        """
        初始化HTTP客户端
        
        Args:
            base_url: 基础URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(headers or {})
        }
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.default_headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], T]:
        """
        执行HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: 端点路径
            response_model: 响应模型类型（Pydantic）
            **kwargs: 其他请求参数
        
        Returns:
            响应数据（如果指定了response_model，则返回验证后的模型实例）
        
        Raises:
            HTTPClientError: 如果请求失败
        """
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {**self.default_headers, **kwargs.pop('headers', {})}
        
        last_error = None
        
        for attempt in range(self.retry_count + 1):
            try:
                if not self._client:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.request(
                            method,
                            url,
                            headers=headers,
                            **kwargs
                        )
                else:
                    response = await self._client.request(
                        method,
                        endpoint,
                        headers=headers,
                        **kwargs
                    )
                
                # 检查状态码
                if not response.is_success:
                    error_data = None
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"text": response.text}
                    
                    raise HTTPClientError(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        status_code=response.status_code,
                        response_data=error_data
                    )
                
                # 解析响应
                try:
                    data = response.json()
                except Exception:
                    data = {"text": response.text}
                
                # 验证响应模型（如果提供）
                if response_model:
                    try:
                        return response_model(**data)
                    except ValidationError as e:
                        logger.warning(
                            f"Response validation failed: {e}. "
                            f"Returning raw data instead."
                        )
                        return data
                
                return data
            
            except httpx.HTTPStatusError as e:
                last_error = HTTPClientError(
                    f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                    status_code=e.response.status_code,
                    response_data={"text": e.response.text}
                )
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise last_error
            
            except httpx.RequestError as e:
                last_error = HTTPClientError(
                    f"Request error: {str(e)}",
                    response_data={"error": str(e)}
                )
                if attempt < self.retry_count:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise last_error
        
        raise last_error or HTTPClientError("Unknown error")
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """GET请求"""
        return await self._request(
            'GET',
            endpoint,
            response_model=response_model,
            params=params,
            headers=headers
        )
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """POST请求"""
        json_data = data.model_dump() if isinstance(data, BaseModel) else data
        return await self._request(
            'POST',
            endpoint,
            response_model=response_model,
            json=json_data,
            headers=headers
        )
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """PUT请求"""
        json_data = data.model_dump() if isinstance(data, BaseModel) else data
        return await self._request(
            'PUT',
            endpoint,
            response_model=response_model,
            json=json_data,
            headers=headers
        )
    
    async def patch(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], BaseModel]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """PATCH请求"""
        json_data = data.model_dump() if isinstance(data, BaseModel) else data
        return await self._request(
            'PATCH',
            endpoint,
            response_model=response_model,
            json=json_data,
            headers=headers
        )
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """DELETE请求"""
        return await self._request(
            'DELETE',
            endpoint,
            response_model=response_model,
            headers=headers
        )


class TypedHTTPClient(HTTPClient):
    """类型化的HTTP客户端"""
    
    async def get_typed(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """GET请求（返回类型化响应）"""
        return await self.get(
            endpoint,
            params=params,
            headers=headers,
            response_model=response_model
        )

