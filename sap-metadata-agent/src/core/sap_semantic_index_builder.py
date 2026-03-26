"""
SAP语义索引构建器
为SAP元数据构建语义索引，支持智能搜索
"""
import logging
from typing import List, Dict, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)


class SAPSemanticIndexBuilder:
    """SAP语义索引构建器"""
    
    def __init__(self, knowledge_base_url: Optional[str] = None):
        """
        初始化语义索引构建器
        
        Args:
            knowledge_base_url: 知识库服务URL
        """
        # 优先使用传入的URL，然后是环境变量，最后是默认值
        # 默认使用localhost而不是Docker容器名，以便本地测试
        self.knowledge_base_url = knowledge_base_url or os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://localhost:8004"  # 改为localhost，便于本地测试
        )
        logger.info(f"SAPSemanticIndexBuilder初始化，知识库URL: {self.knowledge_base_url}")
        
        # 创建HTTP客户端，明确禁用所有代理和Docker相关配置
        # 确保不会触发任何Docker API调用
        self.http_client = httpx.AsyncClient(
            timeout=120.0,  # 增加超时时间到120秒
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
    
    async def build_semantic_index(
        self,
        assets: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        processes: List[Dict[str, Any]],
        knowledge_base_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建语义索引
        
        Args:
            assets: 数据资产列表
            entities: 业务实体列表
            processes: 业务流程列表
            knowledge_base_id: 知识库ID，用于关联文档到指定知识库
            
        Returns:
            索引构建结果
        """
        indexed = 0
        failed = 0
        
        # 为数据资产构建索引
        for asset in assets:
            try:
                doc = await self._create_semantic_document(asset, "data_asset")
                result = await self._store_document(doc, knowledge_base_id)
                if result:
                    indexed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"Failed to index asset {asset.get('name')}: {e}")
                failed += 1
        
        # 为业务实体构建索引
        for entity in entities:
            try:
                doc = await self._create_semantic_document(entity, "business_entity")
                result = await self._store_document(doc, knowledge_base_id)
                if result:
                    indexed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"Failed to index entity {entity.get('name')}: {e}")
                failed += 1
        
        # 为业务流程构建索引
        for process in processes:
            try:
                doc = await self._create_semantic_document(process, "business_process")
                result = await self._store_document(doc, knowledge_base_id)
                if result:
                    indexed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning(f"Failed to index process {process.get('name')}: {e}")
                failed += 1
        
        logger.info(f"Built semantic index: {indexed} indexed, {failed} failed")
        return {
            "indexed": indexed,
            "failed": failed,
            "total": indexed + failed
        }
    
    async def _create_semantic_document(
        self,
        item: Dict[str, Any],
        item_type: str
    ) -> Dict[str, Any]:
        """
        创建语义文档（增强版，包含业务术语和向量嵌入信息）
        
        Args:
            item: 数据项（资产、实体或流程）
            item_type: 项类型
            
        Returns:
            语义文档字典
        """
        # 构建文档内容
        content_parts = []
        
        # 基本信息
        if item.get('name'):
            content_parts.append(f"名称: {item['name']}")
        if item.get('display_name'):
            content_parts.append(f"显示名称: {item['display_name']}")
        if item.get('description'):
            content_parts.append(f"描述: {item['description']}")
        
        # 业务术语
        if item.get('business_terms'):
            content_parts.append(f"业务术语: {', '.join(item['business_terms'])}")
        
        # 分类信息
        if item.get('classification'):
            content_parts.append(f"分类: {item['classification']}")
        
        # 标签
        if item.get('tags'):
            content_parts.append(f"标签: {', '.join(item['tags'])}")
        
        # SAP特定信息
        if item.get('sap_table_name'):
            content_parts.append(f"SAP表: {item['sap_table_name']}")
        if item.get('sap_module'):
            content_parts.append(f"SAP模块: {item['sap_module']}")
        
        # ABAP字典信息
        if item.get('schema_info') and item['schema_info'].get('abap_dictionary'):
            abap_dict = item['schema_info']['abap_dictionary']
            if abap_dict.get('table_info'):
                table_info = abap_dict['table_info']
                if table_info.get('table_description'):
                    content_parts.append(f"表描述: {table_info['table_description']}")
        
        # 字段信息
        if item.get('schema_info') and item['schema_info'].get('fields'):
            field_descriptions = []
            for field in item['schema_info']['fields']:
                if field.get('field_description'):
                    field_descriptions.append(f"{field.get('field_name', '')}: {field['field_description']}")
            if field_descriptions:
                content_parts.append(f"字段: {'; '.join(field_descriptions[:10])}")  # 限制字段数量
        
        content = "\n".join(content_parts)
        
        # 构建文档
        doc = {
            "id": f"{item_type}_{item.get('name', 'unknown')}",
            "type": item_type,
            "title": item.get('display_name') or item.get('name', ''),
            "content": content,
            "metadata": {
                "name": item.get('name'),
                "display_name": item.get('display_name'),
                "description": item.get('description'),
                "classification": item.get('classification'),
                "tags": item.get('tags', []),
                "business_terms": item.get('business_terms', []),
                "sap_table_name": item.get('sap_table_name'),
                "sap_module": item.get('sap_module'),
                "source_system": item.get('source_system', 'SAP'),
                "semantic_relationships": item.get('semantic_relationships', [])
            }
        }
        
        return doc
    
    async def _store_document(self, doc: Dict[str, Any], knowledge_base_id: Optional[str] = None) -> bool:
        """
        存储文档到知识库
        
        Args:
            doc: 文档
            knowledge_base_id: 知识库ID，用于关联文档到指定知识库
            
        Returns:
            是否成功
        """
        logger.info(f"存储文档到知识库: {doc.get('title', 'unknown')}, knowledge_base_id={knowledge_base_id}")
        
        try:
            # 从metadata中提取tags，如果没有则使用空列表
            metadata = doc.get('metadata', {})
            tags = metadata.get('tags', [])
            if not tags and doc.get('tags'):
                tags = doc.get('tags', [])
            
            # 构建请求数据
            request_data = {
                "title": doc.get('title', 'Untitled'),
                "content": doc.get('content', ''),
                "category": "sap_metadata",
                "tags": tags,
                "metadata": metadata,
                "process_async": False  # 同步处理以便立即索引
            }
            
            # 如果提供了knowledge_base_id，添加到请求数据中
            if knowledge_base_id:
                request_data["knowledge_base_id"] = knowledge_base_id
                logger.info(f"文档将关联到知识库: {knowledge_base_id}")
            
            # 构建请求URL
            url = f"{self.knowledge_base_url}/api/documents/create"
            
            logger.info(f"准备调用知识库服务: {url}")
            logger.debug(f"请求数据: title={request_data['title']}, content_length={len(request_data['content'])}, tags={tags}, knowledge_base_id={knowledge_base_id}")
            
            # 使用知识库服务的文档创建API（支持JSON数据）
            # 确保使用我们配置的HTTP客户端，不会触发任何Docker调用
            response = await self.http_client.post(
                url,
                json=request_data
            )
            
            logger.info(f"知识库服务响应: status={response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"文档创建成功: document_id={result.get('document_id', 'unknown')}, knowledge_base_id={knowledge_base_id}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to store document: HTTP {e.response.status_code} - {e.response.text}")
            logger.error(f"Request URL: {url if 'url' in locals() else 'unknown'}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error when storing document: {e}")
            logger.error(f"Request URL: {url if 'url' in locals() else 'unknown'}")
            return False
        except Exception as e:
            logger.error(f"Failed to store document: {e}", exc_info=True)
            return False
