"""
服务发现客户端
与Registry Service集成，实现动态服务发现
"""
import httpx
import logging
from typing import Optional, Dict, Any
from circuitbreaker import circuit
from ..config import settings

logger = logging.getLogger(__name__)


class ServiceDiscoveryClient:
    """服务发现客户端"""

    def __init__(self):
        self.registry_url = settings.REGISTRY_SERVICE_URL
        self.http_client: Optional[httpx.AsyncClient] = None
        self.service_cache: Dict[str, Any] = {}

    async def start(self):
        """启动服务发现客户端"""
        self.http_client = httpx.AsyncClient(timeout=10.0)
        logger.info(f"Service Discovery Client started, registry at {self.registry_url}")

    async def stop(self):
        """停止服务发现客户端"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Service Discovery Client stopped")

    @circuit(failure_threshold=5, recovery_timeout=60)
    async def discover_service(self, service_name: str, load_balancing: str = None) -> Optional[Dict[str, Any]]:
        """
        发现服务实例

        Args:
            service_name: 服务名称
            load_balancing: 负载均衡策略 (round_robin, random)

        Returns:
            服务实例信息
        """
        try:
            if not load_balancing:
                load_balancing = settings.LOAD_BALANCE_STRATEGY

            url = f"{self.registry_url}/api/discover/{service_name}"
            params = {"load_balancing": load_balancing}

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            service_info = response.json()
            logger.debug(f"Discovered service: {service_name} -> {service_info}")

            return service_info

        except httpx.HTTPError as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
            return None

    async def get_service_endpoint(self, service_name: str) -> Optional[str]:
        """
        获取服务端点URL

        Args:
            service_name: 服务名称

        Returns:
            服务端点URL (如: http://host:port)
        """
        service_info = await self.discover_service(service_name)

        if not service_info:
            return None

        host = service_info.get("host")
        port = service_info.get("port")
        service_type = service_info.get("service_type", "http")

        if service_type == "websocket":
            return f"ws://{host}:{port}"
        else:
            return f"http://{host}:{port}"

    async def get_all_service_instances(self, service_name: str) -> list:
        """
        获取服务的所有实例

        Args:
            service_name: 服务名称

        Returns:
            服务实例列表
        """
        try:
            url = f"{self.registry_url}/api/discover/{service_name}/all"
            response = await self.http_client.get(url)
            response.raise_for_status()

            instances = response.json()
            return instances

        except httpx.HTTPError as e:
            logger.error(f"Failed to get service instances for {service_name}: {e}")
            return []

    async def healthcheck(self) -> bool:
        """检查服务发现客户端健康状态"""
        try:
            url = f"{self.registry_url}/health"
            response = await self.http_client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Registry service healthcheck failed: {e}")
            return False


# 全局服务发现客户端实例
service_discovery = ServiceDiscoveryClient()
