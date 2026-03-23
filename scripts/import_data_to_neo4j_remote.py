"""
数据导入脚本：从本地PostgreSQL导入数据到远程Neo4j服务器
使用方法: python scripts/import_data_to_neo4j_remote.py
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.database import get_database_manager
from database.src.core.session import get_db, init_session_factory
from database.src.core.neo4j_client import Neo4jClient, Neo4jSettings
from database.src.models import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    BusinessProcess,
    ApplicationSystem,
    DataEntity,
    TechnologyComponent,
    ArchitectureRelationship
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RemoteNeo4jDataImporter:
    """远程Neo4j数据导入器"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str = "neo4j", neo4j_password: str = "Neo4j@2024"):
        """
        初始化导入器
        
        Args:
            neo4j_uri: Neo4j连接URI，例如 bolt://43.143.90.179:7687
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
        """
        # 配置远程Neo4j连接
        settings = Neo4jSettings(
            NEO4J_URI=neo4j_uri,
            NEO4J_USER=neo4j_user,
            NEO4J_PASSWORD=neo4j_password
        )
        self.neo4j_client = Neo4jClient(settings)
        self.db = None
        self.stats = {
            "knowledge_graph_nodes": 0,
            "knowledge_graph_edges": 0,
            "architecture_relationships": 0,
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
        
        # 连接远程Neo4j
        if not await self.neo4j_client.connect():
            raise RuntimeError("Neo4j连接失败，请检查服务器地址和端口")
        
        logger.info("数据库连接初始化成功")
    
    async def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()
        await self.neo4j_client.disconnect()
        logger.info("资源清理完成")
    
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
                logger.info(f"✅ 创建索引: {index_query.split('FOR')[1].split('ON')[0].strip()}")
            except Exception as e:
                logger.warning(f"⚠️  创建索引失败: {e}")
    
    async def import_knowledge_graph(self, batch_size: int = 100):
        """导入知识图谱数据"""
        logger.info("开始导入知识图谱数据...")
        
        try:
            # 1. 导入节点
            nodes = self.db.query(KnowledgeGraphNode).all()
            logger.info(f"找到 {len(nodes)} 个知识图谱节点")
            
            node_id_mapping: Dict[str, str] = {}
            
            for i, node in enumerate(nodes, 1):
                try:
                    properties = {
                        "uuid": str(node.id),
                        "label": node.label,
                        "node_type": node.node_type or "Entity",
                        **(node.properties or {})
                    }
                    
                    if node.document_id:
                        properties["document_id"] = str(node.document_id)
                    
                    labels = [node.node_type] if node.node_type else ["Entity"]
                    neo4j_node_id = await self.neo4j_client.create_node(labels, properties)
                    node_id_mapping[str(node.id)] = neo4j_node_id
                    
                    self.stats["knowledge_graph_nodes"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已导入 {i}/{len(nodes)} 个节点")
                
                except Exception as e:
                    logger.error(f"导入节点失败 {node.id}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"✅ 节点导入完成: {self.stats['knowledge_graph_nodes']} 个")
            
            # 2. 导入边
            edges = self.db.query(KnowledgeGraphEdge).all()
            logger.info(f"找到 {len(edges)} 个知识图谱边")
            
            for i, edge in enumerate(edges, 1):
                try:
                    source_neo4j_id = node_id_mapping.get(str(edge.source_node_id))
                    target_neo4j_id = node_id_mapping.get(str(edge.target_node_id))
                    
                    if not source_neo4j_id or not target_neo4j_id:
                        logger.warning(f"边 {edge.id} 的节点未找到，跳过")
                        continue
                    
                    properties = {
                        "uuid": str(edge.id),
                        "weight": edge.weight or 1.0,
                        **(edge.edge_metadata or {})
                    }
                    
                    await self.neo4j_client.create_relationship(
                        source_neo4j_id,
                        target_neo4j_id,
                        edge.relationship_type,
                        properties
                    )
                    
                    self.stats["knowledge_graph_edges"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已导入 {i}/{len(edges)} 个边")
                
                except Exception as e:
                    logger.error(f"导入边失败 {edge.id}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"✅ 边导入完成: {self.stats['knowledge_graph_edges']} 个")
        
        except Exception as e:
            logger.error(f"导入知识图谱数据失败: {e}", exc_info=True)
            raise
    
    async def import_architecture_relationships(self, batch_size: int = 100):
        """导入企业架构关系"""
        logger.info("开始导入企业架构关系...")
        
        try:
            relationships = self.db.query(ArchitectureRelationship).all()
            logger.info(f"找到 {len(relationships)} 个架构关系")
            
            entity_nodes = {}
            
            # 创建业务流程节点
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
                        **(process.meta_data or {})
                    }
                    neo4j_id = await self.neo4j_client.create_node(["BusinessProcess"], properties)
                    entity_nodes[f"BusinessProcess:{process.id}"] = neo4j_id
                    process.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"BusinessProcess:{process.id}"] = process.neo4j_node_id
            
            # 创建应用系统节点
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
                        **(system.meta_data or {})
                    }
                    neo4j_id = await self.neo4j_client.create_node(["ApplicationSystem"], properties)
                    entity_nodes[f"ApplicationSystem:{system.id}"] = neo4j_id
                    system.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"ApplicationSystem:{system.id}"] = system.neo4j_node_id
            
            # 创建数据实体节点
            data_entities = self.db.query(DataEntity).all()
            for entity in data_entities:
                if not entity.neo4j_node_id:
                    properties = {
                        "uuid": str(entity.id),
                        "name": entity.name,
                        "description": entity.description or "",
                        "entity_type": entity.entity_type or "",
                        "schema": str(entity.schema) if entity.schema else "",
                        **(entity.meta_data or {})
                    }
                    neo4j_id = await self.neo4j_client.create_node(["DataEntity"], properties)
                    entity_nodes[f"DataEntity:{entity.id}"] = neo4j_id
                    entity.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"DataEntity:{entity.id}"] = entity.neo4j_node_id
            
            # 创建技术组件节点
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
                        **(component.meta_data or {})
                    }
                    neo4j_id = await self.neo4j_client.create_node(["TechnologyComponent"], properties)
                    entity_nodes[f"TechnologyComponent:{component.id}"] = neo4j_id
                    component.neo4j_node_id = neo4j_id
                    self.db.commit()
                else:
                    entity_nodes[f"TechnologyComponent:{component.id}"] = component.neo4j_node_id
            
            # 导入关系
            for i, rel in enumerate(relationships, 1):
                try:
                    source_key = f"{rel.source_type}:{rel.source_id}"
                    target_key = f"{rel.target_type}:{rel.target_id}"
                    
                    source_neo4j_id = entity_nodes.get(source_key)
                    target_neo4j_id = entity_nodes.get(target_key)
                    
                    if not source_neo4j_id or not target_neo4j_id:
                        logger.warning(f"关系 {rel.id} 的节点未找到，跳过")
                        continue
                    
                    properties = {
                        "uuid": str(rel.id),
                        "description": rel.description or "",
                        **(rel.properties or {})
                    }
                    
                    await self.neo4j_client.create_relationship(
                        source_neo4j_id,
                        target_neo4j_id,
                        rel.relationship_type,
                        properties
                    )
                    
                    self.stats["architecture_relationships"] += 1
                    
                    if i % batch_size == 0:
                        logger.info(f"已导入 {i}/{len(relationships)} 个架构关系")
                
                except Exception as e:
                    logger.error(f"导入架构关系失败 {rel.id}: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"✅ 架构关系导入完成: {self.stats['architecture_relationships']} 个")
        
        except Exception as e:
            logger.error(f"导入企业架构关系失败: {e}", exc_info=True)
            raise
    
    async def run_import(self):
        """运行完整导入"""
        logger.info("=" * 80)
        logger.info("开始数据导入到远程Neo4j")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            await self.initialize()
            
            # 创建索引
            await self.create_indexes()
            
            # 导入数据
            await self.import_knowledge_graph()
            await self.import_architecture_relationships()
            
            # 打印统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("导入完成")
            logger.info("=" * 80)
            logger.info(f"导入统计:")
            logger.info(f"  知识图谱节点: {self.stats['knowledge_graph_nodes']}")
            logger.info(f"  知识图谱边: {self.stats['knowledge_graph_edges']}")
            logger.info(f"  架构关系: {self.stats['architecture_relationships']}")
            logger.info(f"  错误数: {self.stats['errors']}")
            logger.info(f"  耗时: {duration:.2f} 秒")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"导入失败: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导入数据到远程Neo4j')
    parser.add_argument('--neo4j-uri', default='bolt://43.143.90.179:7687', help='Neo4j连接URI')
    parser.add_argument('--neo4j-user', default='neo4j', help='Neo4j用户名')
    parser.add_argument('--neo4j-password', default='Neo4j@2024', help='Neo4j密码')
    
    args = parser.parse_args()
    
    importer = RemoteNeo4jDataImporter(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password
    )
    await importer.run_import()


if __name__ == "__main__":
    asyncio.run(main())



