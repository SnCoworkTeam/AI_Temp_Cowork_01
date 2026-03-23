"""
检查本地数据库中的知识图谱数据
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ai_platform")
DB_USER = os.getenv("DB_USER", "ai_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ai_password")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_knowledge_graph_data():
    """检查知识图谱数据"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 60)
        print("检查知识图谱数据")
        print("=" * 60)
        
        # 检查节点数量
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM knowledge_graph_nodes
        """))
        node_count = result.scalar()
        print(f"\n📊 知识图谱节点数量: {node_count}")
        
        # 检查边数量
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM knowledge_graph_edges
        """))
        edge_count = result.scalar()
        print(f"🔗 知识图谱边数量: {edge_count}")
        
        # 如果有点数据，显示一些示例
        if node_count > 0:
            print("\n📋 节点示例（前10个）:")
            result = session.execute(text("""
                SELECT id, label, node_type, properties
                FROM knowledge_graph_nodes
                LIMIT 10
            """))
            nodes = result.fetchall()
            for i, node in enumerate(nodes, 1):
                node_id, label, node_type, properties = node
                print(f"  {i}. ID: {node_id}")
                print(f"     标签: {label}")
                print(f"     类型: {node_type}")
                if properties:
                    print(f"     属性: {str(properties)[:100]}...")
                print()
        
        # 如果有边数据，显示一些示例
        if edge_count > 0:
            print("\n🔗 边示例（前10个）:")
            result = session.execute(text("""
                SELECT e.id, e.source_node_id, e.target_node_id, e.relationship_type, 
                       s.label as source_label, t.label as target_label
                FROM knowledge_graph_edges e
                LEFT JOIN knowledge_graph_nodes s ON e.source_node_id = s.id
                LEFT JOIN knowledge_graph_nodes t ON e.target_node_id = t.id
                LIMIT 10
            """))
            edges = result.fetchall()
            for i, edge in enumerate(edges, 1):
                edge_id, source_id, target_id, rel_type, source_label, target_label = edge
                print(f"  {i}. ID: {edge_id}")
                print(f"     源节点: {source_label or source_id}")
                print(f"     目标节点: {target_label or target_id}")
                print(f"     关系类型: {rel_type}")
                print()
        
        # 按类型统计节点
        if node_count > 0:
            print("\n📊 按类型统计节点:")
            result = session.execute(text("""
                SELECT node_type, COUNT(*) as count
                FROM knowledge_graph_nodes
                GROUP BY node_type
                ORDER BY count DESC
            """))
            type_stats = result.fetchall()
            for node_type, count in type_stats:
                print(f"  {node_type or '(null)'}: {count}")
        
        # 按关系类型统计边
        if edge_count > 0:
            print("\n🔗 按关系类型统计边:")
            result = session.execute(text("""
                SELECT relationship_type, COUNT(*) as count
                FROM knowledge_graph_edges
                GROUP BY relationship_type
                ORDER BY count DESC
            """))
            rel_stats = result.fetchall()
            for rel_type, count in rel_stats:
                print(f"  {rel_type or '(null)'}: {count}")
        
        session.close()
        engine.dispose()
        
        print("\n" + "=" * 60)
        if node_count > 0 or edge_count > 0:
            print("✅ 数据库中有知识图谱数据")
        else:
            print("⚠️  数据库中没有知识图谱数据")
        print("=" * 60)
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "has_data": node_count > 0 or edge_count > 0
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_knowledge_graph_data()



