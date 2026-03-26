"""
健康检查服务
定期检查已注册服务的健康状态
"""
import asyncio
import httpx
from typing import Optional
from datetime import datetime
from ..models.service_models import ServiceStatus, ServiceInfo
from .registry_service import RegistryService
import logging

logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查服务"""

    def __init__(self, registry_service: RegistryService):
        self.registry_service = registry_service
        self.http_client: Optional[httpx.AsyncClient] = None

    async def start_health_check_loop(self, interval: int = 10):
        """启动健康检查循环"""
        self.http_client = httpx.AsyncClient(timeout=5.0)

        try:
            while True:
                await self.check_all_services()
                await asyncio.sleep(interval)
        finally:
            if self.http_client:
                await self.http_client.aclose()

    async def check_all_services(self):
        """检查所有服务"""
        try:
            services = await self.registry_service.get_all_services()

            for service in services:
                await self.check_service(service)

        except Exception as e:
            logger.error(f"Health check error: {e}")

    async def check_service(self, service: ServiceInfo):
        """检查单个服务"""
        try:
            if not service.health_check_url:
                # 如果没有健康检查URL,使用默认端点
                health_url = f"http://{service.host}:{service.port}/api/health"
            else:
                health_url = service.health_check_url

            start_time = datetime.now()
            # 允许跟随重定向（处理 307 等情况）
            response = await self.http_client.get(health_url, follow_redirects=True)
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # 接受 200 和 307（重定向后应该也是 200）
            if response.status_code in [200, 307]:
                # 服务健康
                await self.registry_service.update_heartbeat(
                    service.service_id,
                    ServiceStatus.HEALTHY
                )
                logger.debug(f"Service {service.name} ({service.service_id}) is healthy. Response time: {response_time:.2f}ms")
            else:
                # 服务不健康
                await self.registry_service.update_heartbeat(
                    service.service_id,
                    ServiceStatus.UNHEALTHY
                )
                logger.warning(f"Service {service.name} ({service.service_id}) is unhealthy. Status code: {response.status_code}")

        except httpx.RequestError as e:
            # 网络错误
            try:
                await self.registry_service.update_heartbeat(
                    service.service_id,
                    ServiceStatus.UNHEALTHY
                )
            except Exception:
                pass

            logger.warning(f"Service {service.name} ({service.service_id}) health check failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error checking service {service.service_id}: {e}")
