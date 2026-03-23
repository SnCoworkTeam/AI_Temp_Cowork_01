"""
SAP元数据智能体API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..core.sap_metadata_orchestrator import SAPMetadataOrchestrator
from ..models.sap_metadata_models import SAPDiscoveryResult
from ..services.sap_ontology_extractor import SAPOntologyExtractor

router = APIRouter(prefix="/api/sap-metadata", tags=["SAP Metadata"])


# 全局编排器实例（由main.py设置）
_orchestrator_instance: Optional[SAPMetadataOrchestrator] = None

def set_orchestrator(orchestrator: SAPMetadataOrchestrator):
    """设置编排器实例"""
    global _orchestrator_instance
    _orchestrator_instance = orchestrator

def get_orchestrator() -> SAPMetadataOrchestrator:
    """获取SAP元数据编排器实例"""
    if _orchestrator_instance is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator_instance


@router.post(
    "/discover",
    response_model=SAPDiscoveryResult,
    summary="发现SAP元数据",
    description="发现并构建完整的SAP ERP元数据，包括数据资产、业务实体和业务流程"
)
async def discover_sap_metadata(
    include_database: bool = Body(True, description="是否从数据库发现"),
    include_odata: bool = Body(True, description="是否从OData服务发现"),
    include_bapi: bool = Body(False, description="是否从TFDIR表发现BAPI/RFC函数"),
    build_semantic_index: bool = Body(True, description="是否构建语义索引"),
    sync_to_metadata_service: bool = Body(True, description="是否同步到元数据服务"),
    limit: Optional[int] = Body(None, description="限制处理的服务数量（分批处理）"),
    offset: int = Body(0, description="起始偏移量（分批处理）"),
    knowledge_base_id: Optional[str] = Body(None, description="知识库ID，用于将语义索引文档关联到指定知识库"),
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    发现SAP元数据
    
    执行完整的SAP元数据发现流程：
    1. 从数据库和OData服务发现数据资产
    2. 提取业务实体
    3. 分析业务流程
    4. 构建语义索引（可选）
    5. 同步到元数据服务（可选）
    """
    try:
        result = await orchestrator.orchestrate_sap_metadata(
            include_database=include_database,
            include_odata=include_odata,
            include_bapi=include_bapi,
            build_semantic_index=build_semantic_index,
            sync_to_metadata_service=sync_to_metadata_service,
            limit=limit,
            offset=offset,
            knowledge_base_id=knowledge_base_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover SAP metadata: {str(e)}")


@router.get(
    "/assets",
    summary="获取SAP数据资产",
    description="获取已发现的SAP数据资产列表"
)
async def get_sap_assets(
    asset_type: Optional[str] = Query(None, description="资产类型过滤"),
    domain: Optional[str] = Query(None, description="业务域过滤"),
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    获取SAP数据资产
    
    支持按资产类型和业务域过滤
    """
    try:
        # 重新发现或从缓存获取
        result = await orchestrator.orchestrate_sap_metadata(
            include_database=True,
            include_odata=True,
            build_semantic_index=False,
            sync_to_metadata_service=False
        )
        
        assets = result.data_assets
        
        # 过滤
        if asset_type:
            assets = [a for a in assets if a.get('asset_type') == asset_type]
        if domain:
            assets = [a for a in assets if a.get('sap_module') == domain]
        
        return {
            "total": len(assets),
            "assets": assets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SAP assets: {str(e)}")


@router.get(
    "/entities",
    summary="获取SAP业务实体",
    description="获取已提取的SAP业务实体列表"
)
async def get_sap_entities(
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    domain: Optional[str] = Query(None, description="业务域过滤"),
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    获取SAP业务实体
    
    支持按实体类型和业务域过滤
    """
    try:
        result = await orchestrator.orchestrate_sap_metadata(
            include_database=True,
            include_odata=True,
            build_semantic_index=False,
            sync_to_metadata_service=False
        )
        
        entities = result.business_entities
        
        # 过滤
        if entity_type:
            entities = [e for e in entities if e.get('entity_type') == entity_type]
        if domain:
            entities = [e for e in entities if e.get('business_domain') == domain]
        
        return {
            "total": len(entities),
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SAP entities: {str(e)}")


@router.get(
    "/processes",
    summary="获取SAP业务流程",
    description="获取已分析的SAP业务流程列表"
)
async def get_sap_processes(
    domain: Optional[str] = Query(None, description="业务域过滤"),
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    获取SAP业务流程
    
    支持按业务域过滤
    """
    try:
        result = await orchestrator.orchestrate_sap_metadata(
            include_database=True,
            include_odata=True,
            build_semantic_index=False,
            sync_to_metadata_service=False
        )
        
        processes = result.business_processes
        
        # 过滤
        if domain:
            processes = [p for p in processes if p.get('domain') == domain]
        
        return {
            "total": len(processes),
            "processes": processes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SAP processes: {str(e)}")


@router.get(
    "/processes/{process_name}",
    summary="获取业务流程详情",
    description="获取指定业务流程的详细信息"
)
async def get_business_process(
    process_name: str,
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    获取业务流程详情
    """
    try:
        result = await orchestrator.orchestrate_sap_metadata(
            include_database=True,
            include_odata=True,
            build_semantic_index=False,
            sync_to_metadata_service=False
        )
        
        process = next(
            (p for p in result.business_processes if p.get('name') == process_name),
            None
        )
        
        if not process:
            raise HTTPException(status_code=404, detail=f"Process {process_name} not found")
        
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process: {str(e)}")


@router.post(
    "/search/semantic",
    summary="语义搜索SAP元数据",
    description="使用语义搜索查找SAP元数据"
)
async def semantic_search(
    query: str = Body(..., description="搜索查询"),
    domain: Optional[str] = Body(None, description="业务域过滤"),
    limit: int = Body(10, description="返回结果数量")
):
    """
    语义搜索SAP元数据
    
    通过知识库进行语义搜索
    """
    # TODO: 实现语义搜索
    return {
        "query": query,
        "domain": domain,
        "results": [],
        "total": 0
    }


@router.get(
    "/build-status",
    summary="获取构建状态",
    description="获取SAP元数据构建的当前状态和统计信息"
)
async def get_build_status(
    orchestrator: SAPMetadataOrchestrator = Depends(get_orchestrator)
):
    """
    获取构建状态
    
    返回当前已构建的元数据统计信息
    """
    try:
        # 获取总服务数
        total_services = 0
        if orchestrator.mcp_client:
            try:
                all_services = await orchestrator.mcp_client.discover_services()
                total_services = len(all_services)
            except:
                pass
        
        # 从metadata-service获取已同步的数据
        total_assets = 0
        total_entities = 0
        
        if orchestrator.metadata_client:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # 获取数据资产总数
                    assets_response = await client.get(
                        f"{orchestrator.metadata_client.base_url}/api/data-assets?limit=1"
                    )
                    if assets_response.status_code == 200:
                        assets_data = assets_response.json()
                        total_assets = assets_data.get('total', 0)
                    
                    # 获取业务实体总数
                    entities_response = await client.get(
                        f"{orchestrator.metadata_client.base_url}/api/business-entities?limit=1"
                    )
                    if entities_response.status_code == 200:
                        entities_data = entities_response.json()
                        total_entities = entities_data.get('total', 0)
            except:
                pass
        
        return {
            "total_services": total_services,
            "synced_assets": total_assets,
            "synced_entities": total_entities,
            "build_progress": {
                "services_processed": 0,  # 需要从实际构建中获取
                "services_total": total_services,
                "percentage": 0.0 if total_services == 0 else (total_assets / total_services * 100) if total_services > 0 else 0.0
            },
            "status": "ready" if total_services > 0 else "no_services"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build status: {str(e)}")


@router.get(
    "/health",
    summary="健康检查",
    description="检查SAP元数据智能体健康状态"
)
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "sap-metadata-agent",
        "version": "1.0.0"
    }


@router.post(
    "/ontology/extract",
    summary="提取SAP业务概念并发布到metadata-service",
    description="从OData服务元数据中提取业务概念，并批量发布到metadata-service"
)
async def extract_sap_ontology(
    service_ids: Optional[List[str]] = Body(None, description="要处理的服务ID列表（None表示处理所有服务）"),
    batch_size: int = Body(20, ge=1, le=100, description="批处理大小"),
    enable_idempotency: bool = Body(True, description="是否启用幂等性检查（跳过已存在的实体）")
):
    """
    提取SAP业务概念并发布到metadata-service
    
    执行流程：
    1. 发现OData服务（如果service_ids为None，则发现所有服务）
    2. 获取每个服务的$metadata XML
    3. 解析元数据，提取EntitySet、EntityType、NavigationProperty
    4. 提取SAP注解（sapLabel、sapSemantics）
    5. 推断模块和子模块
    6. 转换为BusinessEntity格式
    7. 批量发布到metadata-service
    """
    extractor = None
    try:
        extractor = SAPOntologyExtractor()
        result = await extractor.extract_and_publish_concepts(
            service_ids=service_ids,
            batch_size=batch_size,
            enable_idempotency=enable_idempotency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract SAP ontology: {str(e)}")
    finally:
        if extractor:
            await extractor.close()

