"""
服务注册服务
使用Redis存储服务注册信息
"""
import json
import uuid
import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..models.service_models import (
    ServiceRegistration,
    ServiceInfo,
    ServiceStatus,
    ServiceType
)


class RegistryService:
    """服务注册服务"""

    def __init__(self, redis_client: redis.Redis, heartbeat_ttl: int = 30):
        self.redis_client = redis_client
        self.service_key_prefix = "service:"
        self.service_list_key = "services:all"
        self.heartbeat_ttl = heartbeat_ttl  # 心跳TTL 30秒

    async def register_service(self, registration: ServiceRegistration) -> str:
        """注册服务"""
        service_id = str(uuid.uuid4())

        service_info = {
            "service_id": service_id,
            "name": registration.name,
            "host": registration.host,
            "port": registration.port,
            "service_type": registration.service_type.value,
            "status": ServiceStatus.HEALTHY.value,
            "metadata": json.dumps(registration.metadata),
            "health_check_url": registration.health_check_url or "",
            "tags": json.dumps(registration.tags),
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat()
        }

        # 存储服务信息
        service_key = f"{self.service_key_prefix}{service_id}"
        await self.redis_client.hset(service_key, mapping=service_info)
        await self.redis_client.expire(service_key, self.heartbeat_ttl)

        # 添加到服务列表
        await self.redis_client.sadd(self.service_list_key, service_id)

        # 添加到服务名索引
        service_name_key = f"service:name:{registration.name}"
        await self.redis_client.sadd(service_name_key, service_id)

        return service_id

    async def unregister_service(self, service_id: str):
        """注销服务"""
        service_key = f"{self.service_key_prefix}{service_id}"

        # 获取服务名
        service_info = await self.redis_client.hgetall(service_key)
        if service_info:
            service_name = service_info.get("name")
            if service_name:
                service_name_key = f"service:name:{service_name}"
                await self.redis_client.srem(service_name_key, service_id)

        # 删除服务信息
        await self.redis_client.delete(service_key)

        # 从服务列表移除
        await self.redis_client.srem(self.service_list_key, service_id)

    async def update_heartbeat(self, service_id: str, status: Optional[ServiceStatus] = None):
        """更新服务心跳"""
        service_key = f"{self.service_key_prefix}{service_id}"

        # 检查服务是否存在
        exists = await self.redis_client.exists(service_key)
        if not exists:
            raise ValueError(f"Service {service_id} not found")

        # 更新心跳时间
        updates = {
            "last_heartbeat": datetime.now().isoformat()
        }

        if status:
            updates["status"] = status.value

        await self.redis_client.hset(service_key, mapping=updates)

        # 刷新TTL
        await self.redis_client.expire(service_key, self.heartbeat_ttl)

    async def get_all_services(self) -> List[ServiceInfo]:
        """获取所有服务"""
        service_ids = await self.redis_client.smembers(self.service_list_key)
        services = []

        for service_id in service_ids:
            service_key = f"{self.service_key_prefix}{service_id}"
            service_data = await self.redis_client.hgetall(service_key)

            if service_data:
                service_info = self._parse_service_info(service_data)
                services.append(service_info)

        return services

    async def get_services_by_name(self, service_name: str) -> List[ServiceInfo]:
        """根据服务名获取服务实例"""
        service_name_key = f"service:name:{service_name}"
        service_ids = await self.redis_client.smembers(service_name_key)
        services = []

        for service_id in service_ids:
            service_key = f"{self.service_key_prefix}{service_id}"
            service_data = await self.redis_client.hgetall(service_key)

            if service_data:
                service_info = self._parse_service_info(service_data)
                services.append(service_info)

        return services

    async def discover_service(self, service_name: str, load_balancing: str = "round_robin") -> Optional[ServiceInfo]:
        """服务发现 - 返回一个可用的服务实例"""
        services = await self.get_services_by_name(service_name)

        # 过滤健康的服务
        healthy_services = [s for s in services if s.status == ServiceStatus.HEALTHY]

        if not healthy_services:
            return None

        # 负载均衡策略
        if load_balancing == "random":
            return random.choice(healthy_services)
        elif load_balancing == "round_robin":
            # 简单的轮询 (使用时间戳作为索引)
            index = int(datetime.now().timestamp()) % len(healthy_services)
            return healthy_services[index]
        else:
            return healthy_services[0]

    async def discover_all_services(self, service_name: str, include_unhealthy: bool = False) -> List[ServiceInfo]:
        """获取服务的所有实例"""
        services = await self.get_services_by_name(service_name)

        if not include_unhealthy:
            services = [s for s in services if s.status == ServiceStatus.HEALTHY]

        return services

    async def get_service_endpoints(self, service_name: str) -> List[str]:
        """获取服务的所有端点URL"""
        services = await self.get_services_by_name(service_name)
        healthy_services = [s for s in services if s.status == ServiceStatus.HEALTHY]

        endpoints = []
        for service in healthy_services:
            if service.service_type == ServiceType.HTTP:
                endpoint = f"http://{service.host}:{service.port}"
            elif service.service_type == ServiceType.WEBSOCKET:
                endpoint = f"ws://{service.host}:{service.port}"
            else:
                endpoint = f"{service.host}:{service.port}"

            endpoints.append(endpoint)

        return endpoints

    async def get_service_health(self, service_id: str) -> Dict[str, Any]:
        """获取服务健康状态"""
        service_key = f"{self.service_key_prefix}{service_id}"
        service_data = await self.redis_client.hgetall(service_key)

        if not service_data:
            raise ValueError(f"Service {service_id} not found")

        service_info = self._parse_service_info(service_data)
        last_heartbeat = datetime.fromisoformat(service_data["last_heartbeat"])
        time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()

        return {
            "service_id": service_id,
            "status": service_info.status.value,
            "last_heartbeat": last_heartbeat.isoformat(),
            "time_since_heartbeat_seconds": time_since_heartbeat,
            "is_healthy": time_since_heartbeat < self.heartbeat_ttl
        }

    async def get_discovery_stats(self) -> Dict[str, Any]:
        """获取服务发现统计信息"""
        all_services = await self.get_all_services()

        stats = {
            "total_services": len(all_services),
            "healthy_services": sum(1 for s in all_services if s.status == ServiceStatus.HEALTHY),
            "unhealthy_services": sum(1 for s in all_services if s.status != ServiceStatus.HEALTHY),
            "services_by_type": {},
            "services_by_name": {}
        }

        for service in all_services:
            # 按类型统计
            service_type = service.service_type.value
            stats["services_by_type"][service_type] = stats["services_by_type"].get(service_type, 0) + 1

            # 按名称统计
            stats["services_by_name"][service.name] = stats["services_by_name"].get(service.name, 0) + 1

        return stats

    async def get_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        all_services = await self.get_all_services()

        return {
            "registry_service": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "total_registered_services": len(all_services),
                "redis_connected": bool(self.redis_client)
            },
            "services": [
                {
                    "service_id": s.service_id,
                    "name": s.name,
                    "status": s.status.value,
                    "uptime_seconds": s.uptime_seconds
                }
                for s in all_services
            ]
        }

    def _parse_service_info(self, service_data: Dict[str, str]) -> ServiceInfo:
        """解析服务信息"""
        registered_at = datetime.fromisoformat(service_data["registered_at"])
        last_heartbeat = datetime.fromisoformat(service_data["last_heartbeat"])
        uptime = (datetime.now() - registered_at).total_seconds()

        return ServiceInfo(
            service_id=service_data["service_id"],
            name=service_data["name"],
            host=service_data["host"],
            port=int(service_data["port"]),
            service_type=ServiceType(service_data["service_type"]),
            status=ServiceStatus(service_data["status"]),
            metadata=json.loads(service_data["metadata"]),
            health_check_url=service_data.get("health_check_url") or None,
            tags=json.loads(service_data["tags"]),
            registered_at=registered_at,
            last_heartbeat=last_heartbeat,
            uptime_seconds=uptime
        )
