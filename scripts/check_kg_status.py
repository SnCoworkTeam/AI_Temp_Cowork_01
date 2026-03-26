#!/usr/bin/env python3
"""
检查知识图谱状态
"""

import requests

METADATA_SERVICE_URL = "http://localhost:8005"

def check_kg_status():
    """检查知识图谱状态"""
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=30)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            
            print("=" * 60)
            print("知识图谱当前状态")
            print("=" * 60)
            print(f"节点数: {stats.get('total_nodes', 0)}")
            print(f"边数: {stats.get('total_edges', 0)}")
            print(f"节点类型分布: {stats.get('nodes_by_type', {})}")
            print(f"边类型分布: {stats.get('edges_by_type', {})}")
            print()
            
            edges = stats.get('total_edges', 0)
            if edges >= 200:
                print(f"✅ 已达到目标（边>200）！当前: {edges}条")
            else:
                print(f"❌ 未达到目标，还差 {200 - edges} 条边（当前: {edges}条）")
            
            print("=" * 60)
        else:
            print(f"❌ 无法获取知识图谱统计: {r.status_code}")
    except Exception as e:
        print(f"❌ 获取知识图谱统计异常: {e}")

if __name__ == "__main__":
    check_kg_status()

