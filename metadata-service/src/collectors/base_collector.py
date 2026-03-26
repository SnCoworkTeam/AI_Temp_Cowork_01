"""
基础采集器
提供所有采集器的通用功能
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from httpx import AsyncClient, Timeout

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """基础采集器抽象类"""
    
    def __init__(
        self,
        source_service_url: str,
        metadata_service_url: str = "http://localhost:8005",
        timeout: float = 30.0
    ):
        """
        初始化采集器
        
        Args:
            source_service_url: 源服务URL
            metadata_service_url: 元数据服务URL
            timeout: 请求超时时间（秒）
        """
        self.source_service_url = source_service_url
        self.metadata_service_url = metadata_service_url
        self.timeout = Timeout(timeout)
        self._source_client: Optional[AsyncClient] = None
        self._metadata_client: Optional[AsyncClient] = None
    
    async def _get_source_client(self) -> AsyncClient:
        """获取源服务HTTP客户端（懒加载）"""
        if self._source_client is None:
            self._source_client = AsyncClient(
                base_url=self.source_service_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._source_client
    
    async def _get_metadata_client(self) -> AsyncClient:
        """获取元数据服务HTTP客户端（懒加载）"""
        if self._metadata_client is None:
            self._metadata_client = AsyncClient(
                base_url=self.metadata_service_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._metadata_client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._source_client:
            await self._source_client.aclose()
            self._source_client = None
        if self._metadata_client:
            await self._metadata_client.aclose()
            self._metadata_client = None
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        采集元数据
        
        Returns:
            采集到的元数据列表
        """
        pass
    
    @abstractmethod
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步元数据到元数据服务
        
        Args:
            metadata_list: 元数据列表
            
        Returns:
            同步结果统计
        """
        pass
    
    async def collect_and_sync(self) -> Dict[str, Any]:
        """
        采集并同步元数据
        
        Returns:
            同步结果统计
        """
        try:
            logger.info(f"Starting collection for {self.__class__.__name__}")
            metadata_list = await self.collect()
            logger.info(f"Collected {len(metadata_list)} items from {self.__class__.__name__}")
            
            if not metadata_list:
                return {
                    "success": True,
                    "collected": 0,
                    "synced": 0,
                    "errors": 0,
                    "message": "No metadata to sync"
                }
            
            result = await self.sync(metadata_list)
            logger.info(f"Sync completed for {self.__class__.__name__}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in collect_and_sync for {self.__class__.__name__}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "collected": 0,
                "synced": 0,
                "errors": 1,
                "message": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            source_client = await self._get_source_client()
            response = await source_client.get("/api/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.__class__.__name__}: {str(e)}")
            return False

