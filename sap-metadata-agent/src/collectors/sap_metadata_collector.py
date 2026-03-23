"""
SAP元数据采集器
集成到metadata-service的采集器框架
"""
import logging
from typing import List, Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from metadata_service.src.collectors.base_collector import BaseCollector
except ImportError:
    # 如果无法导入，创建一个简化版本
    from abc import ABC, abstractmethod
    class BaseCollector(ABC):
        def __init__(self, source_service_url: str, metadata_service_url: str = "http://localhost:8005", timeout: float = 30.0):
            self.source_service_url = source_service_url
            self.metadata_service_url = metadata_service_url
            self.timeout = timeout
        
        @abstractmethod
        async def collect(self) -> List[Dict[str, Any]]:
            pass
        
        @abstractmethod
        async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
            pass

logger = logging.getLogger(__name__)


class SAPMetadataCollector(BaseCollector):
    """SAP元数据采集器"""
    
    def __init__(
        self,
        sap_metadata_agent_url: str = "http://sap-metadata-agent:8015",
        metadata_service_url: str = "http://metadata-service:8005",
        **kwargs
    ):
        """
        初始化SAP元数据采集器
        
        Args:
            sap_metadata_agent_url: SAP元数据智能体服务URL
            metadata_service_url: 元数据服务URL
            **kwargs: 其他参数
        """
        super().__init__(
            source_service_url=sap_metadata_agent_url,
            metadata_service_url=metadata_service_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从SAP元数据智能体采集元数据
        
        Returns:
            元数据列表
        """
        try:
            import httpx
            client = await self._get_source_client()
            
            # 调用发现API
            response = await client.post(
                "/api/sap-metadata/discover",
                json={
                    "include_database": True,
                    "include_odata": True,
                    "build_semantic_index": False,  # 采集时不构建索引
                    "sync_to_metadata_service": False  # 由采集器负责同步
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # 转换为元数据列表
            metadata_list = []
            
            # 数据资产
            for asset in result.get("data_assets", []):
                metadata_list.append({
                    "type": "data_asset",
                    "data": asset
                })
            
            # 业务实体
            for entity in result.get("business_entities", []):
                metadata_list.append({
                    "type": "business_entity",
                    "data": entity
                })
            
            logger.info(f"Collected {len(metadata_list)} SAP metadata items")
            return metadata_list
            
        except Exception as e:
            logger.error(f"Error collecting SAP metadata: {e}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步元数据到元数据服务
        
        Args:
            metadata_list: 元数据列表
            
        Returns:
            同步结果统计
        """
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                metadata_type = metadata.get("type")
                data = metadata.get("data")
                
                if metadata_type == "data_asset":
                    # 转换为数据资产格式
                    asset_data = {
                        "name": data.get("name"),
                        "display_name": data.get("display_name"),
                        "description": data.get("description"),
                        "asset_type": self._map_asset_type(data.get("asset_type")),
                        "source_system": "SAP",
                        "source_path": data.get("sap_table_name") or data.get("odata_entity"),
                        "schema_info": data.get("schema_info"),
                        "tags": data.get("tags", []),
                        "classification": data.get("classification"),
                        "metadata": data.get("metadata", {})
                    }
                    
                    response = await client.post("/api/data-assets", json=asset_data)
                    if response.status_code in [200, 201]:
                        synced += 1
                    else:
                        errors += 1
                        logger.warning(f"Failed to sync data asset {data.get('name')}: {response.status_code}")
                
                elif metadata_type == "business_entity":
                    # 转换为业务实体格式
                    entity_data = {
                        "name": data.get("name"),
                        "display_name": data.get("display_name"),
                        "description": data.get("description"),
                        "entity_type": "concept",
                        "business_definition": f"SAP业务实体: {data.get('display_name')}",
                        "tags": ["SAP", "business_entity"] + data.get("tags", []),
                        "metadata": data.get("metadata", {})
                    }
                    
                    response = await client.post("/api/business-entities", json=entity_data)
                    if response.status_code in [200, 201]:
                        synced += 1
                    else:
                        errors += 1
                        logger.warning(f"Failed to sync business entity {data.get('name')}: {response.status_code}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error syncing metadata: {e}", exc_info=True)
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "errors": errors,
            "message": f"Synced {synced}/{len(metadata_list)} SAP metadata items"
        }
    
    def _map_asset_type(self, sap_asset_type: str) -> str:
        """映射SAP资产类型到数据资产类型"""
        mapping = {
            "business_object": "api",
            "master_data": "table",
            "transaction_data": "table",
            "configuration": "table",
            "table": "table",
            "view": "view",
            "report": "api",
            "workflow": "workflow",
            "interface": "api"
        }
        return mapping.get(sap_asset_type, "table")


