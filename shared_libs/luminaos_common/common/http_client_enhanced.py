"""
增强的HTTP客户端

提供重试、超时、熔断器等功能的统一HTTP客户端
"""
import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """
    熔断器实现

    当失败率超过阈值时，熔断器会打开，停止请求一段时间
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        """执行函数调用，经过熔断器"""
        if self.state == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("熔断器进入半开状态")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """成功回调"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info("熔断器关闭")

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"熔断器打开，将在 {self.timeout}秒后尝试恢复")


class EnhancedHTTPClient:
    """
    增强的HTTP客户端

    Features:
    - 自动重试（指数退避）
    - 请求超时
    - 熔断器
    - 请求追踪
    - 统一错误处理
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        enable_circuit_breaker: bool = True
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建httpx客户端
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True
        )

        # 熔断器
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """带重试的请求"""
        logger.debug(f"{method} {url}")

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code}: {url}")
            raise
        except httpx.TimeoutException:
            logger.error(f"Request timeout: {url}")
            raise
        except httpx.NetworkError as e:
            logger.error(f"Network error: {url} - {str(e)}")
            raise

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> httpx.Response:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            request_id: 请求追踪ID
            **kwargs: 其他httpx参数

        Returns:
            httpx.Response
        """
        # 添加请求追踪ID
        if request_id:
            headers = headers or {}
            headers["X-Request-ID"] = request_id

        # 如果启用了熔断器
        if self.circuit_breaker:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self.circuit_breaker.call,
                self._request_with_retry,
                method,
                url,
                headers=headers,
                **kwargs
            )
        else:
            return await self._request_with_retry(
                method, url, headers=headers, **kwargs
            )

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET请求"""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST请求"""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT请求"""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """PATCH请求"""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE请求"""
        return await self.request("DELETE", url, **kwargs)

    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET请求并返回JSON"""
        response = await self.get(url, **kwargs)
        return response.json()

    async def post_json(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """POST JSON数据并返回JSON"""
        response = await self.post(url, json=json, **kwargs)
        return response.json()


class ServiceClient:
    """
    服务客户端基类

    封装对特定服务的调用
    """

    def __init__(
        self,
        service_name: str,
        base_url: str,
        timeout: int = 30
    ):
        self.service_name = service_name
        self.base_url = base_url
        self.client = EnhancedHTTPClient(
            base_url=base_url,
            timeout=timeout
        )

    async def health_check(self) -> bool:
        """检查服务健康状态"""
        try:
            response = await self.client.get("/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"{self.service_name} health check failed: {str(e)}")
            return False

    async def close(self):
        """关闭客户端"""
        await self.client.close()


# 使用示例
"""
# 基本使用
async with EnhancedHTTPClient() as client:
    response = await client.get_json("https://api.example.com/data")

# 服务客户端
class WorkflowServiceClient(ServiceClient):
    def __init__(self, base_url: str):
        super().__init__("workflow-engine", base_url)

    async def execute_workflow(self, workflow_id: str, data: dict):
        return await self.client.post_json(
            f"/api/workflows/{workflow_id}/execute",
            json=data
        )

client = WorkflowServiceClient("http://localhost:8002")
result = await client.execute_workflow("wf-123", {"input": "data"})
await client.close()
"""
