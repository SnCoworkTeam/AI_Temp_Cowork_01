"""
知识库元数据采集器
从knowledge-base服务采集文档元数据
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class KnowledgeCollector(BaseCollector):
    """知识库元数据采集器"""
    
    def __init__(self, knowledge_base_url: str = "http://knowledge-base:8004", **kwargs):
        """
        初始化知识库采集器
        
        Args:
            knowledge_base_url: Knowledge Base服务URL
            **kwargs: 其他参数传递给BaseCollector
        """
        super().__init__(
            source_service_url=knowledge_base_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从Knowledge Base采集文档元数据
        
        Returns:
            文档元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取所有文档列表
            response = await client.get("/api/documents")
            response.raise_for_status()
            
            documents_data = response.json()
            documents = documents_data.get("documents", []) if isinstance(documents_data, dict) else documents_data
            
            metadata_list = []
            for doc in documents:
                try:
                    doc_id = doc.get("id", "")
                    doc_metadata = doc.get("metadata", {})
                    
                    # 转换文档信息为数据资产格式
                    asset_metadata = {
                        "name": doc_id,
                        "display_name": doc.get("filename", doc_metadata.get("title", doc_id)),
                        "description": f"Document: {doc.get('filename', doc_id)}",
                        "asset_type": "file",
                        "source_system": "knowledge-base",
                        "source_path": doc.get("file_path", ""),
                        "schema_info": {
                            "document_type": doc.get("file_type", ""),
                            "language": doc_metadata.get("language", ""),
                            "filename": doc.get("filename", ""),
                            "file_size": doc.get("file_size", 0),
                            "page_count": doc_metadata.get("page_count"),
                            "word_count": doc_metadata.get("word_count")
                        },
                        "sample_data": {
                            "topics": doc.get("tags", []),
                            "entities": []
                        },
                        "data_quality_metrics": {
                            "quality_score": 0.8,  # 默认值，可以从质量评估服务获取
                            "vector_embedding_status": "completed" if doc.get("status") == "processed" else "pending"
                        },
                        "business_owner": doc.get("created_by", ""),
                        "technical_owner": doc.get("created_by", ""),
                        "tags": doc.get("tags", []),
                        "classification": "document",
                        "record_count": doc.get("total_chunks", 0),
                        "size_bytes": doc.get("file_size", 0),
                        "last_updated": doc.get("updated_at") or doc.get("processed_at"),
                        "update_frequency": "on_demand",
                        "metadata": {
                            "uploaded_at": doc.get("uploaded_at"),
                            "processed_at": doc.get("processed_at"),
                            "status": doc.get("status", ""),
                            "version": doc.get("version", 1),
                            "author": doc_metadata.get("author"),
                            "creation_date": doc_metadata.get("creation_date"),
                            "modification_date": doc_metadata.get("modification_date"),
                            **doc_metadata.get("custom_metadata", {})
                        }
                    }
                    metadata_list.append(asset_metadata)
                except Exception as e:
                    logger.warning(f"Failed to process document {doc.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return metadata_list
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to collect documents: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error collecting documents: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步文档元数据到元数据服务
        
        Args:
            metadata_list: 文档元数据列表
            
        Returns:
            同步结果统计
        """
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                asset_name = metadata.get("name")
                
                # 通过搜索查找现有资产
                search_response = await client.get(
                    "/api/data-assets",
                    params={"search": asset_name, "asset_type": "file"}
                )
                search_response.raise_for_status()
                existing_assets = search_response.json()
                
                if existing_assets and len(existing_assets) > 0:
                    # 更新现有记录
                    asset_id = existing_assets[0]["id"]
                    response = await client.put(f"/api/data-assets/{asset_id}", json=metadata)
                else:
                    # 创建新记录
                    response = await client.post("/api/data-assets", json=metadata)
                
                response.raise_for_status()
                synced += 1
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to sync document {metadata.get('name', 'unknown')}: {e.response.status_code} - {e.response.text}")
                errors += 1
            except Exception as e:
                logger.error(f"Error syncing document {metadata.get('name', 'unknown')}: {str(e)}")
                errors += 1
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "errors": errors,
            "message": f"Synced {synced}/{len(metadata_list)} documents"
        }

