"""
网关代理核心
实现反向代理、负载均衡、熔断、重试等功能
"""
import httpx
import logging
from typing import Optional, Dict, Any
from circuitbreaker import circuit
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from ..config import settings
from .service_discovery import service_discovery

logger = logging.getLogger(__name__)


class GatewayProxy:
    """网关代理"""

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.circuit_breakers: Dict[str, Any] = {}

    async def start(self):
        """启动代理"""
        # httpx 的 timeout 需要是 httpx.Timeout 对象或数字（秒）
        timeout_value = httpx.Timeout(settings.REQUEST_TIMEOUT, connect=10.0)
        self.http_client = httpx.AsyncClient(
            timeout=timeout_value,
            follow_redirects=True
        )
        logger.info("Gateway Proxy started")
    
    async def start_stream_proxy(self):
        """启动流式代理（如果还没有启动）"""
        # 流式代理使用独立的客户端，在需要时创建
        pass

    async def stop(self):
        """停止代理"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Gateway Proxy stopped")

    async def forward_request(
        self,
        request: Request,
        service_name: str,
        path: str,
        **kwargs
    ) -> Response:
        """
        转发请求到目标服务

        Args:
            request: FastAPI请求对象
            service_name: 目标服务名称
            path: 请求路径
            **kwargs: 额外参数

        Returns:
            FastAPI响应对象
        """
        # 服务发现
        endpoint = await service_discovery.get_service_endpoint(service_name)

        # 如果服务发现失败，尝试使用fallback
        if not endpoint:
            # 根据 LOCAL_DEV 配置选择使用 localhost 还是 Docker 服务名
            use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
            
            if use_localhost:
                # 本地开发模式：使用 localhost
                service_fallback = {
                    "config-center": "http://localhost:8090",
                    "workflow-engine": "http://localhost:8002",
                    "auth-service": "http://localhost:8003",
                    "mcp-gateway": "http://localhost:8001",
                    "knowledge-base": "http://localhost:8004",
                    "metadata-service": "http://localhost:8005",
                    "chat-service": "http://localhost:8006",
                    "joyagent-adapter": "http://localhost:8007",
                    "dag-orchestrator": "http://localhost:8009",
                    "agent-service": "http://localhost:8010",
                    "agent-orchestrator": "http://localhost:8011",
                    "agent-registry": "http://localhost:8012",
                    "project-management": "http://localhost:8016",
                    "ai-scenario-service": "http://localhost:8022",
                }
                mode = "local"
            else:
                # Docker 模式：使用 Docker 服务名
                service_fallback = {
                    "config-center": "http://config-center:8090",
                    "workflow-engine": "http://workflow-engine:8002",
                    "auth-service": "http://auth-service:8003",
                    "mcp-gateway": "http://mcp-gateway:8001",
                    "knowledge-base": "http://knowledge-base:8004",
                    "metadata-service": "http://metadata-service:8005",
                    "chat-service": "http://chat-service:8006",
                    "joyagent-adapter": "http://joyagent-adapter:8007",
                    "dag-orchestrator": "http://dag-orchestrator:8009",
                    "agent-service": "http://agent-service:8010",
                    "agent-orchestrator": "http://agent-orchestrator:8011",
                    "agent-registry": "http://agent-registry:8012",
                    "project-management": "http://project-management:8016",
                    "ai-scenario-service": "http://ai-scenario-service:8000",
                }
                mode = "docker"
            
            endpoint = service_fallback.get(service_name)
            if endpoint:
                logger.warning(f"Service {service_name} not found in registry, using fallback: {endpoint} (mode: {mode})")
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Service {service_name} is not available"
                )

        # 构建目标URL
        target_url = f"{endpoint}{path}"
        logger.info(f"Forwarding {request.method} request to {service_name}: {target_url}")

        # 准备请求参数
        headers = dict(request.headers)
        headers.pop("host", None)  # 移除原始host头

        # 检测是否为文件上传请求（multipart/form-data）
        content_type = request.headers.get("content-type", "")
        is_file_upload = "multipart/form-data" in content_type.lower()

        # 对于文件上传，使用流式传输；其他请求读取body
        if is_file_upload:
            # 流式传输：不读取整个body到内存
            logger.info(f"Using streaming upload for {request.method} {target_url}")

            # 使用流式请求体
            async def request_body_stream():
                """异步生成器：流式读取请求体"""
                async for chunk in request.stream():
                    yield chunk

            body_content = request_body_stream()
        else:
            # 非文件上传，正常读取body
            body = await request.body()
            body_content = body if body else None

        # 执行请求（带重试）
        for attempt in range(settings.MAX_RETRIES + 1):
            try:
                response = await self._make_request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body_content,
                    params=dict(request.query_params),
                    is_stream=is_file_upload
                )

                # 4xx 客户端错误是正常的业务响应，不需要重试，直接返回
                if response.status_code < 500:
                    # 复制响应头，确保 CORS 头被正确传递
                    response_headers = dict(response.headers)
                    # 确保 CORS 头存在（如果后端没有设置，API Gateway 会设置）
                    if "access-control-allow-origin" not in response_headers:
                        response_headers["Access-Control-Allow-Origin"] = "*"
                    if "access-control-allow-methods" not in response_headers:
                        response_headers["Access-Control-Allow-Methods"] = "*"
                    if "access-control-allow-headers" not in response_headers:
                        response_headers["Access-Control-Allow-Headers"] = "*"
                    
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=response_headers,
                    )
                
                # 5xx 服务器错误，可以重试
                if attempt < settings.MAX_RETRIES:
                    logger.warning(
                        f"Request to {service_name} failed (attempt {attempt + 1}/{settings.MAX_RETRIES + 1}): Status {response.status_code}"
                    )
                    # 等待后重试
                    import asyncio
                    await asyncio.sleep(settings.RETRY_DELAY * (attempt + 1))
                    continue
                
                # 最后一次重试失败，返回错误响应
                response_headers = dict(response.headers)
                # 确保 CORS 头存在
                if "access-control-allow-origin" not in response_headers:
                    response_headers["Access-Control-Allow-Origin"] = "*"
                if "access-control-allow-methods" not in response_headers:
                    response_headers["Access-Control-Allow-Methods"] = "*"
                if "access-control-allow-headers" not in response_headers:
                    response_headers["Access-Control-Allow-Headers"] = "*"
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                )

            except httpx.HTTPStatusError as e:
                # HTTP 状态错误
                # 4xx 客户端错误是正常的业务响应，不需要重试
                if e.response.status_code < 500:
                    response_headers = dict(e.response.headers)
                    # 确保 CORS 头存在
                    if "access-control-allow-origin" not in response_headers:
                        response_headers["Access-Control-Allow-Origin"] = "*"
                    if "access-control-allow-methods" not in response_headers:
                        response_headers["Access-Control-Allow-Methods"] = "*"
                    if "access-control-allow-headers" not in response_headers:
                        response_headers["Access-Control-Allow-Headers"] = "*"
                    
                    return Response(
                        content=e.response.content,
                        status_code=e.response.status_code,
                        headers=response_headers,
                    )
                
                # 5xx 服务器错误，可以重试
                if attempt < settings.MAX_RETRIES:
                    logger.warning(
                        f"Request to {service_name} failed (attempt {attempt + 1}/{settings.MAX_RETRIES + 1}): {e}"
                    )
                    # 等待后重试
                    import asyncio
                    await asyncio.sleep(settings.RETRY_DELAY * (attempt + 1))
                    continue
                
                # 最后一次重试失败，返回错误响应
                response_headers = dict(e.response.headers)
                # 确保 CORS 头存在
                if "access-control-allow-origin" not in response_headers:
                    response_headers["Access-Control-Allow-Origin"] = "*"
                if "access-control-allow-methods" not in response_headers:
                    response_headers["Access-Control-Allow-Methods"] = "*"
                if "access-control-allow-headers" not in response_headers:
                    response_headers["Access-Control-Allow-Headers"] = "*"
                
                return Response(
                    content=e.response.content,
                    status_code=e.response.status_code,
                    headers=response_headers,
                )
                
            except httpx.HTTPError as e:
                # 其他 HTTP 错误（网络错误等），可以重试
                logger.warning(
                    f"Request to {service_name} failed (attempt {attempt + 1}/{settings.MAX_RETRIES + 1}): {e}"
                )

                if attempt == settings.MAX_RETRIES:
                    # 确保错误响应也包含 CORS 头
                    error_response = JSONResponse(
                        status_code=502,
                        content={"detail": f"Failed to reach service {service_name}: {str(e)}"}
                    )
                    error_response.headers["Access-Control-Allow-Origin"] = "*"
                    error_response.headers["Access-Control-Allow-Methods"] = "*"
                    error_response.headers["Access-Control-Allow-Headers"] = "*"
                    return error_response

                # 等待后重试
                import asyncio
                await asyncio.sleep(settings.RETRY_DELAY * (attempt + 1))
            
            except Exception as e:
                # 处理 CircuitBreakerError 等其他异常
                logger.error(f"Unexpected error in forward_request: {e}", exc_info=True)
                if attempt == settings.MAX_RETRIES:
                    # 确保错误响应也包含 CORS 头
                    error_response = JSONResponse(
                        status_code=502,
                        content={"detail": f"Service {service_name} is temporarily unavailable: {str(e)}"}
                    )
                    error_response.headers["Access-Control-Allow-Origin"] = "*"
                    error_response.headers["Access-Control-Allow-Methods"] = "*"
                    error_response.headers["Access-Control-Allow-Headers"] = "*"
                    return error_response
                
                # 等待后重试
                import asyncio
                await asyncio.sleep(settings.RETRY_DELAY * (attempt + 1))

    async def _make_request(
        self,
        method: str,
        url: str,
        is_stream: bool = False,
        **kwargs
    ) -> httpx.Response:
        """
        执行HTTP请求（带熔断保护）

        Args:
            method: HTTP方法
            url: 请求URL
            is_stream: 是否为流式请求
            **kwargs: 请求参数

        Returns:
            httpx响应对象
        """
        try:
            # 对于流式上传，设置更长的超时时间
            if is_stream:
                # 文件上传需要更长的超时时间（10分钟）
                kwargs['timeout'] = httpx.Timeout(600.0, connect=30.0)
                logger.debug(f"Using extended timeout for streaming upload: 600s")

            response = await self.http_client.request(
                method=method,
                url=url,
                **kwargs
            )
            
            # 只有 5xx 服务器错误才应该触发熔断器
            # 4xx 客户端错误（如 401 Unauthorized）是正常的业务响应，不应该触发熔断
            if response.status_code >= 500:
                # 5xx 错误，可能触发熔断器
                response.raise_for_status()
            
            # 不调用 raise_for_status()，让调用者处理状态码
            # 这样 4xx 错误可以正常返回给客户端
            return response
            
        except httpx.HTTPStatusError as e:
            # 如果是 4xx 错误，直接返回响应，不触发熔断器
            if e.response.status_code < 500:
                return e.response
            # 5xx 错误，继续抛出异常，可能触发熔断器
            raise
        except httpx.HTTPError as e:
            # 网络错误等，应该触发熔断器
            raise


# 全局代理实例
gateway_proxy = GatewayProxy()
