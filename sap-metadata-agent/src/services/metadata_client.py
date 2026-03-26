"""
元数据服务客户端
用于将SAP元数据注册到metadata-service
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)


class MetadataClient:
    """元数据服务客户端"""
    
    def __init__(self, metadata_service_url: Optional[str] = None):
        """
        初始化元数据服务客户端
        
        Args:
            metadata_service_url: 元数据服务URL
        """
        self.base_url = metadata_service_url or os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        # 明确禁用所有代理和Docker相关配置，确保不会触发任何Docker API调用
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            proxies={},  # 明确禁用所有代理（空字典表示禁用）
            verify=True,  # 验证SSL证书
            follow_redirects=True,  # 跟随重定向
            # 明确设置传输层，避免使用系统默认配置
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=5.0
            )
        )
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def create_data_asset(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建数据资产
        
        Args:
            asset_data: 数据资产数据
            
        Returns:
            创建的数据资产，失败返回None
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/data-assets",
                json=asset_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create data asset: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating data asset: {e}", exc_info=True)
            return None
    
    async def create_business_entity(self, entity_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建业务实体
        
        Args:
            entity_data: 业务实体数据
            
        Returns:
            创建的业务实体，失败返回None
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/business-entities",
                json=entity_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create business entity: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating business entity: {e}", exc_info=True)
            return None
    
    async def list_data_assets(
        self,
        limit: int = 100,
        offset: int = 0,
        classification: Optional[str] = None,
        source_system: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出数据资产
        
        Args:
            limit: 限制数量
            offset: 偏移量
            classification: 分类过滤
            source_system: 源系统过滤
            
        Returns:
            数据资产列表
        """
        try:
            params = {
                "limit": limit,
                "skip": offset,
                "include_total": "true"
            }
            if classification:
                params["classification"] = classification
            if source_system:
                params["source_system"] = source_system
            
            response = await self.http_client.get(
                f"{self.base_url}/api/data-assets",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            # API可能返回列表或包含items的对象
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "items" in result:
                return result["items"]
            elif isinstance(result, dict) and "data" in result:
                return result["data"]
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing data assets: {e}", exc_info=True)
            return []
    
    async def list_business_entities(
        self,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        列出业务实体
        
        Args:
            limit: 限制数量
            offset: 偏移量
            tags: 标签过滤
            
        Returns:
            业务实体列表
        """
        try:
            params = {
                "limit": limit,
                "skip": offset
            }
            if tags:
                params["tags"] = ",".join(tags)
            
            response = await self.http_client.get(
                f"{self.base_url}/api/business-entities",
                params=params
            )
            response.raise_for_status()
            result = response.json()
            # API可能返回列表或包含items的对象
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "items" in result:
                return result["items"]
            elif isinstance(result, dict) and "data" in result:
                return result["data"]
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing business entities: {e}", exc_info=True)
            return []
    
    async def batch_create_data_assets(
        self,
        assets: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        批量创建数据资产
        
        Args:
            assets: 数据资产列表
            batch_size: 批次大小
            
        Returns:
            批量创建结果统计
        """
        created = 0
        failed = 0
        errors = []
        
        for i in range(0, len(assets), batch_size):
            batch = assets[i:i + batch_size]
            for asset in batch:
                result = await self.create_data_asset(asset)
                if result:
                    created += 1
                else:
                    failed += 1
                    errors.append(f"Failed to create asset: {asset.get('name', 'unknown')}")
        
        return {
            "total": len(assets),
            "created": created,
            "failed": failed,
            "errors": errors[:10]  # 只返回前10个错误
        }
    
    async def batch_create_business_entities(
        self,
        entities: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        批量创建业务实体
        
        Args:
            entities: 业务实体列表
            batch_size: 批次大小
            
        Returns:
            批量创建结果统计
        """
        created = 0
        failed = 0
        errors = []
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            for entity in batch:
                result = await self.create_business_entity(entity)
                if result:
                    created += 1
                else:
                    failed += 1
                    errors.append(f"Failed to create entity: {entity.get('name', 'unknown')}")
        
        return {
            "total": len(entities),
            "created": created,
            "failed": failed,
            "errors": errors[:10]
        }


