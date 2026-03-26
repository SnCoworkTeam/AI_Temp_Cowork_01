"""
本体构建API路由（迁移自knowledge-base）
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from ..core.database import SessionLocal
from ..services.metadata_catalog import MetadataCatalogService
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..services.ontology_service import OntologyService
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/ontology", tags=["Ontology"])
logger = setup_logger(__name__)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ontology_service(
    db: Session = Depends(get_db),
    use_llm: bool = True
) -> OntologyService:
    """获取本体服务"""
    catalog = MetadataCatalogService(db)
    kg_repo = KnowledgeGraphRepository(db)
    return OntologyService(db, catalog, kg_repo, use_llm=use_llm)


@router.post("/build", summary="构建业务本体")
async def build_ontology(
    use_llm: bool = Body(True, description="是否使用LLM增强"),
    priority_entities: Optional[List[str]] = Body(None, description="优先处理的实体列表"),
    force_rebuild: bool = Body(False, description="强制重建（即使已存在）"),
    db: Session = Depends(get_db)
):
    """
    从metadata-service的业务实体构建业务本体（增强版）
    
    **迁移说明**: 此功能已从knowledge-base迁移到metadata-service
    - 直接使用metadata-service的数据库，无需HTTP调用
    - 性能更好，数据一致性更强
    - 使用混合方案发现关系（规则引擎 + LLM增强）
    
    **新增功能**:
    - force_rebuild: 强制重建知识图谱（即使已存在）
    - priority_entities: 优先处理的实体列表
    - use_llm: 是否使用LLM增强关系发现
    
    Args:
        use_llm: 是否使用LLM增强关系发现
        priority_entities: 优先处理的实体列表（实体名称列表）
        force_rebuild: 是否强制重建（删除现有知识图谱节点和边）
    
    Returns:
        本体构建结果
    """
    try:
        service = get_ontology_service(db, use_llm=use_llm)
        
        # 如果force_rebuild，先清理现有知识图谱数据
        if force_rebuild:
            logger.info("Force rebuild enabled, cleaning existing knowledge graph data...")
            await service.clean_existing_ontology()
        
        # 构建本体（支持priority_entities）
        result = await service.build_business_ontology(priority_entities=priority_entities)
        await service.relationship_discovery.close()
        return result
    except Exception as e:
        logger.error(f"Failed to build ontology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concepts", summary="获取概念列表")
async def get_concepts(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    db: Session = Depends(get_db)
):
    """
    获取本体概念列表
    
    **迁移说明**: 此功能已从knowledge-base迁移到metadata-service
    
    Args:
        skip: 跳过数量
        limit: 返回数量限制
        node_type: 节点类型过滤（可选）
    
    Returns:
        概念列表
    """
    try:
        service = get_ontology_service(db, use_llm=False)
        concepts = await service.get_concepts(skip=skip, limit=limit, node_type=node_type)
        return {
            "success": True,
            "concepts": concepts,
            "total": len(concepts)
        }
    except Exception as e:
        logger.error(f"Failed to get concepts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sap/build", summary="构建SAP业务本体")
async def build_sap_ontology(
    request: Optional[Dict[str, Any]] = Body(None, description="请求参数"),
    db: Session = Depends(get_db)
):
    """
    构建SAP业务本体（按模块层次组织）
    
    **迁移说明**: 此功能已从knowledge-base迁移到metadata-service
    - 直接使用metadata-service的数据库，无需HTTP调用
    - 支持SAP模块层次结构
    - 使用混合方案发现关系（规则引擎 + LLM增强）
    
    从metadata-service获取SAP业务实体，按模块和子模块组织，构建层次化的知识图谱
    
    Returns:
        本体构建结果，包含模块层次结构
    """
    try:
        use_llm = True
        if request and "use_llm" in request:
            use_llm = request.get("use_llm", True)
        service = get_ontology_service(db, use_llm=use_llm)
        result = await service.build_sap_business_ontology()
        await service.relationship_discovery.close()
        return result
    except Exception as e:
        logger.error(f"Failed to build SAP ontology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

