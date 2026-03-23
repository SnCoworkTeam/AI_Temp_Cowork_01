"""
EA向量化服务
将企业架构实体（业务流程、应用系统、数据实体）向量化并接入语义搜索
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# 导入数据库模型
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    BusinessProcess, ApplicationSystem, DataEntity
)

# 尝试导入向量协调服务
try:
    vector_service_path = project_root / "vector-coordinator-service" / "src"
    if str(vector_service_path) not in sys.path:
        sys.path.insert(0, str(vector_service_path))
    from core.embedding_manager import UnifiedEmbeddingManager, get_unified_embedding_manager
    from core.qdrant_client import QdrantVectorStore
    VECTOR_SERVICES_AVAILABLE = True
except ImportError as e:
    VECTOR_SERVICES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"向量服务未找到，将使用模拟向量: {e}")

if 'logger' not in locals():
    logger = logging.getLogger(__name__)


class EAVectorizationService:
    """EA向量化服务"""
    
    def __init__(self, db: Session, vector_client=None, qdrant_client=None):
        """
        初始化EA向量化服务
        
        Args:
            db: 数据库会话
            vector_client: 向量化客户端（UnifiedEmbeddingManager等）
            qdrant_client: Qdrant向量数据库客户端
        """
        self.db = db
        
        # 初始化向量化服务
        if VECTOR_SERVICES_AVAILABLE:
            try:
                self.embedding_manager = get_unified_embedding_manager()
                logger.info("已集成统一向量模型管理器")
            except Exception as e:
                logger.warning(f"向量模型管理器初始化失败: {e}，将使用模拟向量")
                self.embedding_manager = None
        else:
            self.embedding_manager = None
        
        # 使用传入的向量客户端或创建新的
        self.vector_client = vector_client or self.embedding_manager
        
        # 初始化Qdrant客户端
        if qdrant_client:
            self.qdrant_client = qdrant_client
        elif VECTOR_SERVICES_AVAILABLE:
            try:
                # 尝试创建Qdrant客户端
                import os
                self.qdrant_client = QdrantVectorStore(
                    host=os.getenv("QDRANT_HOST", "qdrant"),
                    port=int(os.getenv("QDRANT_PORT", "6333")),
                    collection_name="ea_vectors",
                    vector_size=384  # 默认维度
                )
                logger.info("已集成Qdrant向量数据库")
            except Exception as e:
                logger.warning(f"Qdrant客户端初始化失败: {e}，向量将存储在内存中")
                self.qdrant_client = None
        else:
            self.qdrant_client = None
        
        logger.info("EA向量化服务初始化完成")
    
    def vectorize_entity(self, entity: Dict[str, Any]) -> List[float]:
        """
        向量化EA实体
        
        Args:
            entity: EA实体字典，包含type, name, description等字段
            
        Returns:
            List[float]: 向量表示
        """
        # 构建实体文本描述
        text_parts = []
        
        # 添加名称
        if "name" in entity:
            text_parts.append(entity["name"])
        
        # 添加描述
        if "description" in entity:
            text_parts.append(entity["description"])
        
        # 添加类型信息
        if "type" in entity:
            text_parts.append(f"类型: {entity['type']}")
        
        # 添加业务域（如果有）
        if "business_domain" in entity:
            text_parts.append(f"业务域: {entity['business_domain']}")
        
        # 组合文本
        entity_text = " ".join(text_parts)
        
        # 使用真实的向量化服务
        if self.embedding_manager:
            try:
                # 使用统一向量模型管理器
                vectors = self.embedding_manager.encode([entity_text])
                if vectors and len(vectors) > 0:
                    return vectors[0]
            except Exception as e:
                logger.warning(f"向量化失败: {e}，使用模拟向量")
        
        # 降级：模拟向量
        import hashlib
        import random
        seed = int(hashlib.md5(entity_text.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        dimension = self.embedding_manager.dimension if self.embedding_manager else 384
        return [random.gauss(0, 0.1) for _ in range(dimension)]
    
    def vectorize_business_process(self, process: BusinessProcess) -> Dict[str, Any]:
        """
        向量化业务流程
        
        Args:
            process: BusinessProcess对象
            
        Returns:
            Dict: 包含向量和元数据的字典
        """
        entity_dict = {
            "id": process.id,
            "type": "BusinessProcess",
            "name": process.name,
            "description": process.description or "",
            "business_domain": getattr(process, "business_domain", None)
        }
        
        vector = self.vectorize_entity(entity_dict)
        
        return {
            "entity_id": process.id,
            "entity_type": "BusinessProcess",
            "vector": vector,
            "metadata": entity_dict
        }
    
    def vectorize_application_system(self, system: ApplicationSystem) -> Dict[str, Any]:
        """
        向量化应用系统
        
        Args:
            system: ApplicationSystem对象
            
        Returns:
            Dict: 包含向量和元数据的字典
        """
        entity_dict = {
            "id": system.id,
            "type": "ApplicationSystem",
            "name": system.name,
            "description": system.description or "",
            "system_type": getattr(system, "system_type", None)
        }
        
        vector = self.vectorize_entity(entity_dict)
        
        return {
            "entity_id": system.id,
            "entity_type": "ApplicationSystem",
            "vector": vector,
            "metadata": entity_dict
        }
    
    def vectorize_data_entity(self, entity: DataEntity) -> Dict[str, Any]:
        """
        向量化数据实体
        
        Args:
            entity: DataEntity对象
            
        Returns:
            Dict: 包含向量和元数据的字典
        """
        entity_dict = {
            "id": entity.id,
            "type": "DataEntity",
            "name": entity.name,
            "description": entity.description or "",
            "entity_type": getattr(entity, "entity_type", None)
        }
        
        vector = self.vectorize_entity(entity_dict)
        
        return {
            "entity_id": entity.id,
            "entity_type": "DataEntity",
            "vector": vector,
            "metadata": entity_dict
        }
    
    def batch_vectorize_processes(
        self,
        processes: Optional[List[BusinessProcess]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量向量化业务流程
        
        Args:
            processes: 业务流程列表，如果为None则从数据库加载所有
            
        Returns:
            List[Dict]: 向量化结果列表
        """
        if processes is None:
            processes = self.db.query(BusinessProcess).all()
        
        results = []
        for process in processes:
            try:
                result = self.vectorize_business_process(process)
                results.append(result)
            except Exception as e:
                logger.error(f"向量化业务流程失败: {process.id}, 错误: {e}")
        
        logger.info(f"批量向量化业务流程完成: {len(results)}/{len(processes)}")
        return results
    
    def batch_vectorize_systems(
        self,
        systems: Optional[List[ApplicationSystem]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量向量化应用系统
        
        Args:
            systems: 应用系统列表，如果为None则从数据库加载所有
            
        Returns:
            List[Dict]: 向量化结果列表
        """
        if systems is None:
            systems = self.db.query(ApplicationSystem).all()
        
        results = []
        for system in systems:
            try:
                result = self.vectorize_application_system(system)
                results.append(result)
            except Exception as e:
                logger.error(f"向量化应用系统失败: {system.id}, 错误: {e}")
        
        logger.info(f"批量向量化应用系统完成: {len(results)}/{len(systems)}")
        return results
    
    def batch_vectorize_data_entities(
        self,
        entities: Optional[List[DataEntity]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量向量化数据实体
        
        Args:
            entities: 数据实体列表，如果为None则从数据库加载所有
            
        Returns:
            List[Dict]: 向量化结果列表
        """
        if entities is None:
            entities = self.db.query(DataEntity).all()
        
        results = []
        for entity in entities:
            try:
                result = self.vectorize_data_entity(entity)
                results.append(result)
            except Exception as e:
                logger.error(f"向量化数据实体失败: {entity.id}, 错误: {e}")
        
        logger.info(f"批量向量化数据实体完成: {len(results)}/{len(entities)}")
        return results
    
    def semantic_search(
        self,
        query: str,
        entity_type: Optional[str] = None,  # "BusinessProcess" | "ApplicationSystem" | "DataEntity"
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        语义搜索EA实体
        
        Args:
            query: 查询文本
            entity_type: 可选的实体类型过滤
            top_k: 返回前k个结果
            
        Returns:
            List[Dict]: 搜索结果列表，每个结果包含entity_id, entity_type, score, metadata
        """
        # 向量化查询
        query_vector = self.vectorize_entity({"name": query, "description": query})
        
        # 在Qdrant向量数据库中搜索
        if self.qdrant_client and self.qdrant_client.client:
            try:
                # 构建过滤条件
                filter_conditions = None
                if entity_type:
                    from qdrant_client.models import Filter, FieldCondition, MatchValue
                    filter_conditions = Filter(
                        must=[
                            FieldCondition(
                                key="entity_type",
                                match=MatchValue(value=entity_type)
                            )
                        ]
                    )
                
                # 执行向量搜索
                search_results = self.qdrant_client.client.search(
                    collection_name="ea_vectors",
                    query_vector=query_vector,
                    query_filter=filter_conditions,
                    limit=top_k
                )
                
                # 转换为结果格式
                results = []
                for result in search_results:
                    results.append({
                        "entity_id": result.payload.get("entity_id"),
                        "entity_type": result.payload.get("entity_type"),
                        "score": result.score,
                        "metadata": result.payload.get("metadata", {})
                    })
                
                return results
            except Exception as e:
                logger.error(f"Qdrant搜索失败: {e}")
                return []
        else:
            # 降级：从数据库查询（简化实现）
            logger.warning("Qdrant客户端未配置，使用数据库查询（性能较低）")
            # TODO: 实现基于数据库的向量搜索
            return []

