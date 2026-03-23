"""
监控中间件
实现Prometheus指标收集
"""
import time
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

# 定义Prometheus指标
REQUEST_COUNT = Counter(
    'api_gateway_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'api_gateway_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'api_gateway_requests_in_progress',
    'Number of requests in progress'
)

ERROR_COUNT = Counter(
    'api_gateway_errors_total',
    'Total error count',
    ['method', 'endpoint', 'error_type']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""

    async def dispatch(self, request: Request, call_next):
        """处理请求并收集指标"""

        # 增加进行中的请求数
        REQUEST_IN_PROGRESS.inc()

        # 记录开始时间
        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 记录请求计数
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()

            # 记录请求时长
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            return response

        except Exception as e:
            # 记录错误
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__
            ).inc()
            raise

        finally:
            # 减少进行中的请求数
            REQUEST_IN_PROGRESS.dec()
