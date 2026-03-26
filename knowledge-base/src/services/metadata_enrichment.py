"""
元数据增强服务
用于与metadata-service通信，管理文档元数据
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from httpx import AsyncClient, Timeout

from ..config import settings
from ..models.document_metadata import (
    DocumentMetadata,
    DocumentMetadataCreate,
    DocumentMetadataUpdate
)

logger = logging.getLogger(__name__)


class MetadataEnrichment:
    """元数据增强服务"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """
        初始化元数据增强服务
        
        Args:
            base_url: 元数据服务基础URL，如果为None则从配置读取
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or getattr(settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005')
        self.timeout = Timeout(timeout)
        self._client: Optional[AsyncClient] = None
    
    async def _get_client(self) -> AsyncClient:
        """获取HTTP客户端（懒加载）"""
        if self._client is None:
            self._client = AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def create_document_metadata(
        self,
        document_metadata: DocumentMetadataCreate
    ) -> Optional[Dict[str, Any]]:
        """
        创建文档元数据
        
        Args:
            document_metadata: 文档元数据
            
        Returns:
            创建结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            
            # 将文档元数据转换为数据资产格式（因为metadata-service使用data_assets表）
            payload = {
                "name": document_metadata.document_id,
                "display_name": document_metadata.title,
                "description": f"Document: {document_metadata.title}",
                "asset_type": "file",
                "source_system": document_metadata.source,
                "source_path": document_metadata.file_path or "",
                "schema_info": {
                    "document_type": document_metadata.document_type,
                    "language": document_metadata.language,
                    "filename": document_metadata.filename,
                    "file_size": document_metadata.file_size
                },
                "sample_data": {
                    "topics": document_metadata.topics or [],
                    "entities": document_metadata.entities or []
                },
                "data_quality_metrics": {
                    "quality_score": document_metadata.quality_score or 0.0,
                    "vector_embedding_status": document_metadata.vector_embedding_status or "pending",
                    "search_popularity": document_metadata.search_popularity or 0
                },
                "business_owner": document_metadata.author,
                "technical_owner": document_metadata.author,
                "tags": document_metadata.tags or [],
                "classification": document_metadata.access_level or "public",
                "record_count": document_metadata.search_popularity or 0,
                "size_bytes": document_metadata.file_size or 0,
                "last_updated": document_metadata.modified_date.isoformat() if document_metadata.modified_date else None,
                "update_frequency": "on_demand",
                "metadata": {
                    "created_date": document_metadata.created_date.isoformat() if document_metadata.created_date else None,
                    "modified_date": document_metadata.modified_date.isoformat() if document_metadata.modified_date else None,
                    "vector_embedding_status": document_metadata.vector_embedding_status,
                    **{k: v for k, v in (document_metadata.metadata or {}).items()}
                }
            }
            
            response = await client.post("/api/data-assets", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Document metadata created for {document_metadata.document_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create document metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating document metadata: {str(e)}", exc_info=True)
            return None
    
    async def update_document_metadata(
        self,
        document_id: str,
        document_metadata: DocumentMetadataUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        更新文档元数据
        
        Args:
            document_id: 文档ID
            document_metadata: 文档元数据更新
            
        Returns:
            更新结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            
            # 首先获取数据资产ID（通过名称查找）
            # 注意：这里假设document_id作为name存储
            list_response = await client.get(
                f"/api/data-assets",
                params={"search": document_id, "asset_type": "file"}
            )
            list_response.raise_for_status()
            assets = list_response.json()
            
            if not assets or len(assets) == 0:
                logger.warning(f"Document asset not found for {document_id}")
                return None
            
            asset_id = assets[0]["id"]
            
            # 构建更新payload
            payload = {}
            if document_metadata.title is not None:
                payload["display_name"] = document_metadata.title
            if document_metadata.source is not None:
                payload["source_system"] = document_metadata.source
            if document_metadata.file_path is not None:
                payload["source_path"] = document_metadata.file_path
            if document_metadata.author is not None:
                payload["business_owner"] = document_metadata.author
                payload["technical_owner"] = document_metadata.author
            if document_metadata.tags is not None:
                payload["tags"] = document_metadata.tags
            if document_metadata.access_level is not None:
                payload["classification"] = document_metadata.access_level
            
            # 更新schema_info
            schema_updates = {}
            if document_metadata.document_type is not None:
                schema_updates["document_type"] = document_metadata.document_type
            if document_metadata.language is not None:
                schema_updates["language"] = document_metadata.language
            if document_metadata.filename is not None:
                schema_updates["filename"] = document_metadata.filename
            if document_metadata.file_size is not None:
                schema_updates["file_size"] = document_metadata.file_size
            
            if schema_updates:
                payload["schema_info"] = schema_updates
            
            # 更新sample_data
            sample_updates = {}
            if document_metadata.topics is not None:
                sample_updates["topics"] = document_metadata.topics
            if document_metadata.entities is not None:
                sample_updates["entities"] = document_metadata.entities
            
            if sample_updates:
                payload["sample_data"] = sample_updates
            
            # 更新质量指标
            quality_updates = {}
            if document_metadata.quality_score is not None:
                quality_updates["quality_score"] = document_metadata.quality_score
            if document_metadata.vector_embedding_status is not None:
                quality_updates["vector_embedding_status"] = document_metadata.vector_embedding_status
            if document_metadata.search_popularity is not None:
                quality_updates["search_popularity"] = document_metadata.search_popularity
                payload["record_count"] = document_metadata.search_popularity
            
            if quality_updates:
                payload["data_quality_metrics"] = quality_updates
            
            # 更新metadata
            metadata_updates = {}
            if document_metadata.created_date is not None:
                metadata_updates["created_date"] = document_metadata.created_date.isoformat()
            if document_metadata.modified_date is not None:
                metadata_updates["modified_date"] = document_metadata.modified_date.isoformat()
                payload["last_updated"] = document_metadata.modified_date
            if document_metadata.vector_embedding_status is not None:
                metadata_updates["vector_embedding_status"] = document_metadata.vector_embedding_status
            if document_metadata.metadata is not None:
                metadata_updates.update(document_metadata.metadata)
            
            if metadata_updates:
                payload["metadata"] = metadata_updates
            
            if document_metadata.file_size is not None:
                payload["size_bytes"] = document_metadata.file_size
            
            response = await client.put(f"/api/data-assets/{asset_id}", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Document metadata updated for {document_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Document metadata not found for {document_id}")
            else:
                logger.error(f"Failed to update document metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error updating document metadata: {str(e)}", exc_info=True)
            return None
    
    async def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档元数据
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档元数据，如果不存在返回None
        """
        try:
            client = await self._get_client()
            
            # 通过搜索查找文档资产
            response = await client.get(
                f"/api/data-assets",
                params={"search": document_id, "asset_type": "file"}
            )
            response.raise_for_status()
            
            assets = response.json()
            if assets and len(assets) > 0:
                logger.debug(f"Retrieved document metadata for {document_id}")
                return assets[0]
            
            return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Document metadata not found for {document_id}")
            else:
                logger.error(f"Failed to get document metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}", exc_info=True)
            return None
    
    async def update_quality_score(
        self,
        document_id: str,
        quality_score: float
    ) -> bool:
        """
        更新文档质量分数
        
        Args:
            document_id: 文档ID
            quality_score: 质量分数（0.0-1.0）
            
        Returns:
            是否更新成功
        """
        update = DocumentMetadataUpdate(
            quality_score=quality_score
        )
        result = await self.update_document_metadata(document_id, update)
        return result is not None
    
    async def update_search_popularity(
        self,
        document_id: str,
        popularity: int
    ) -> bool:
        """
        更新文档搜索热度
        
        Args:
            document_id: 文档ID
            popularity: 搜索热度
            
        Returns:
            是否更新成功
        """
        update = DocumentMetadataUpdate(
            search_popularity=popularity
        )
        result = await self.update_document_metadata(document_id, update)
        return result is not None
    
    async def update_vector_embedding_status(
        self,
        document_id: str,
        status: str
    ) -> bool:
        """
        更新向量嵌入状态
        
        Args:
            document_id: 文档ID
            status: 嵌入状态（如：pending, completed, failed）
            
        Returns:
            是否更新成功
        """
        update = DocumentMetadataUpdate(
            vector_embedding_status=status
        )
        result = await self.update_document_metadata(document_id, update)
        return result is not None


# 全局服务实例（单例）
_metadata_enrichment: Optional[MetadataEnrichment] = None


def get_metadata_enrichment() -> MetadataEnrichment:
    """获取元数据增强服务实例（单例）"""
    global _metadata_enrichment
    if _metadata_enrichment is None:
        _metadata_enrichment = MetadataEnrichment()
    return _metadata_enrichment


async def close_metadata_enrichment():
    """关闭元数据增强服务"""
    global _metadata_enrichment
    if _metadata_enrichment:
        await _metadata_enrichment.close()
        _metadata_enrichment = None

