#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证SAP MM知识图谱
"""
import requests
import json
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

METADATA_SERVICE_URL = "http://localhost:8005"

def verify_graph():
    """验证知识图谱"""
    print("=" * 60)
    print("验证SAP MM知识图谱")
    print("=" * 60)
    print()
    
    try:
        # 查询节点
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/knowledge-graph/nodes?limit=100",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            count = data.get("count", len(nodes))
            print(f"总节点数: {count}")
            
            sap_nodes = [n for n in nodes if n.get("properties", {}).get("sap_module") == "MM"]
            print(f"SAP MM节点数: {len(sap_nodes)}")
            print()
            print("SAP MM节点列表:")
            for node in sap_nodes[:10]:
                print(f"  - {node.get('label')} (类型: {node.get('node_type')})")
        
        # 查询边
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/knowledge-graph/edges?limit=50",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            edges = data.get("edges", [])
            count = data.get("count", len(edges))
            print()
            print(f"总边数: {count}")
            print()
            print("关系边示例:")
            for edge in edges[:10]:
                print(f"  - {edge.get('relationship_type')}: {edge.get('source_id')} -> {edge.get('target_id')}")
    except Exception as e:
        print(f"验证失败: {e}")

if __name__ == "__main__":
    verify_graph()





