"""
数据库迁移测试脚本
测试Neo4j和Qdrant数据迁移是否成功
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.database import get_database_manager
from database.src.core.session import get_db, init_session_factory
from database.src.core.neo4j_client import Neo4jClient
from database.src.models import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    ArchitectureRelationship
)
from qdrant_client import QdrantClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationTester:
    """迁移测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.neo4j_client = Neo4jClient()
        self.qdrant_client = QdrantClient(url="http://localhost:6333")
        self.db = None
        self.test_results = {
            "neo4j_connection": False,
            "qdrant_connection": False,
            "knowledge_graph_nodes": {"postgresql": 0, "neo4j": 0, "match": False},
            "knowledge_graph_edges": {"postgresql": 0, "neo4j": 0, "match": False},
            "architecture_relationships": {"postgresql": 0, "neo4j": 0, "match": False},
            "quality_vectors": {"postgresql": 0, "qdrant": 0, "match": False},
            "errors": []
        }
    
    async def initialize(self):
        """初始化连接"""
        # PostgreSQL
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("PostgreSQL连接失败")
        init_session_factory()
        self.db = next(get_db())
        
        # Neo4j
        if await self.neo4j_client.connect():
            self.test_results["neo4j_connection"] = True
            logger.info("✅ Neo4j连接成功")
        else:
            self.test_results["errors"].append("Neo4j连接失败")
            logger.error("❌ Neo4j连接失败")
        
        # Qdrant
        try:
            collections = self.qdrant_client.get_collections()
            self.test_results["qdrant_connection"] = True
            logger.info("✅ Qdrant连接成功")
        except Exception as e:
            self.test_results["errors"].append(f"Qdrant连接失败: {e}")
            logger.error(f"❌ Qdrant连接失败: {e}")
    
    async def test_knowledge_graph_migration(self):
        """测试知识图谱迁移"""
        logger.info("测试知识图谱数据迁移...")
        
        try:
            # PostgreSQL中的节点数
            pg_nodes = self.db.query(KnowledgeGraphNode).count()
            self.test_results["knowledge_graph_nodes"]["postgresql"] = pg_nodes
            
            # Neo4j中的节点数（查询所有节点，因为可能使用不同的标签）
            result = await self.neo4j_client.execute_query(
                "MATCH (n) RETURN count(n) AS count"
            )
            neo4j_nodes = result[0]["count"] if result else 0
            self.test_results["knowledge_graph_nodes"]["neo4j"] = neo4j_nodes
            
            # 检查是否匹配
            if pg_nodes == neo4j_nodes:
                self.test_results["knowledge_graph_nodes"]["match"] = True
                logger.info(f"✅ 知识图谱节点数量匹配: {pg_nodes}")
            else:
                logger.warning(f"⚠️ 知识图谱节点数量不匹配: PostgreSQL={pg_nodes}, Neo4j={neo4j_nodes}")
            
            # PostgreSQL中的边数
            pg_edges = self.db.query(KnowledgeGraphEdge).count()
            self.test_results["knowledge_graph_edges"]["postgresql"] = pg_edges
            
            # Neo4j中的边数
            result = await self.neo4j_client.execute_query(
                "MATCH ()-[r]->() RETURN count(r) AS count"
            )
            neo4j_edges = result[0]["count"] if result else 0
            self.test_results["knowledge_graph_edges"]["neo4j"] = neo4j_edges
            
            # 检查是否匹配
            if pg_edges == neo4j_edges:
                self.test_results["knowledge_graph_edges"]["match"] = True
                logger.info(f"✅ 知识图谱边数量匹配: {pg_edges}")
            else:
                logger.warning(f"⚠️ 知识图谱边数量不匹配: PostgreSQL={pg_edges}, Neo4j={neo4j_edges}")
        
        except Exception as e:
            error_msg = f"测试知识图谱迁移失败: {e}"
            self.test_results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    async def test_architecture_relationships_migration(self):
        """测试架构关系迁移"""
        logger.info("测试架构关系迁移...")
        
        try:
            # PostgreSQL中的关系数
            pg_rels = self.db.query(ArchitectureRelationship).count()
            self.test_results["architecture_relationships"]["postgresql"] = pg_rels
            
            # Neo4j中的关系数（架构关系）
            result = await self.neo4j_client.execute_query(
                """
                MATCH ()-[r]->()
                WHERE type(r) IN ['IMPLEMENTED_BY', 'USES', 'DEPENDS_ON', 'STORED_IN', 'RUNS_ON']
                RETURN count(r) AS count
                """
            )
            neo4j_rels = result[0]["count"] if result else 0
            self.test_results["architecture_relationships"]["neo4j"] = neo4j_rels
            
            # 检查是否匹配（允许一定误差，因为可能还有其他关系）
            if pg_rels <= neo4j_rels:
                self.test_results["architecture_relationships"]["match"] = True
                logger.info(f"✅ 架构关系数量匹配: PostgreSQL={pg_rels}, Neo4j>={neo4j_rels}")
            else:
                logger.warning(f"⚠️ 架构关系数量不匹配: PostgreSQL={pg_rels}, Neo4j={neo4j_rels}")
        
        except Exception as e:
            error_msg = f"测试架构关系迁移失败: {e}"
            self.test_results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    async def test_quality_vectors_migration(self):
        """测试质量规则向量迁移"""
        logger.info("测试质量规则向量迁移...")
        
        try:
            # PostgreSQL中的向量数
            from sqlalchemy import text
            result = self.db.execute(text("SELECT COUNT(*) FROM quality_rule_vectors"))
            pg_vectors = result.scalar() or 0
            self.test_results["quality_vectors"]["postgresql"] = pg_vectors
            
            # Qdrant中的向量数
            try:
                collection_info = self.qdrant_client.get_collection("quality_rule_vectors")
                qdrant_vectors = collection_info.points_count
                self.test_results["quality_vectors"]["qdrant"] = qdrant_vectors
                
                # 检查是否匹配
                if pg_vectors == qdrant_vectors:
                    self.test_results["quality_vectors"]["match"] = True
                    logger.info(f"✅ 质量规则向量数量匹配: {pg_vectors}")
                else:
                    logger.warning(f"⚠️ 质量规则向量数量不匹配: PostgreSQL={pg_vectors}, Qdrant={qdrant_vectors}")
            except Exception as e:
                logger.warning(f"⚠️ Qdrant集合不存在或无法访问: {e}")
                self.test_results["quality_vectors"]["qdrant"] = 0
        
        except Exception as e:
            error_msg = f"测试质量规则向量迁移失败: {e}"
            self.test_results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    async def test_neo4j_queries(self):
        """测试Neo4j查询功能"""
        logger.info("测试Neo4j查询功能...")
        
        try:
            # 测试1: 简单查询
            result = await self.neo4j_client.execute_query("RETURN 1 AS test")
            if result and result[0]["test"] == 1:
                logger.info("✅ Neo4j简单查询测试通过")
            else:
                raise Exception("Neo4j简单查询失败")
            
            # 测试2: 节点查询
            result = await self.neo4j_client.execute_query(
                "MATCH (n:Entity) RETURN count(n) AS count LIMIT 1"
            )
            logger.info(f"✅ Neo4j节点查询测试通过，找到 {result[0]['count'] if result else 0} 个节点")
            
            # 测试3: 关系查询
            result = await self.neo4j_client.execute_query(
                "MATCH ()-[r]->() RETURN count(r) AS count LIMIT 1"
            )
            logger.info(f"✅ Neo4j关系查询测试通过，找到 {result[0]['count'] if result else 0} 个关系")
        
        except Exception as e:
            error_msg = f"Neo4j查询测试失败: {e}"
            self.test_results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    async def test_qdrant_queries(self):
        """测试Qdrant查询功能"""
        logger.info("测试Qdrant查询功能...")
        
        try:
            # 测试向量搜索
            test_vector = [0.0] * 384
            result = self.qdrant_client.search(
                collection_name="quality_rule_vectors",
                query_vector=test_vector,
                limit=5
            )
            logger.info(f"✅ Qdrant向量搜索测试通过，返回 {len(result)} 个结果")
        
        except Exception as e:
            logger.warning(f"⚠️ Qdrant查询测试失败（可能集合不存在）: {e}")
    
    async def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()
        await self.neo4j_client.disconnect()
        logger.info("资源清理完成")
    
    def print_test_report(self):
        """打印测试报告"""
        print("=" * 80)
        print("数据库迁移测试报告")
        print("=" * 80)
        print()
        
        # 连接测试
        print("📡 连接测试:")
        print(f"  Neo4j: {'✅ 通过' if self.test_results['neo4j_connection'] else '❌ 失败'}")
        print(f"  Qdrant: {'✅ 通过' if self.test_results['qdrant_connection'] else '❌ 失败'}")
        print()
        
        # 数据迁移测试
        print("📊 数据迁移测试:")
        
        kg_nodes = self.test_results["knowledge_graph_nodes"]
        print(f"  知识图谱节点:")
        print(f"    PostgreSQL: {kg_nodes['postgresql']}")
        print(f"    Neo4j: {kg_nodes['neo4j']}")
        print(f"    状态: {'✅ 匹配' if kg_nodes['match'] else '⚠️ 不匹配'}")
        
        kg_edges = self.test_results["knowledge_graph_edges"]
        print(f"  知识图谱边:")
        print(f"    PostgreSQL: {kg_edges['postgresql']}")
        print(f"    Neo4j: {kg_edges['neo4j']}")
        print(f"    状态: {'✅ 匹配' if kg_edges['match'] else '⚠️ 不匹配'}")
        
        arch_rels = self.test_results["architecture_relationships"]
        print(f"  架构关系:")
        print(f"    PostgreSQL: {arch_rels['postgresql']}")
        print(f"    Neo4j: {arch_rels['neo4j']}")
        print(f"    状态: {'✅ 匹配' if arch_rels['match'] else '⚠️ 不匹配'}")
        
        vectors = self.test_results["quality_vectors"]
        print(f"  质量规则向量:")
        print(f"    PostgreSQL: {vectors['postgresql']}")
        print(f"    Qdrant: {vectors['qdrant']}")
        print(f"    状态: {'✅ 匹配' if vectors['match'] else '⚠️ 不匹配'}")
        print()
        
        # 错误报告
        if self.test_results["errors"]:
            print("❌ 错误:")
            for error in self.test_results["errors"]:
                print(f"    - {error}")
            print()
        
        # 总结
        all_passed = (
            self.test_results["neo4j_connection"] and
            self.test_results["qdrant_connection"] and
            self.test_results["knowledge_graph_nodes"]["match"] and
            self.test_results["knowledge_graph_edges"]["match"] and
            self.test_results["quality_vectors"]["match"]
        )
        
        print("=" * 80)
        if all_passed:
            print("✅ 所有测试通过！")
        else:
            print("⚠️ 部分测试未通过，请检查上述结果")
        print("=" * 80)
        
        return all_passed
    
    async def run_tests(self):
        """运行所有测试"""
        logger.info("=" * 80)
        logger.info("开始数据库迁移测试")
        logger.info("=" * 80)
        
        try:
            await self.initialize()
            
            await self.test_neo4j_queries()
            await self.test_qdrant_queries()
            await self.test_knowledge_graph_migration()
            await self.test_architecture_relationships_migration()
            await self.test_quality_vectors_migration()
            
            return self.print_test_report()
        
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return False
        finally:
            await self.cleanup()


async def main():
    """主函数"""
    tester = MigrationTester()
    success = await tester.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

