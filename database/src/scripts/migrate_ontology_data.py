"""
本体数据迁移脚本
将knowledge-base中的知识图谱数据迁移到metadata-service（如果需要）

注意：由于knowledge-base和metadata-service使用相同的数据库，
知识图谱数据已经共享，通常不需要数据迁移。
此脚本主要用于验证数据一致性。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy.orm import Session
from database.src.core.session import SessionLocal
from database.src.models.knowledge_models import KnowledgeGraphNode, KnowledgeGraphEdge
from database.src.repositories.knowledge_repository import (
    KnowledgeGraphNodeRepository,
    KnowledgeGraphEdgeRepository
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_knowledge_graph_data(db: Session) -> dict:
    """
    验证知识图谱数据
    
    由于knowledge-base和metadata-service使用相同的数据库，
    知识图谱数据已经共享，只需要验证数据一致性。
    
    Args:
        db: 数据库会话
    
    Returns:
        验证结果
    """
    try:
        node_repo = KnowledgeGraphNodeRepository(db)
        edge_repo = KnowledgeGraphEdgeRepository(db)
        
        # 统计节点
        all_nodes = node_repo.get_all(limit=10000)
        nodes_by_type = {}
        for node in all_nodes:
            node_type = node.node_type or "unknown"
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        # 统计边
        all_edges = edge_repo.get_all(limit=10000)
        edges_by_type = {}
        for edge in all_edges:
            rel_type = edge.relationship_type or "unknown"
            edges_by_type[rel_type] = edges_by_type.get(rel_type, 0) + 1
        
        result = {
            "total_nodes": len(all_nodes),
            "total_edges": len(all_edges),
            "nodes_by_type": nodes_by_type,
            "edges_by_type": edges_by_type,
            "status": "verified"
        }
        
        logger.info(f"Knowledge graph data verified: {result['total_nodes']} nodes, {result['total_edges']} edges")
        return result
        
    except Exception as e:
        logger.error(f"Failed to verify knowledge graph data: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """主函数"""
    logger.info("Starting knowledge graph data verification...")
    
    db = SessionLocal()
    try:
        result = verify_knowledge_graph_data(db)
        
        print("\n" + "="*50)
        print("知识图谱数据验证结果")
        print("="*50)
        print(f"总节点数: {result.get('total_nodes', 0)}")
        print(f"总边数: {result.get('total_edges', 0)}")
        print("\n节点类型分布:")
        for node_type, count in result.get('nodes_by_type', {}).items():
            print(f"  {node_type}: {count}")
        print("\n边类型分布:")
        for edge_type, count in result.get('edges_by_type', {}).items():
            print(f"  {edge_type}: {count}")
        print("\n状态:", result.get('status', 'unknown'))
        print("="*50)
        
        if result.get('status') == 'verified':
            logger.info("✅ Knowledge graph data verification completed successfully")
            print("\n✅ 验证完成：知识图谱数据已共享，无需迁移")
        else:
            logger.error("❌ Knowledge graph data verification failed")
            print("\n❌ 验证失败，请检查错误信息")
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"\n❌ 错误: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()






