"""
比较本地和服务器数据库的知识图谱数据
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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

# 服务器数据库配置（通过SSH）
SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_FILE = "enterprise_ai_platform.pem"

def get_local_db_stats():
    """获取本地数据库统计"""
    try:
        engine = create_engine(LOCAL_DATABASE_URL)
        with engine.connect() as conn:
            # 节点统计
            node_result = conn.execute(text("""
                SELECT COUNT(*) as count,
                       COUNT(DISTINCT node_type) as type_count
                FROM knowledge_graph_nodes
            """))
            node_row = node_result.fetchone()
            
            # 边统计
            edge_result = conn.execute(text("""
                SELECT COUNT(*) as count,
                       COUNT(DISTINCT relationship_type) as type_count
                FROM knowledge_graph_edges
            """))
            edge_row = edge_result.fetchone()
            
            # 节点类型分布
            type_result = conn.execute(text("""
                SELECT node_type, COUNT(*) as count
                FROM knowledge_graph_nodes
                GROUP BY node_type
                ORDER BY count DESC
            """))
            type_dist = {row[0]: row[1] for row in type_result.fetchall()}
            
            engine.dispose()
            
            return {
                "nodes": {
                    "total": node_row[0] if node_row else 0,
                    "type_count": node_row[1] if node_row else 0,
                    "type_distribution": type_dist
                },
                "edges": {
                    "total": edge_row[0] if edge_row else 0,
                    "type_count": edge_row[1] if edge_row else 0
                }
            }
    except Exception as e:
        print(f"❌ 本地数据库连接失败: {e}")
        return None

def get_server_db_stats():
    """获取服务器数据库统计"""
    key_path = Path(KEY_FILE)
    if not key_path.exists():
        print(f"❌ 找不到SSH密钥文件: {KEY_FILE}")
        return None
    
    try:
        # 通过SSH执行SQL查询
        cmd = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \\"SELECT COUNT(*) as node_count, COUNT(DISTINCT node_type) as type_count FROM knowledge_graph_nodes; SELECT COUNT(*) as edge_count, COUNT(DISTINCT relationship_type) as rel_type_count FROM knowledge_graph_edges; SELECT node_type, COUNT(*) as count FROM knowledge_graph_nodes GROUP BY node_type ORDER BY count DESC;\\""'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 服务器数据库查询失败: {result.stderr}")
            return None
        
        output = result.stdout
        lines = output.strip().split('\n')
        
        # 解析节点统计
        node_line = None
        edge_line = None
        type_lines = []
        
        for i, line in enumerate(lines):
            if 'node_count' in line or 'count' in line.lower():
                if 'node_count' in line:
                    node_line = lines[i+1] if i+1 < len(lines) else None
                elif 'edge_count' in line:
                    edge_line = lines[i+1] if i+1 < len(lines) else None
                elif 'node_type' in line:
                    # 开始类型分布
                    j = i + 1
                    while j < len(lines) and lines[j].strip() and not lines[j].startswith('('):
                        if '|' in lines[j]:
                            type_lines.append(lines[j])
                        j += 1
        
        # 解析数据
        node_count = 0
        node_type_count = 0
        edge_count = 0
        edge_type_count = 0
        type_dist = {}
        
        if node_line:
            parts = node_line.split('|')
            if len(parts) >= 2:
                node_count = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                node_type_count = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
        
        if edge_line:
            parts = edge_line.split('|')
            if len(parts) >= 2:
                edge_count = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                edge_type_count = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
        
        for line in type_lines:
            parts = line.split('|')
            if len(parts) >= 2:
                node_type = parts[0].strip()
                count = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                if node_type:
                    type_dist[node_type] = count
        
        return {
            "nodes": {
                "total": node_count,
                "type_count": node_type_count,
                "type_distribution": type_dist
            },
            "edges": {
                "total": edge_count,
                "type_count": edge_type_count
            }
        }
    except Exception as e:
        print(f"❌ 获取服务器数据库统计失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_databases():
    """比较两个数据库"""
    print("=" * 60)
    print("数据库比较：本地 vs 服务器")
    print("=" * 60)
    
    print("\n📊 获取本地数据库统计...")
    local_stats = get_local_db_stats()
    
    print("📊 获取服务器数据库统计...")
    server_stats = get_server_db_stats()
    
    if not local_stats:
        print("\n⚠️  无法获取本地数据库统计，跳过比较")
        return
    
    if not server_stats:
        print("\n⚠️  无法获取服务器数据库统计，跳过比较")
        return
    
    print("\n" + "=" * 60)
    print("比较结果")
    print("=" * 60)
    
    # 节点比较
    print("\n📌 节点统计:")
    print(f"  本地: {local_stats['nodes']['total']} 个节点, {local_stats['nodes']['type_count']} 种类型")
    print(f"  服务器: {server_stats['nodes']['total']} 个节点, {server_stats['nodes']['type_count']} 种类型")
    
    if local_stats['nodes']['total'] == server_stats['nodes']['total']:
        print("  ✅ 节点总数一致")
    else:
        diff = server_stats['nodes']['total'] - local_stats['nodes']['total']
        print(f"  ⚠️  节点总数不一致，差异: {diff}")
    
    # 边比较
    print("\n🔗 边统计:")
    print(f"  本地: {local_stats['edges']['total']} 条边, {local_stats['edges']['type_count']} 种关系类型")
    print(f"  服务器: {server_stats['edges']['total']} 条边, {server_stats['edges']['type_count']} 种关系类型")
    
    if local_stats['edges']['total'] == server_stats['edges']['total']:
        print("  ✅ 边总数一致")
    else:
        diff = server_stats['edges']['total'] - local_stats['edges']['total']
        print(f"  ⚠️  边总数不一致，差异: {diff}")
    
    # 节点类型分布比较
    print("\n📊 节点类型分布:")
    all_types = set(local_stats['nodes']['type_distribution'].keys()) | set(server_stats['nodes']['type_distribution'].keys())
    
    for node_type in sorted(all_types):
        local_count = local_stats['nodes']['type_distribution'].get(node_type, 0)
        server_count = server_stats['nodes']['type_distribution'].get(node_type, 0)
        
        if local_count == server_count:
            print(f"  ✅ {node_type}: 本地={local_count}, 服务器={server_count}")
        else:
            print(f"  ⚠️  {node_type}: 本地={local_count}, 服务器={server_count} (差异: {server_count - local_count})")
    
    print("\n" + "=" * 60)
    
    # 总结
    nodes_match = local_stats['nodes']['total'] == server_stats['nodes']['total']
    edges_match = local_stats['edges']['total'] == server_stats['edges']['total']
    
    if nodes_match and edges_match:
        print("\n✅ 数据库数据一致！")
    else:
        print("\n⚠️  数据库数据不一致，需要同步")

if __name__ == "__main__":
    compare_databases()



