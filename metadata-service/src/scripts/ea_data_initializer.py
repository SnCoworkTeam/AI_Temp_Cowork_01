"""
EA数据初始化脚本
从现有EA数据加载到图谱和向量库
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models.enterprise_architecture_models import (
    BusinessProcess, ApplicationSystem, DataEntity, ArchitectureRelationship
)
from metadata_service.src.services.ea_vectorization_service import EAVectorizationService
from metadata_service.src.services.ea_knowledge_graph import EAKnowledgeGraph
from metadata_service.src.services.ea_hybrid_query import EAHybridQuery

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EADataInitializer:
    """EA数据初始化器"""
    
    def __init__(self):
        """初始化"""
        # 初始化数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("数据库连接失败")
        
        init_session_factory()
        self.db = next(get_db())
        
        # 初始化EA服务
        self.vector_service = EAVectorizationService(self.db)
        self.graph_service = EAKnowledgeGraph(self.db)
        self.hybrid_query = EAHybridQuery(self.db, self.graph_service, self.vector_service)
    
    async def initialize_all(self) -> Dict[str, Any]:
        """
        初始化所有EA数据
        
        Returns:
            Dict: 初始化统计信息
        """
        stats = {
            "processes": {"total": 0, "vectorized": 0, "graphed": 0},
            "systems": {"total": 0, "vectorized": 0, "graphed": 0},
            "entities": {"total": 0, "vectorized": 0, "graphed": 0},
            "relationships": {"total": 0, "graphed": 0}
        }
        
        try:
            # 1. 向量化业务流程
            logger.info("开始向量化业务流程...")
            processes = self.db.query(BusinessProcess).all()
            stats["processes"]["total"] = len(processes)
            
            vectorized_processes = self.vector_service.batch_vectorize_processes(processes)
            stats["processes"]["vectorized"] = len(vectorized_processes)
            
            # 存储到Qdrant（如果有）
            if self.vector_service.qdrant_client and self.vector_service.qdrant_client.client:
                await self._store_vectors_to_qdrant(vectorized_processes, "BusinessProcess")
            
            # 2. 向量化应用系统
            logger.info("开始向量化应用系统...")
            systems = self.db.query(ApplicationSystem).all()
            stats["systems"]["total"] = len(systems)
            
            vectorized_systems = self.vector_service.batch_vectorize_systems(systems)
            stats["systems"]["vectorized"] = len(vectorized_systems)
            
            if self.vector_service.qdrant_client and self.vector_service.qdrant_client.client:
                await self._store_vectors_to_qdrant(vectorized_systems, "ApplicationSystem")
            
            # 3. 向量化数据实体
            logger.info("开始向量化数据实体...")
            entities = self.db.query(DataEntity).all()
            stats["entities"]["total"] = len(entities)
            
            vectorized_entities = self.vector_service.batch_vectorize_data_entities(entities)
            stats["entities"]["vectorized"] = len(vectorized_entities)
            
            if self.vector_service.qdrant_client and self.vector_service.qdrant_client.client:
                await self._store_vectors_to_qdrant(vectorized_entities, "DataEntity")
            
            # 4. 加载关系到图谱
            logger.info("开始加载关系到图谱...")
            relationships = self.db.query(ArchitectureRelationship).all()
            stats["relationships"]["total"] = len(relationships)
            
            # 确保Neo4j连接
            if self.graph_service.use_neo4j and self.graph_service.neo4j_client:
                if not self.graph_service.neo4j_client.driver:
                    await self.graph_service.neo4j_client.connect()
            
            # 先创建所有实体节点
            for process in processes:
                await self.graph_service.create_entity(
                    entity_type="BusinessProcess",
                    entity_id=process.id,
                    properties={
                        "name": process.name,
                        "description": process.description or "",
                        "business_domain": getattr(process, "business_domain", None)
                    }
                )
                stats["processes"]["graphed"] += 1
            
            for system in systems:
                await self.graph_service.create_entity(
                    entity_type="ApplicationSystem",
                    entity_id=system.id,
                    properties={
                        "name": system.name,
                        "description": system.description or "",
                        "system_type": getattr(system, "system_type", None)
                    }
                )
                stats["systems"]["graphed"] += 1
            
            for entity in entities:
                await self.graph_service.create_entity(
                    entity_type="DataEntity",
                    entity_id=entity.id,
                    properties={
                        "name": entity.name,
                        "description": entity.description or "",
                        "entity_type": getattr(entity, "entity_type", None)
                    }
                )
                stats["entities"]["graphed"] += 1
            
            # 创建关系
            for rel in relationships:
                success = await self.graph_service.create_relationship(
                    from_entity_id=rel.from_entity_id,
                    to_entity_id=rel.to_entity_id,
                    relation_type=rel.relationship_type,
                    properties={}
                )
                if success:
                    stats["relationships"]["graphed"] += 1
            
            logger.info("EA数据初始化完成")
            return stats
            
        except Exception as e:
            logger.error(f"EA数据初始化失败: {e}", exc_info=True)
            raise
        finally:
            self.db.close()
    
    async def _store_vectors_to_qdrant(
        self,
        vectorized_items: List[Dict[str, Any]],
        entity_type: str
    ):
        """存储向量到Qdrant"""
        if not self.vector_service.qdrant_client or not self.vector_service.qdrant_client.client:
            return
        
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for item in vectorized_items:
                points.append(PointStruct(
                    id=hash(item["entity_id"]) % (2**63),  # Qdrant需要整数ID
                    vector=item["vector"],
                    payload={
                        "entity_id": item["entity_id"],
                        "entity_type": entity_type,
                        "metadata": item["metadata"]
                    }
                ))
            
            # 批量上传
            self.vector_service.qdrant_client.client.upsert(
                collection_name="ea_vectors",
                points=points
            )
            
            logger.info(f"已存储 {len(points)} 个 {entity_type} 向量到Qdrant")
        except Exception as e:
            logger.error(f"存储向量到Qdrant失败: {e}")


async def main():
    """主函数"""
    print("=" * 60)
    print("EA数据初始化")
    print("=" * 60)
    print()
    
    try:
        initializer = EADataInitializer()
        stats = await initializer.initialize_all()
        
        print("\n初始化统计:")
        print(f"  业务流程: {stats['processes']['vectorized']}/{stats['processes']['total']} 向量化, {stats['processes']['graphed']} 加载到图谱")
        print(f"  应用系统: {stats['systems']['vectorized']}/{stats['systems']['total']} 向量化, {stats['systems']['graphed']} 加载到图谱")
        print(f"  数据实体: {stats['entities']['vectorized']}/{stats['entities']['total']} 向量化, {stats['entities']['graphed']} 加载到图谱")
        print(f"  关系: {stats['relationships']['graphed']}/{stats['relationships']['total']} 加载到图谱")
        
        print("\n" + "=" * 60)
        print("[OK] EA数据初始化完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))

