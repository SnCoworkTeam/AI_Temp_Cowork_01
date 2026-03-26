"""
比较本地和服务器数据库的知识图谱数据
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import subprocess

# 加载环境变量
load_dotenv()

# 本地数据库配置
LOCAL_DB_HOST = os.getenv("DB_HOST", "localhost")
LOCAL_DB_PORT = os.getenv("DB_PORT", "5432")
LOCAL_DB_NAME = os.getenv("DB_NAME", "ai_platform")
LOCAL_DB_USER = os.getenv("DB_USER", "ai_user")
LOCAL_DB_PASSWORD = os.getenv("DB_PASSWORD", "ai_password")

LOCAL_DATABASE_URL = f"postgresql://{LOCAL_DB_USER}:{LOCAL_DB_PASSWORD}@{LOCAL_DB_HOST}:{LOCAL_DB_PORT}/{LOCAL_DB_NAME}"

# 服务器配置
SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_FILE = "enterprise_ai_platform.pem"

def get_local_stats():
    """获取本地数据库统计"""
    try:
        engine = create_engine(LOCAL_DATABASE_URL)
        with engine.connect() as conn:
            # 节点统计
            result = conn.execute(text("SELECT COUNT(*) FROM knowledge_graph_nodes"))
            node_count = result.scalar()
            
            # 边统计
            result = conn.execute(text("SELECT COUNT(*) FROM knowledge_graph_edges"))
            edge_count = result.scalar()
            
            # 节点类型分布
            result = conn.execute(text("""
                SELECT node_type, COUNT(*) as count
                FROM knowledge_graph_nodes
                GROUP BY node_type
                ORDER BY count DESC
            """))
            type_dist = {row[0]: row[1] for row in result.fetchall()}
            
            # 关系类型分布
            result = conn.execute(text("""
                SELECT relationship_type, COUNT(*) as count
                FROM knowledge_graph_edges
                GROUP BY relationship_type
                ORDER BY count DESC
            """))
            rel_dist = {row[0]: row[1] for row in result.fetchall()}
            
            engine.dispose()
            
            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "type_distribution": type_dist,
                "rel_distribution": rel_dist
            }
    except Exception as e:
        print(f"❌ 本地数据库查询失败: {e}")
        return None

def get_server_stats():
    """获取服务器数据库统计"""
    key_path = Path(KEY_FILE)
    if not key_path.exists():
        print(f"❌ 找不到SSH密钥文件: {KEY_FILE}")
        return None
    
    try:
        # 节点和边数量
        cmd1 = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -t -c \\"SELECT COUNT(*) FROM knowledge_graph_nodes;\\""'
        result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
        node_count = int(result1.stdout.strip()) if result1.returncode == 0 and result1.stdout.strip().isdigit() else 0
        
        cmd2 = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -t -c \\"SELECT COUNT(*) FROM knowledge_graph_edges;\\""'
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        edge_count = int(result2.stdout.strip()) if result2.returncode == 0 and result2.stdout.strip().isdigit() else 0
        
        # 节点类型分布
        cmd3 = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -t -A -F\\"|\\" -c \\"SELECT node_type, COUNT(*) FROM knowledge_graph_nodes GROUP BY node_type ORDER BY COUNT(*) DESC;\\""'
        result3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
        type_dist = {}
        if result3.returncode == 0:
            for line in result3.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        node_type = parts[0].strip()
                        count = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                        if node_type:
                            type_dist[node_type] = count
        
        # 关系类型分布
        cmd4 = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -t -A -F\\"|\\" -c \\"SELECT relationship_type, COUNT(*) FROM knowledge_graph_edges GROUP BY relationship_type ORDER BY COUNT(*) DESC;\\""'
        result4 = subprocess.run(cmd4, shell=True, capture_output=True, text=True)
        rel_dist = {}
        if result4.returncode == 0:
            for line in result4.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        rel_type = parts[0].strip()
                        count = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                        if rel_type:
                            rel_dist[rel_type] = count
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "type_distribution": type_dist,
            "rel_distribution": rel_dist
        }
    except Exception as e:
        print(f"❌ 服务器数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_databases():
    """比较两个数据库"""
    print("=" * 70)
    print("数据库比较：本地 vs 服务器")
    print("=" * 70)
    
    print("\n📊 正在获取本地数据库统计...")
    local_stats = get_local_stats()
    
    print("📊 正在获取服务器数据库统计...")
    server_stats = get_server_stats()
    
    if not local_stats:
        print("\n❌ 无法获取本地数据库统计")
        return
    
    if not server_stats:
        print("\n❌ 无法获取服务器数据库统计")
        return
    
    print("\n" + "=" * 70)
    print("比较结果")
    print("=" * 70)
    
    # 节点比较
    print("\n📌 节点统计:")
    print(f"  本地:   {local_stats['node_count']:>6} 个节点")
    print(f"  服务器: {server_stats['node_count']:>6} 个节点")
    
    if local_stats['node_count'] == server_stats['node_count']:
        print("  ✅ 节点总数一致")
    else:
        diff = server_stats['node_count'] - local_stats['node_count']
        print(f"  ⚠️  节点总数不一致，差异: {diff:+d}")
    
    # 边比较
    print("\n🔗 边统计:")
    print(f"  本地:   {local_stats['edge_count']:>6} 条边")
    print(f"  服务器: {server_stats['edge_count']:>6} 条边")
    
    if local_stats['edge_count'] == server_stats['edge_count']:
        print("  ✅ 边总数一致")
    else:
        diff = server_stats['edge_count'] - local_stats['edge_count']
        print(f"  ⚠️  边总数不一致，差异: {diff:+d}")
    
    # 节点类型分布比较
    print("\n📊 节点类型分布:")
    all_types = set(local_stats['type_distribution'].keys()) | set(server_stats['type_distribution'].keys())
    
    print(f"{'类型':<20} {'本地':>10} {'服务器':>10} {'状态':<10}")
    print("-" * 50)
    
    for node_type in sorted(all_types):
        local_count = local_stats['type_distribution'].get(node_type, 0)
        server_count = server_stats['type_distribution'].get(node_type, 0)
        status = "✅" if local_count == server_count else "⚠️"
        print(f"{node_type:<20} {local_count:>10} {server_count:>10} {status:<10}")
    
    # 关系类型分布比较
    print("\n🔗 关系类型分布:")
    all_rels = set(local_stats['rel_distribution'].keys()) | set(server_stats['rel_distribution'].keys())
    
    print(f"{'关系类型':<20} {'本地':>10} {'服务器':>10} {'状态':<10}")
    print("-" * 50)
    
    for rel_type in sorted(all_rels):
        local_count = local_stats['rel_distribution'].get(rel_type, 0)
        server_count = server_stats['rel_distribution'].get(rel_type, 0)
        status = "✅" if local_count == server_count else "⚠️"
        print(f"{rel_type:<20} {local_count:>10} {server_count:>10} {status:<10}")
    
    print("\n" + "=" * 70)
    
    # 总结
    nodes_match = local_stats['node_count'] == server_stats['node_count']
    edges_match = local_stats['edge_count'] == server_stats['edge_count']
    types_match = local_stats['type_distribution'] == server_stats['type_distribution']
    rels_match = local_stats['rel_distribution'] == server_stats['rel_distribution']
    
    if nodes_match and edges_match and types_match and rels_match:
        print("\n✅ 数据库数据完全一致！")
    else:
        print("\n⚠️  数据库数据不一致，需要同步")
        if not nodes_match:
            print(f"   - 节点数量不一致")
        if not edges_match:
            print(f"   - 边数量不一致")
        if not types_match:
            print(f"   - 节点类型分布不一致")
        if not rels_match:
            print(f"   - 关系类型分布不一致")

if __name__ == "__main__":
    compare_databases()



