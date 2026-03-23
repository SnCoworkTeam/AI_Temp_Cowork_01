"""
流式代理
支持将流式请求代理到后端服务
"""
import logging
import httpx
from typing import AsyncGenerator, Optional
from fastapi import Request
from fastapi.responses import StreamingResponse

from .service_discovery import service_discovery

logger = logging.getLogger(__name__)


class StreamProxy:
    """流式代理"""
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端（延迟初始化）"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=300.0)  # 流式请求可能需要更长时间
        return self.http_client
    
    async def proxy_stream(
        self,
        request: Request,
        service_name: str,
        path: str
    ) -> StreamingResponse:
        """
        代理流式请求到后端服务
        
        Args:
            request: FastAPI请求对象
            service_name: 目标服务名称
            path: 请求路径
            
        Returns:
            StreamingResponse对象
        """
        try:
            # 服务发现
            endpoint = await service_discovery.get_service_endpoint(service_name)
            
            if not endpoint:
                # Fallback到Docker服务名
                service_fallback = {
                    "agent-service": "http://agent-service:8010",
                    "chat-service": "http://chat-service:8006",
                    "workflow-engine": "http://workflow-engine:8002",
                    "dag-orchestrator": "http://dag-orchestrator:8009",
                }
                endpoint = service_fallback.get(service_name)
                if endpoint:
                    logger.warning(f"Service {service_name} not found in registry, using fallback: {endpoint}")
                else:
                    raise Exception(f"Service {service_name} is not available")
            
            # 构建目标URL
            target_url = f"{endpoint}{path}"
            logger.info(f"Proxying stream request to {service_name}: {target_url}")
            
            # 准备请求参数
            headers = dict(request.headers)
            headers.pop("host", None)
            headers.pop("connection", None)  # 移除connection头，让httpx管理
            
            # 获取请求体（确保是有效的JSON）
            body_bytes = await request.body()
            
            # 创建流式请求
            async def generate_stream():
                try:
                    client = await self._get_client()
                    # 使用 content 参数传递原始字节，让 httpx 自动处理 Content-Type
                    async with client.stream(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=body_bytes if body_bytes else None,
                        params=dict(request.query_params),
                        timeout=300.0,  # 增加超时时间到300秒
                    ) as response:
                        # 检查响应状态码
                        if response.status_code != 200:
                            # 读取错误响应
                            error_text = await response.aread()
                            import json
                            error_msg = json.dumps({
                                "type": "error",
                                "error": f"HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')}"
                            })
                            yield f"data: {error_msg}\n\n"
                            return
                        
                        # 流式传输响应数据
                        try:
                            async for chunk in response.aiter_bytes():
                                yield chunk
                        except Exception as chunk_error:
                            # 如果流式传输过程中出错，记录但不中断整个响应
                            logger.warning(f"Stream chunk error (may be normal completion): {chunk_error}")
                            # 不yield错误，让前端根据已接收的数据判断是否正常完成
                            
                except Exception as e:
                    logger.error(f"Stream proxy error: {e}", exc_info=True)
                    # 转义JSON中的特殊字符
                    import json
                    error_msg = json.dumps({
                        "type": "error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    yield f"data: {error_msg}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
            
        except Exception as e:
            logger.error(f"Stream proxy failed: {e}", exc_info=True)
            async def error_stream():
                error_msg = f'{{"type": "error", "error": "{str(e)}"}}'
                yield f"data: {error_msg}\n\n"
            
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                status_code=500,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )


# 全局流式代理实例
stream_proxy = StreamProxy()

