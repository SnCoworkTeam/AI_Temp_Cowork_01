#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建SAP MM知识图谱
"""
import requests
import json
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

METADATA_SERVICE_URL = "http://localhost:8005"

def build_ontology(use_llm=False):
    """构建知识图谱"""
    print("=" * 60)
    print("构建SAP MM知识图谱")
    print("=" * 60)
    print()
    
    print(f"使用LLM增强: {use_llm}")
    print()
    
    try:
        response = requests.post(
            f"{METADATA_SERVICE_URL}/api/ontology/sap/build",
            json={"use_llm": use_llm},
            timeout=300  # 增加到5分钟，因为实体数量多
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 知识图谱构建成功！")
            print()
            print("构建结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"❌ 构建失败: HTTP {response.status_code}")
            print(f"错误信息: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return None

def verify_graph():
    """验证知识图谱"""
    print()
    print("=" * 60)
    print("验证知识图谱")
    print("=" * 60)
    print()
    
    try:
        # 查询节点
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/knowledge-graph/nodes?limit=50",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            count = data.get("count", len(nodes))
            print(f"✅ 总节点数: {count}")
            
            sap_nodes = [n for n in nodes if n.get("properties", {}).get("sap_module") == "MM"]
            print(f"✅ SAP MM节点数: {len(sap_nodes)}")
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
            print(f"✅ 总边数: {count}")
            print()
            print("关系边示例:")
            for edge in edges[:5]:
                print(f"  - {edge.get('relationship_type')}: {edge.get('source_id')} -> {edge.get('target_id')}")
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    use_llm = "--llm" in sys.argv or "-l" in sys.argv
    
    result = build_ontology(use_llm=use_llm)
    
    if result:
        verify_graph()

