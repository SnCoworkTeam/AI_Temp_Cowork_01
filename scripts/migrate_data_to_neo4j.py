"""
数据迁移脚本：从PostgreSQL迁移数据到Neo4j
迁移内容：
1. 知识图谱节点和边
2. 企业架构关系
3. 数据血缘关系
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.database import get_database_manager
from database.src.core.session import get_db, init_session_factory
from database.src.core.neo4j_client import Neo4jClient, get_neo4j_settings
from database.src.models import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    BusinessProcess,
    ApplicationSystem,
    DataEntity,
    TechnologyComponent,
    ArchitectureRelationship
)

# LineageEdge可能在不同的位置，尝试导入
try:
    from database.src.models.metadata_models import LineageEdge
except ImportError:
    try:
        from metadata_service.src.models.lineage import LineageEdge
    except ImportError:
        # 如果找不到，使用None，稍后处理
        LineageEdge = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        """初始化迁移器"""
        self.neo4j_client = Neo4jClient()
        self.db = None
        self.stats = {
            "knowledge_graph_nodes": 0,
            "knowledge_graph_edges": 0,
            "architecture_relationships": 0,
            "lineage_edges": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """初始化连接"""
        # 初始化PostgreSQL
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("PostgreSQL连接失败")
        init_session_factory()
        self.db = next(get_db())
        
        # 连接Neo4j
        if not await self.neo4j_client.connect():
            raise RuntimeError("Neo4j连接失败")
        
        logger.info("数据库连接初始化成功")
    
    async def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()
        await self.neo4j_client.disconnect()
        logger.info("资源清理完成")
    
    async def migrate_knowledge_graph(self, batch_size: int = 100):
        """
        迁移知识图谱数据
        
        Args:
            batch_size: 批处理大小
        """
        logger.info("开始迁移知识图谱数据...")
        
        try:
            # 1. 迁移节点
            nodes = self.db.query(KnowledgeGraphNode).all()
            logger.info(f"找到 {len(nodes)} 个知识图谱节点")
            
            node_id_mapping: Dict[str, str] = {}  # PostgreSQL UUID -> Neo4j node_id
            
            for i, node in enumerate(nodes, 1):
                try:
                    # 构建节点属性
                    properties = {
                        "uuid": str(node.id),
                        "label": node.label,
                        "node_type": node.node_type or "Entity",
                        **node.properties
                    }
                    
                    if node.document_id:
                        properties["document_id"] = str(node.document_id)
                    
                    # 创建Neo4j节点
                    labels = [node.node_type] if node.node_type else ["Entity"]
                    neo4j_node_id = await self.neo4j_client.create_node(labels, properties)
                    node_id_mapping[str(node.id)] = neo4j_node_id
                    
                    self.stats["knowledge_graph_nodes"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已迁移 {i}/{len(nodes)} 个节点")
                
                except Exception as e:
                    logger.error(f"迁移节点失败 {node.id}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"节点迁移完成: {self.stats['knowledge_graph_nodes']} 个")
            
            # 2. 迁移边
            edges = self.db.query(KnowledgeGraphEdge).all()
            logger.info(f"找到 {len(edges)} 个知识图谱边")
            
            for i, edge in enumerate(edges, 1):
                try:
                    source_neo4j_id = node_id_mapping.get(str(edge.source_node_id))
                    target_neo4j_id = node_id_mapping.get(str(edge.target_node_id))
                    
                    if not source_neo4j_id or not target_neo4j_id:
                        logger.warning(f"边 {edge.id} 的节点未找到，跳过")
                        continue
                    
                    # 构建关系属性
                    properties = {
                        "uuid": str(edge.id),
                        "weight": edge.weight or 1.0,
                        **edge.edge_metadata
                    }
                    
                    # 创建Neo4j关系
                    await self.neo4j_client.create_relationship(
                        source_neo4j_id,
                        target_neo4j_id,
                        edge.relationship_type,
                        properties
                    )
                    
                    self.stats["knowledge_graph_edges"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已迁移 {i}/{len(edges)} 个边")
                
                except Exception as e:
                    logger.error(f"迁移边失败 {edge.id}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"边迁移完成: {self.stats['knowledge_graph_edges']} 个")
        
        except Exception as e:
            logger.error(f"迁移知识图谱数据失败: {e}", exc_info=True)
            raise
    
    async def migrate_architecture_relationships(self, batch_size: int = 100):
        """
        迁移企业架构关系
        
        Args:
            batch_size: 批处理大小
        """
        logger.info("开始迁移企业架构关系...")
        
        try:
            relationships = self.db.query(ArchitectureRelationship).all()
            logger.info(f"找到 {len(relationships)} 个架构关系")
            
            # 首先创建所有架构实体节点
            entity_nodes = {}
            
            # 业务流程节点
            processes = self.db.query(BusinessProcess).all()
            for process in processes:
                if not process.neo4j_node_id:
                    properties = {
                        "uuid": str(process.id),
                        "name": process.name,
                        "description": process.description or "",
                        "owner": process.owner or "",
                        "status": process.status or "active",
                        "classification": process.classification or "",
                        **process.meta_data
                    }
                    neo4j_id = await self.neo4j_client.create_node(["BusinessProcess"], properties)
                    entity_nodes[f"BusinessProcess:{process.id}"] = neo4j_id
                    # 更新PostgreSQL中的neo4j_node_id
                    process.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"BusinessProcess:{process.id}"] = process.neo4j_node_id
            
            # 应用系统节点
            systems = self.db.query(ApplicationSystem).all()
            for system in systems:
                if not system.neo4j_node_id:
                    properties = {
                        "uuid": str(system.id),
                        "name": system.name,
                        "description": system.description or "",
                        "system_type": system.system_type or "",
                        "vendor": system.vendor or "",
                        "version": system.version or "",
                        "status": system.status or "active",
                        **system.meta_data
                    }
                    neo4j_id = await self.neo4j_client.create_node(["ApplicationSystem"], properties)
                    entity_nodes[f"ApplicationSystem:{system.id}"] = neo4j_id
                    system.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"ApplicationSystem:{system.id}"] = system.neo4j_node_id
            
            # 数据实体节点
            data_entities = self.db.query(DataEntity).all()
            for entity in data_entities:
                if not entity.neo4j_node_id:
                    properties = {
                        "uuid": str(entity.id),
                        "name": entity.name,
                        "description": entity.description or "",
                        "entity_type": entity.entity_type or "",
                        "schema": str(entity.schema) if entity.schema else "",
                        **entity.meta_data
                    }
                    neo4j_id = await self.neo4j_client.create_node(["DataEntity"], properties)
                    entity_nodes[f"DataEntity:{entity.id}"] = neo4j_id
                    entity.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"DataEntity:{entity.id}"] = entity.neo4j_node_id
            
            # 技术组件节点
            components = self.db.query(TechnologyComponent).all()
            for component in components:
                if not component.neo4j_node_id:
                    properties = {
                        "uuid": str(component.id),
                        "name": component.name,
                        "description": component.description or "",
                        "component_type": component.component_type or "",
                        "version": getattr(component, 'version', None) or "",
                        "vendor": getattr(component, 'vendor', None) or "",
                        **component.meta_data
                    }
                    neo4j_id = await self.neo4j_client.create_node(["TechnologyComponent"], properties)
                    entity_nodes[f"TechnologyComponent:{component.id}"] = neo4j_id
                    component.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"TechnologyComponent:{component.id}"] = component.neo4j_node_id
            
            # 迁移关系
            for i, rel in enumerate(relationships, 1):
                try:
                    source_key = f"{rel.source_type}:{rel.source_id}"
                    target_key = f"{rel.target_type}:{rel.target_id}"
                    
                    source_neo4j_id = entity_nodes.get(source_key)
                    target_neo4j_id = entity_nodes.get(target_key)
                    
                    if not source_neo4j_id or not target_neo4j_id:
                        # 如果节点未找到，尝试通过UUID在Neo4j中查找
                        logger.warning(f"关系 {rel.id} 的节点未在entity_nodes中找到，尝试在Neo4j中查找...")
                        
                        # 尝试通过UUID查找源节点
                        # 标签名称映射：PostgreSQL中的类型名 -> Neo4j中的标签名
                        label_map = {
                            "business_process": "BusinessProcess",
                            "application_system": "ApplicationSystem",
                            "data_entity": "DataEntity",
                            "technology_component": "TechnologyComponent",
                            "business_capability": "BusinessCapability",
                            "application_service": "ApplicationService",
                            "data_model": "DataModel",
                            "technology_stack": "TechnologyStack"
                        }
                        
                        source_label = label_map.get(rel.source_type, rel.source_type.capitalize())
                        target_label = label_map.get(rel.target_type, rel.target_type.capitalize())
                        
                        if not source_neo4j_id:
                            source_query = f"""
                            MATCH (n:{source_label})
                            WHERE n.uuid = $uuid
                            RETURN id(n) AS node_id
                            LIMIT 1
                            """
                            source_results = await self.neo4j_client.execute_query(
                                source_query, 
                                {"uuid": str(rel.source_id)}
                            )
                            if source_results:
                                source_neo4j_id = str(source_results[0]["node_id"])
                                entity_nodes[source_key] = source_neo4j_id
                                logger.info(f"通过UUID找到源节点: {rel.source_type}:{rel.source_id} -> Neo4j ID: {source_neo4j_id}")
                        
                        # 尝试通过UUID查找目标节点
                        if not target_neo4j_id:
                            target_query = f"""
                            MATCH (n:{target_label})
                            WHERE n.uuid = $uuid
                            RETURN id(n) AS node_id
                            LIMIT 1
                            """
                            target_results = await self.neo4j_client.execute_query(
                                target_query,
                                {"uuid": str(rel.target_id)}
                            )
                            if target_results:
                                target_neo4j_id = str(target_results[0]["node_id"])
                                entity_nodes[target_key] = target_neo4j_id
                                logger.info(f"通过UUID找到目标节点: {rel.target_type}:{rel.target_id} -> Neo4j ID: {target_neo4j_id}")
                        
                        # 如果还是找不到，跳过
                        if not source_neo4j_id or not target_neo4j_id:
                            logger.warning(f"关系 {rel.id} 的节点在Neo4j中也未找到，跳过 (source={rel.source_type}:{rel.source_id}, target={rel.target_type}:{rel.target_id})")
                            continue
                    
                    properties = {
                        "uuid": str(rel.id),
                        "description": rel.description or "",
                        **rel.properties
                    }
                    
                    await self.neo4j_client.create_relationship(
                        source_neo4j_id,
                        target_neo4j_id,
                        rel.relationship_type,
                        properties
                    )
                    
                    self.stats["architecture_relationships"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已迁移 {i}/{len(relationships)} 个架构关系")
                
                except Exception as e:
                    logger.error(f"迁移架构关系失败 {rel.id}: {e}", exc_info=True)
                    self.stats["errors"] += 1
            
            logger.info(f"架构关系迁移完成: {self.stats['architecture_relationships']} 个")
        
        except Exception as e:
            logger.error(f"迁移企业架构关系失败: {e}", exc_info=True)
            raise
    
    async def migrate_lineage_edges(self, batch_size: int = 100):
        """
        迁移数据血缘关系
        
        Args:
            batch_size: 批处理大小
        """
        logger.info("开始迁移数据血缘关系...")
        
        try:
            edges = self.db.query(LineageEdge).all()
            logger.info(f"找到 {len(edges)} 个数据血缘边")
            
            # 这里需要根据实际的数据血缘模型调整
            # 假设LineageEdge有source_asset_id和target_asset_id
            for i, edge in enumerate(edges, 1):
                try:
                    # 需要根据实际模型调整
                    # 这里只是示例
                    logger.warning(f"数据血缘迁移需要根据实际模型实现")
                    break
                
                except Exception as e:
                    logger.error(f"迁移数据血缘失败 {edge.id if hasattr(edge, 'id') else 'unknown'}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"数据血缘迁移完成: {self.stats['lineage_edges']} 个")
        
        except Exception as e:
            logger.error(f"迁移数据血缘关系失败: {e}", exc_info=True)
            raise
    
    async def create_indexes(self):
        """创建Neo4j索引"""
        logger.info("创建Neo4j索引...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.uuid)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.label)",
            "CREATE INDEX IF NOT EXISTS FOR (n:BusinessProcess) ON (n.uuid)",
            "CREATE INDEX IF NOT EXISTS FOR (n:BusinessProcess) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:ApplicationSystem) ON (n.uuid)",
            "CREATE INDEX IF NOT EXISTS FOR (n:ApplicationSystem) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:DataEntity) ON (n.uuid)",
            "CREATE INDEX IF NOT EXISTS FOR (n:DataEntity) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.uuid)",
            "CREATE INDEX IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.name)",
        ]
        
        for index_query in indexes:
            try:
                await self.neo4j_client.execute_write(index_query)
                logger.info(f"创建索引: {index_query}")
            except Exception as e:
                logger.warning(f"创建索引失败: {index_query} - {e}")
    
    async def run_migration(self):
        """运行完整迁移"""
        logger.info("=" * 80)
        logger.info("开始数据迁移到Neo4j")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            await self.initialize()
            
            # 创建索引
            await self.create_indexes()
            
            # 迁移数据
            await self.migrate_knowledge_graph()
            await self.migrate_architecture_relationships()
            # await self.migrate_lineage_edges()  # 需要根据实际模型实现
            
            # 打印统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("迁移完成")
            logger.info("=" * 80)
            logger.info(f"迁移统计:")
            logger.info(f"  知识图谱节点: {self.stats['knowledge_graph_nodes']}")
            logger.info(f"  知识图谱边: {self.stats['knowledge_graph_edges']}")
            logger.info(f"  架构关系: {self.stats['architecture_relationships']}")
            logger.info(f"  数据血缘: {self.stats['lineage_edges']}")
            logger.info(f"  错误数: {self.stats['errors']}")
            logger.info(f"  耗时: {duration:.2f} 秒")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"迁移失败: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()


async def main():
    """主函数"""
    migrator = DataMigrator()
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())

