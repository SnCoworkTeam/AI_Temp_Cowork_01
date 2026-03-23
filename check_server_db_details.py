"""
检查服务器数据库的详细数据
"""
import subprocess
from pathlib import Path

SERVER_IP = "43.143.139.197"
SERVER_USER = "ubuntu"
KEY_FILE = "enterprise_ai_platform.pem"

def run_ssh_command(cmd):
    """执行SSH命令"""
    key_path = Path(KEY_FILE)
    if not key_path.exists():
        print(f"❌ 找不到SSH密钥文件: {KEY_FILE}")
        return None
    
    full_cmd = f'ssh -i {key_path} -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 命令执行失败: {result.stderr}")
        return None
    
    return result.stdout

def check_database():
    """检查数据库数据"""
    print("=" * 60)
    print("服务器数据库详细检查")
    print("=" * 60)
    
    # 基本统计
    print("\n📊 基本统计:")
    cmd = "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT COUNT(*) as node_count FROM knowledge_graph_nodes; SELECT COUNT(*) as edge_count FROM knowledge_graph_edges;\""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    # 节点类型分布
    print("\n📌 节点类型分布:")
    cmd = "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT node_type, COUNT(*) as count FROM knowledge_graph_nodes GROUP BY node_type ORDER BY count DESC;\""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    # 关系类型分布
    print("\n🔗 关系类型分布:")
    cmd = "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT relationship_type, COUNT(*) as count FROM knowledge_graph_edges GROUP BY relationship_type ORDER BY count DESC;\""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    # 检查边的有效性（source和target是否都存在）
    print("\n✅ 检查边的有效性:")
    cmd = """cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c "SELECT 
    COUNT(*) as total_edges,
    COUNT(CASE WHEN s.id IS NULL THEN 1 END) as missing_source,
    COUNT(CASE WHEN t.id IS NULL THEN 1 END) as missing_target
FROM knowledge_graph_edges e
LEFT JOIN knowledge_graph_nodes s ON e.source_node_id = s.id
LEFT JOIN knowledge_graph_nodes t ON e.target_node_id = t.id;"
"""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    # 节点示例
    print("\n📋 节点示例（前5个）:")
    cmd = "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT id, label, node_type FROM knowledge_graph_nodes LIMIT 5;\""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    # 边示例
    print("\n🔗 边示例（前5个）:")
    cmd = "cd /opt/enterprise-ai-platform && docker compose exec -T postgres psql -U ai_user -d ai_platform -c \"SELECT id, source_node_id, target_node_id, relationship_type FROM knowledge_graph_edges LIMIT 5;\""
    output = run_ssh_command(cmd)
    if output:
        print(output)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_database()



