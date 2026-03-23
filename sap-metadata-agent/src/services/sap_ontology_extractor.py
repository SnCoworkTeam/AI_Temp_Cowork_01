"""
SAP业务概念提取器
从OData元数据中提取业务概念并发布到metadata-service
"""
import logging
import asyncio
import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.sap_odata_metadata_parser import SAPODataMetadataParser
from ..core.sap_module_inference import SAPModuleInference
from .sap_mcp_client import SAPMCPClient

logger = logging.getLogger(__name__)


class SAPOntologyExtractor:
    """SAP业务概念提取器"""
    
    def __init__(
        self,
        mcp_client: Optional[SAPMCPClient] = None,
        metadata_service_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化提取器
        
        Args:
            mcp_client: SAP MCP客户端（可选，默认创建新实例）
            metadata_service_url: metadata-service URL
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.mcp_client = mcp_client or SAPMCPClient()
        self.parser = SAPODataMetadataParser()
        self.module_inference = SAPModuleInference()
        self.metadata_service_url = metadata_service_url or os.getenv(
            "METADATA_SERVICE_URL", 
            "http://metadata-service:8005"
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def extract_and_publish_concepts(
        self,
        service_ids: Optional[List[str]] = None,
        batch_size: int = 20,
        enable_idempotency: bool = True
    ) -> Dict[str, Any]:
        """
        提取业务概念并发布到metadata-service
        
        Args:
            service_ids: 要处理的服务ID列表（None表示处理所有服务）
            batch_size: 批处理大小
            enable_idempotency: 是否启用幂等性检查
            
        Returns:
            提取和发布结果
        """
        results = {
            "success": False,
            "services_processed": 0,
            "concepts_extracted": 0,
            "entities_published": 0,
            "errors": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        try:
            # 1. 发现OData服务
            services = await self._discover_services_with_retry(service_ids)
            logger.info(f"Discovered {len(services)} services to process")
            
            # 2. 批量处理服务
            for i in range(0, len(services), batch_size):
                batch = services[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} services)")
                
                # 并发处理批次
                batch_tasks = [
                    self._process_service(service, enable_idempotency)
                    for service in batch
                ]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 汇总批次结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["errors"].append(str(result))
                        logger.error(f"Batch processing error: {result}", exc_info=True)
                    elif isinstance(result, dict):
                        results["services_processed"] += result.get("services_processed", 0)
                        results["concepts_extracted"] += result.get("concepts_extracted", 0)
                        results["entities_published"] += result.get("entities_published", 0)
                        if result.get("errors"):
                            results["errors"].extend(result["errors"])
            
            results["success"] = len(results["errors"]) == 0
            results["end_time"] = datetime.now().isoformat()
            
            logger.info(
                f"Extraction completed: {results['services_processed']} services, "
                f"{results['concepts_extracted']} concepts, "
                f"{results['entities_published']} entities published"
            )
            
        except Exception as e:
            logger.error(f"Failed to extract and publish concepts: {e}", exc_info=True)
            results["success"] = False
            results["errors"].append(str(e))
            results["end_time"] = datetime.now().isoformat()
        
        return results
    
    async def _process_service(
        self,
        service: Dict[str, Any],
        enable_idempotency: bool
    ) -> Dict[str, Any]:
        """处理单个服务"""
        result = {
            "services_processed": 0,
            "concepts_extracted": 0,
            "entities_published": 0,
            "errors": []
        }
        
        service_id = service.get("serviceId")
        if not service_id:
            result["errors"].append("Service missing serviceId")
            return result
        
        try:
            # 1. 提取概念
            concepts = await self._extract_concepts_with_fallback(service)
            if not concepts:
                logger.warning(f"No concepts extracted from service: {service_id}")
                return result
            
            result["concepts_extracted"] = len(concepts)
            result["services_processed"] = 1
            
            # 2. 转换为BusinessEntity格式
            entities = self._convert_to_business_entities(concepts)
            
            # 3. 发布到metadata-service
            if enable_idempotency:
                # 检查已存在的实体
                existing = await self._check_existing_entities([e["name"] for e in entities])
                entities = [e for e in entities if e["name"] not in existing]
            
            if entities:
                publish_result = await self._publish_entities(entities)
                result["entities_published"] = publish_result.get("published", 0)
                if publish_result.get("errors"):
                    result["errors"].extend(publish_result["errors"])
            
        except Exception as e:
            logger.error(f"Failed to process service {service_id}: {e}", exc_info=True)
            result["errors"].append(f"Service {service_id}: {str(e)}")
        
        return result
    
    async def _discover_services_with_retry(
        self,
        service_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """发现OData服务（带重试）"""
        for attempt in range(self.max_retries):
            try:
                all_services = await self.mcp_client.discover_services()
                
                if service_ids:
                    services = [s for s in all_services if s.get("serviceId") in service_ids]
                else:
                    services = all_services
                
                return services
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Service discovery failed (attempt {attempt + 1}/{self.max_retries}), retrying..."
                    )
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    async def _extract_concepts_with_fallback(
        self,
        service: Dict,
        enable_fallback: bool = True
    ) -> List[Dict]:
        """提取概念（带降级策略）"""
        service_id = service.get("serviceId")
        service_name = service.get("name", service_id)
        
        # 方法1: 从OData元数据提取（主要方法）
        try:
            metadata = await self.mcp_client.get_service_metadata(service_id)
            if metadata:
                parsed = self.parser.parse_metadata(metadata)
                if "error" not in parsed and parsed.get("entities"):
                    concepts = self._convert_to_concepts(parsed["entities"], service)
                    if concepts:
                        logger.info(
                            f"Extracted {len(concepts)} concepts from OData metadata: {service_id}"
                        )
                        return concepts
        except Exception as e:
            logger.warning(f"OData metadata extraction failed for {service_id}: {e}")
            if not enable_fallback:
                raise
        
        # 方法2: 从服务名称推断（降级方法）
        if enable_fallback:
            try:
                module, sub_module, confidence = self.module_inference.infer_module_with_confidence(
                    service_name
                )
                concept = {
                    "name": service_name,
                    "display_name": service_name,
                    "entity_type": "concept",
                    "module": module,
                    "sub_module": sub_module,
                    "properties": [],
                    "navigation_properties": [],
                    "metadata": {
                        "service_id": service_id,
                        "service_name": service_name,
                        "extraction_method": "service_name_inference",
                        "confidence": confidence
                    }
                }
                logger.info(
                    f"Used service name inference for {service_id} (confidence: {confidence:.2f})"
                )
                return [concept]
            except Exception as e:
                logger.warning(f"Service name inference failed for {service_id}: {e}")
        
        # 方法3: 创建基础概念（最终降级）
        if enable_fallback:
            concept = {
                "name": service_name,
                "display_name": service_name,
                "entity_type": "concept",
                "module": "OTHER",
                "sub_module": "General",
                "properties": [],
                "navigation_properties": [],
                "metadata": {
                    "service_id": service_id,
                    "service_name": service_name,
                    "extraction_method": "fallback",
                    "confidence": 0.1
                }
            }
            logger.warning(f"Using fallback concept for {service_id}")
            return [concept]
        
        return []
    
    def _convert_to_concepts(
        self,
        entities: List[Dict],
        service: Dict
    ) -> List[Dict]:
        """将解析的实体转换为业务概念"""
        concepts = []
        service_id = service.get("serviceId")
        service_name = service.get("name", service_id)
        
        for entity in entities:
            # 推断模块
            module, sub_module, confidence = self.module_inference.infer_module_with_confidence(
                service_name,
                entity.get("name")
            )
            
            concept = {
                "name": entity["name"],
                "display_name": entity.get("sap_label") or entity["name"],
                "entity_type": "concept",
                "module": module,
                "sub_module": sub_module,
                "properties": entity.get("properties", []),
                "navigation_properties": entity.get("navigation_properties", []),
                "metadata": {
                    "service_id": service_id,
                    "service_name": service_name,
                    "entity_type": entity.get("type"),
                    "full_type": entity.get("full_type"),
                    "sap_label": entity.get("sap_label"),
                    "properties": entity.get("properties", []),
                    "navigation_properties": entity.get("navigation_properties", []),
                    "keys": entity.get("keys", []),
                    "extraction_method": "odata_metadata",
                    "confidence": confidence
                }
            }
            concepts.append(concept)
        
        return concepts
    
    def _convert_to_business_entities(self, concepts: List[Dict]) -> List[Dict]:
        """转换为BusinessEntity格式"""
        return [
            {
                "name": concept["name"],
                "display_name": concept["display_name"],
                "description": (
                    f"SAP {concept['module']}模块的{concept['display_name']}实体"
                    if concept.get("module") != "OTHER"
                    else f"SAP {concept['display_name']}实体"
                ),
                "entity_type": "concept",
                "metadata": {
                    "source_system": "SAP",
                    "sap_module": concept.get("module"),
                    "sap_sub_module": concept.get("sub_module"),
                    "service_id": concept["metadata"].get("service_id"),
                    "service_name": concept["metadata"].get("service_name"),
                    "sap_label": concept["metadata"].get("sap_label"),
                    "properties": concept.get("properties", []),
                    "navigation_properties": concept.get("navigation_properties", []),
                    "keys": concept["metadata"].get("keys", []),
                    "extraction_method": concept["metadata"].get("extraction_method"),
                    "confidence": concept["metadata"].get("confidence", 1.0)
                }
            }
            for concept in concepts
        ]
    
    async def _check_existing_entities(self, entity_names: List[str]) -> set:
        """检查已存在的实体"""
        try:
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 10000}
            )
            response.raise_for_status()
            entities = response.json()
            
            if isinstance(entities, list):
                existing_names = {e.get("name") for e in entities if e.get("name")}
            elif isinstance(entities, dict):
                entity_list = entities.get("items", entities.get("data", []))
                existing_names = {e.get("name") for e in entity_list if e.get("name")}
            else:
                existing_names = set()
            
            return existing_names & set(entity_names)
        except Exception as e:
            logger.warning(f"Failed to check existing entities: {e}")
            return set()
    
    async def _publish_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """发布实体到metadata-service"""
        result = {
            "published": 0,
            "errors": []
        }
        
        # 批量发布（每次50个）
        batch_size = 50
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            try:
                response = await self.http_client.post(
                    f"{self.metadata_service_url}/api/business-entities/batch",
                    json={"entities": batch}
                )
                response.raise_for_status()
                batch_result = response.json()
                
                if isinstance(batch_result, dict):
                    result["published"] += batch_result.get("created", len(batch))
                else:
                    result["published"] += len(batch)
                
                logger.info(f"Published batch {i // batch_size + 1} ({len(batch)} entities)")
                
            except Exception as e:
                error_msg = f"Failed to publish batch {i // batch_size + 1}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                result["errors"].append(error_msg)
        
        return result
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()

