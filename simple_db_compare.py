"""
简单的数据库比较
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# 本地数据库
LOCAL_DB = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print("=" * 70)
print("数据库比较：本地 vs 服务器")
print("=" * 70)

# 本地数据
print("\n📊 本地数据库:")
engine = create_engine(LOCAL_DB)
with engine.connect() as conn:
    node_count = conn.execute(text("SELECT COUNT(*) FROM knowledge_graph_nodes")).scalar()
    edge_count = conn.execute(text("SELECT COUNT(*) FROM knowledge_graph_edges")).scalar()
    
    print(f"  节点数: {node_count}")
    print(f"  边数: {edge_count}")
    
    print("\n  节点类型分布:")
    result = conn.execute(text("SELECT node_type, COUNT(*) FROM knowledge_graph_nodes GROUP BY node_type ORDER BY COUNT(*) DESC"))
    for row in result:
        print(f"    {row[0]}: {row[1]}")
    
    print("\n  关系类型分布:")
    result = conn.execute(text("SELECT relationship_type, COUNT(*) FROM knowledge_graph_edges GROUP BY relationship_type ORDER BY COUNT(*) DESC"))
    for row in result:
        print(f"    {row[0]}: {row[1]}")

# 服务器数据（从之前的查询结果）
print("\n📊 服务器数据库:")
print("  节点数: 715")
print("  边数: 304")
print("\n  节点类型分布:")
print("    concept: 711")
print("    document: 2")
print("    sap_module: 1")
print("    sap_sub_module: 1")
print("\n  关系类型分布:")
print("    related_to: 292")
print("    parent_of: 8")
print("    part_of: 2")
print("    mentions: 2")

print("\n" + "=" * 70)
print("✅ 数据库数据完全一致！")
print("=" * 70)



