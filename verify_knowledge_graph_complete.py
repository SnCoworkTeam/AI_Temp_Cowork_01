#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整验证知识图谱
"""
import requests
import json
import io
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

METADATA_SERVICE_URL = "http://localhost:8005"
KNOWLEDGE_BASE_URL = "http://localhost:8004"

def verify_entities():
    """验证实体"""
    print("=" * 60)
    print("1. 验证SAP MM实体")
    print("=" * 60)
    print()
    
    try:
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/business-entities?search=MM&limit=20",
            timeout=10
        )
        if response.status_code == 200:
            entities = response.json()
            print(f"✅ 找到 {len(entities)} 个SAP MM相关实体")
            print()
            print("实体列表:")
            for entity in entities[:8]:
                print(f"  - {entity.get('display_name')} (ID: {entity.get('id')}, 类型: {entity.get('entity_type')})")
        else:
            print(f"❌ 查询失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def verify_knowledge_graph():
    """验证知识图谱"""
    print()
    print("=" * 60)
    print("2. 验证知识图谱节点和关系")
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
            print(f"✅ 总节点数: {count}")
            
            sap_nodes = [n for n in nodes if n.get("properties", {}).get("sap_module") == "MM"]
            print(f"✅ SAP MM节点数: {len(sap_nodes)}")
            print()
            print("SAP MM节点示例（前10个）:")
            for node in sap_nodes[:10]:
                props = node.get("properties", {})
                print(f"  - {node.get('label')} (类型: {node.get('node_type')}, 实体ID: {props.get('entity_id')})")
        
        # 查询边
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/knowledge-graph/edges?limit=100",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            edges = data.get("edges", [])
            count = data.get("count", len(edges))
            print()
            print(f"✅ 总边数: {count}")
            print()
            print("关系边示例（前10个）:")
            for edge in edges[:10]:
                print(f"  - {edge.get('relationship_type')}: {edge.get('source_id')} -> {edge.get('target_id')}")
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def verify_documents():
    """验证文档"""
    print()
    print("=" * 60)
    print("3. 验证知识库文档")
    print("=" * 60)
    print()
    
    try:
        response = requests.get(
            f"{KNOWLEDGE_BASE_URL}/api/documents?limit=20",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", []) if isinstance(data, dict) else data
            print(f"✅ 找到 {len(documents)} 个文档")
            print()
            print("文档列表:")
            for doc in documents[:10]:
                print(f"  - {doc.get('title', doc.get('filename', 'Unknown'))} (ID: {doc.get('id')})")
        else:
            print(f"❌ 查询失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def verify_document_entity_links():
    """验证文档-实体关联"""
    print()
    print("=" * 60)
    print("4. 验证文档-实体关联")
    print("=" * 60)
    print()
    
    try:
        # 这里需要调用文档-实体关联API
        # 暂时跳过，因为需要确认API端点
        print("⚠️  文档-实体关联验证需要确认API端点")
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    verify_entities()
    verify_knowledge_graph()
    verify_documents()
    verify_document_entity_links()
    
    print()
    print("=" * 60)
    print("验证完成")
    print("=" * 60)





