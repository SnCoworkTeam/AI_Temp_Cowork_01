"""
SAP元数据编排器
统一管理SAP元数据全生命周期
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.sap_metadata_models import SAPDiscoveryResult
from .sap_data_asset_discoverer import SAPDataAssetDiscoverer
from .sap_business_entity_extractor import SAPBusinessEntityExtractor
from .sap_business_process_analyzer import SAPBusinessProcessAnalyzer
from .sap_semantic_index_builder import SAPSemanticIndexBuilder
from .sap_business_term_mapper import SAPBusinessTermMapper
from ..services.sap_database_client import SAPDatabaseClient
from ..services.sap_mcp_client import SAPMCPClient
from ..services.metadata_client import MetadataClient
from typing import List

logger = logging.getLogger(__name__)


class SAPMetadataOrchestrator:
    """SAP元数据编排器"""
    
    def __init__(
        self,
        db_client: Optional[SAPDatabaseClient] = None,
        mcp_client: Optional[SAPMCPClient] = None,
        metadata_client: Optional[MetadataClient] = None,
        knowledge_base_url: Optional[str] = None
    ):
        """
        初始化SAP元数据编排器
        
        Args:
            db_client: SAP数据库客户端
            mcp_client: SAP MCP客户端
            metadata_client: 元数据服务客户端
            knowledge_base_url: 知识库服务URL
        """
        self.db_client = db_client
        self.mcp_client = mcp_client
        self.metadata_client = metadata_client
        
        # 初始化组件
        self.asset_discoverer = SAPDataAssetDiscoverer(db_client, mcp_client)
        self.entity_extractor = SAPBusinessEntityExtractor(self.asset_discoverer)
        self.process_analyzer = SAPBusinessProcessAnalyzer()
        self.semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
        self.term_mapper = SAPBusinessTermMapper()
    
    async def orchestrate_sap_metadata(
        self,
        include_database: bool = True,
        include_odata: bool = True,
        include_bapi: bool = False,
        build_semantic_index: bool = True,
        sync_to_metadata_service: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
        knowledge_base_id: Optional[str] = None
    ) -> SAPDiscoveryResult:
        """
        编排SAP元数据全生命周期
        
        Args:
            include_database: 是否从数据库发现
            include_odata: 是否从OData服务发现
            include_bapi: 是否从TFDIR表发现BAPI/RFC函数
            build_semantic_index: 是否构建语义索引
            sync_to_metadata_service: 是否同步到元数据服务
            limit: 限制处理的服务数量（分批处理）
            offset: 起始偏移量（分批处理）
            knowledge_base_id: 知识库ID，用于将语义索引文档关联到指定知识库
            
        Returns:
            发现结果
        """
        logger.info("Starting SAP metadata orchestration...")
        
        results = {
            "data_assets": [],
            "business_entities": [],
            "business_processes": [],
            "tables_discovered": 0,
            "odata_services_discovered": 0,
            "discovery_time": datetime.now(),
            "metadata": {}
        }
        
        try:
            # 1. 发现数据资产（支持分批处理）
            # 如果只构建语义索引，从metadata-service获取现有资产
            if build_semantic_index and not include_database and not include_odata:
                logger.info("Step 1: Loading existing data assets from metadata service for semantic indexing...")
                if self.metadata_client:
                    try:
                        # 从metadata-service获取所有SAP数据资产（分批获取）
                        from ..models.sap_metadata_models import SAPDataAsset, SAPAssetType
                        assets = []
                        page_size = 100
                        offset = 0
                        
                        while True:
                            metadata_assets = await self.metadata_client.list_data_assets(
                                limit=page_size,
                                offset=offset,
                                source_system="SAP"
                            )
                            
                            if not metadata_assets:
                                break
                            
                            # 记录进度
                            logger.info(f"Loading assets: {offset + len(metadata_assets)} loaded...")
                            
                            # 转换为SAPDataAsset格式
                            for meta_asset in metadata_assets:
                                try:
                                    # 提取业务术语和语义关系
                                    metadata_dict = meta_asset.get("metadata", {})
                                    if isinstance(metadata_dict, str):
                                        import json
                                        try:
                                            metadata_dict = json.loads(metadata_dict)
                                        except:
                                            metadata_dict = {}
                                    
                                    asset = SAPDataAsset(
                                        name=meta_asset.get("name", ""),
                                        display_name=meta_asset.get("display_name", ""),
                                        description=meta_asset.get("description", ""),
                                        asset_type=SAPAssetType(meta_asset.get("asset_type", "table")),
                                        schema_info=meta_asset.get("schema_info", {}),
                                        classification=meta_asset.get("classification", ""),
                                        tags=meta_asset.get("tags", []),
                                        business_terms=metadata_dict.get("business_terms", []),
                                        semantic_relationships=metadata_dict.get("semantic_relationships", []),
                                        metadata=metadata_dict
                                    )
                                    # 添加SAP特定字段
                                    if metadata_dict:
                                        asset.sap_table_name = metadata_dict.get("sap_table_name")
                                        asset.sap_module = metadata_dict.get("sap_module")
                                        asset.odata_service = metadata_dict.get("odata_service")
                                        asset.odata_entity = metadata_dict.get("odata_entity")
                                    
                                    assets.append(asset)
                                except Exception as e:
                                    logger.warning(f"Failed to convert metadata asset {meta_asset.get('name', 'unknown')} to SAPDataAsset: {e}")
                            
                            if len(metadata_assets) < page_size:
                                break
                            
                            offset += page_size
                        
                        logger.info(f"Loaded {len(assets)} existing assets from metadata service")
                    except Exception as e:
                        logger.warning(f"Failed to load assets from metadata service: {e}, using empty list")
                        assets = []
                else:
                    logger.warning("Metadata client not available, cannot load existing assets")
                    assets = []
            else:
                logger.info(f"Step 1: Discovering data assets (limit={limit}, offset={offset})...")
                assets = await self.asset_discoverer.discover_all_assets(
                    include_database=include_database,
                    include_odata=include_odata,
                    include_bapi=include_bapi,
                    limit=limit,
                    offset=offset
                )
            
            results["data_assets"] = [asset.model_dump() for asset in assets]
            results["tables_discovered"] = len([a for a in assets if a.sap_table_name])
            results["odata_services_discovered"] = len([a for a in assets if a.odata_service])
            
            # 获取总服务数
            if self.mcp_client and include_odata:
                try:
                    all_services = await self.mcp_client.discover_services()
                    results["metadata"]["total_services"] = len(all_services)
                    results["metadata"]["processed_services"] = len(assets)
                    results["metadata"]["has_more"] = limit is not None and (offset + (limit or 0)) < len(all_services)
                except:
                    results["metadata"]["total_services"] = len(assets)
                    results["metadata"]["processed_services"] = len(assets)
            
            logger.info(f"Discovered {len(assets)} data assets")
            
            # 2. 提取业务实体
            logger.info("Step 2: Extracting business entities...")
            entities = await self.entity_extractor.extract_entities(results["data_assets"])
            results["business_entities"] = [entity.model_dump() for entity in entities]
            logger.info(f"Extracted {len(entities)} business entities")
            
            # 2.5. 构建业务术语映射
            logger.info("Step 2.5: Building business term mappings...")
            term_mappings = []
            semantic_relationships = []
            
            # 从资产中提取业务术语
            for asset_dict in results["data_assets"]:
                # 转换为SAPDataAsset对象（简化处理）
                from ..models.sap_metadata_models import SAPDataAsset, SAPAssetType, SAPBusinessDomain
                try:
                    asset = SAPDataAsset(
                        name=asset_dict.get("name", ""),
                        display_name=asset_dict.get("display_name"),
                        description=asset_dict.get("description"),
                        asset_type=SAPAssetType(asset_dict.get("asset_type", "table")),
                        sap_table_name=asset_dict.get("sap_table_name"),
                        sap_module=SAPBusinessDomain(asset_dict.get("sap_module")) if asset_dict.get("sap_module") else None,
                        schema_info=asset_dict.get("schema_info"),
                        classification=asset_dict.get("classification"),
                        business_terms=asset_dict.get("business_terms", []),
                        metadata=asset_dict.get("metadata", {})
                    )
                    # 提取业务术语（如果还没有）
                    if not asset.business_terms:
                        terms = self.term_mapper.extract_business_terms_from_asset(asset)
                        term_mappings.extend(terms)
                        # 更新资产字典中的业务术语
                        asset_dict["business_terms"] = [t["business_term"] for t in terms]
                    else:
                        # 如果已有业务术语，创建映射
                        for term in asset.business_terms:
                            term_mapping = self.term_mapper.create_term_mapping(
                                business_term=term,
                                technical_assets=[asset.sap_table_name] if asset.sap_table_name else []
                            )
                            term_mappings.append(term_mapping)
                except Exception as e:
                    logger.warning(f"Failed to extract terms from asset {asset_dict.get('name')}: {e}")
            
            # 构建语义关系
            if entities:
                try:
                    # 转换资产为SAPDataAsset对象
                    asset_objects = []
                    for asset_dict in results["data_assets"]:
                        try:
                            from ..models.sap_metadata_models import SAPDataAsset, SAPAssetType, SAPBusinessDomain
                            asset_obj = SAPDataAsset(
                                name=asset_dict.get("name", ""),
                                display_name=asset_dict.get("display_name"),
                                description=asset_dict.get("description"),
                                asset_type=SAPAssetType(asset_dict.get("asset_type", "table")),
                                sap_table_name=asset_dict.get("sap_table_name"),
                                sap_module=SAPBusinessDomain(asset_dict.get("sap_module")) if asset_dict.get("sap_module") else None,
                                schema_info=asset_dict.get("schema_info"),
                                classification=asset_dict.get("classification"),
                                business_terms=asset_dict.get("business_terms", []),
                                metadata=asset_dict.get("metadata", {})
                            )
                            asset_objects.append(asset_obj)
                        except Exception as e:
                            logger.warning(f"Failed to convert asset to SAPDataAsset: {e}")
                    
                    relationships = self.term_mapper.build_semantic_relationships(
                        asset_objects,
                        entities
                    )
                    semantic_relationships.extend(relationships)
                    
                    # 将语义关系添加到资产中
                    for asset_dict in results["data_assets"]:
                        asset_name = asset_dict.get("name")
                        asset_relationships = [
                            rel for rel in semantic_relationships 
                            if rel.get("source", "").endswith(f":{asset_name}")
                        ]
                        if asset_relationships:
                            asset_dict["semantic_relationships"] = asset_relationships
                except Exception as e:
                    logger.warning(f"Failed to build semantic relationships: {e}")
            
            results["metadata"]["term_mappings"] = term_mappings
            results["metadata"]["semantic_relationships"] = semantic_relationships
            logger.info(f"Built {len(term_mappings)} term mappings and {len(semantic_relationships)} semantic relationships")
            
            # 3. 分析业务流程
            logger.info("Step 3: Analyzing business processes...")
            processes = await self.process_analyzer.analyze_processes(results["data_assets"])
            results["business_processes"] = [process.model_dump() for process in processes]
            logger.info(f"Analyzed {len(processes)} business processes")
            
            # 4. 构建语义索引
            if build_semantic_index:
                logger.info("Step 4: Building semantic index...")
                if knowledge_base_id:
                    logger.info(f"语义索引将关联到知识库: {knowledge_base_id}")
                index_result = await self.semantic_builder.build_semantic_index(
                    results["data_assets"],
                    results["business_entities"],
                    results["business_processes"],
                    knowledge_base_id=knowledge_base_id
                )
                results["metadata"]["semantic_index"] = index_result
                logger.info(f"Built semantic index: {index_result['indexed']} documents")
            
            # 5. 同步到元数据服务
            if sync_to_metadata_service and self.metadata_client:
                logger.info("Step 5: Syncing to metadata service...")
                sync_result = await self._sync_to_metadata_service(
                    results["data_assets"],
                    results["business_entities"]
                )
                results["metadata"]["sync_result"] = sync_result
                logger.info(f"Synced to metadata service: {sync_result}")
            
            logger.info("SAP metadata orchestration completed successfully")
            
        except Exception as e:
            logger.error(f"Error in SAP metadata orchestration: {e}", exc_info=True)
            results["metadata"]["error"] = str(e)
        
        return SAPDiscoveryResult(**results)
    
    async def _sync_to_metadata_service(
        self,
        assets: List[Dict[str, Any]],
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        同步到元数据服务
        
        Args:
            assets: 数据资产列表
            entities: 业务实体列表
            
        Returns:
            同步结果
        """
        # 转换数据资产格式
        data_assets = []
        for asset in assets:
            # 转换为metadata-service的数据资产格式
            data_asset = {
                "name": asset.get('name'),
                "display_name": asset.get('display_name'),
                "description": asset.get('description'),
                "asset_type": self._map_asset_type(asset.get('asset_type')),
                "source_system": "SAP",
                "source_path": asset.get('sap_table_name') or asset.get('odata_entity'),
                "schema_info": asset.get('schema_info'),
                "tags": asset.get('tags', []),
                "classification": asset.get('classification'),
                "metadata": {
                    "business_terms": asset.get('business_terms', []),
                    "semantic_relationships": asset.get('semantic_relationships', []),
                    "semantic_embedding": asset.get('semantic_embedding'),
                    **asset.get('metadata', {}),
                    "sap_table_name": asset.get('sap_table_name'),
                    "sap_module": asset.get('sap_module'),
                    "odata_service": asset.get('odata_service'),
                    "odata_entity": asset.get('odata_entity')
                }
            }
            data_assets.append(data_asset)
        
        # 转换业务实体格式
        business_entities = []
        for entity in entities:
            business_entity = {
                "name": entity.get('name'),
                "display_name": entity.get('display_name'),
                "description": entity.get('description'),
                "entity_type": "concept",  # 使用concept类型
                "business_definition": f"SAP业务实体: {entity.get('display_name')}",
                "tags": ["SAP", "business_entity", entity.get('entity_type')],
                "metadata": {
                    **entity.get('metadata', {}),
                    "sap_table_name": entity.get('sap_table_name'),
                    "entity_type": entity.get('entity_type'),
                    "business_domain": entity.get('business_domain'),
                    "key_fields": entity.get('key_fields', []),
                    "business_terms": entity.get('business_terms', []),
                    "semantic_relationships": entity.get('semantic_relationships', [])
                }
            }
            business_entities.append(business_entity)
        
        # 批量创建
        assets_result = await self.metadata_client.batch_create_data_assets(data_assets)
        entities_result = await self.metadata_client.batch_create_business_entities(business_entities)
        
        return {
            "data_assets": assets_result,
            "business_entities": entities_result
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

