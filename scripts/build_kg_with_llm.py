#!/usr/bin/env python3
"""
使用LLM增强重新构建知识图谱
"""

import requests
import time
import json

METADATA_SERVICE_URL = "http://localhost:8005"

def get_kg_stats():
    """获取知识图谱统计"""
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('statistics', {})
        return {}
    except Exception as e:
        print(f"获取统计失败: {e}")
        return {}

def build_ontology_with_llm(force_rebuild=False):
    """使用LLM增强构建知识图谱"""
    print("=" * 60)
    print("使用LLM增强构建知识图谱")
    print("=" * 60)
    print()
    
    # 1. 检查当前状态
    print("1. 检查当前知识图谱状态...")
    stats_before = get_kg_stats()
    print(f"   构建前边数: {stats_before.get('total_edges', 0)}")
    print(f"   构建前节点数: {stats_before.get('total_nodes', 0)}")
    print()
    
    # 2. 构建知识图谱
    print("2. 开始构建知识图谱（启用LLM增强）...")
    payload = {
        "use_llm": True,
        "force_rebuild": force_rebuild,
        "priority_entities": None
    }
    
    try:
        print("   发送请求...")
        r = requests.post(
            f"{METADATA_SERVICE_URL}/api/ontology/build",
            json=payload,
            timeout=1800  # 30分钟超时（LLM处理可能需要较长时间）
        )
        
        if r.status_code == 200:
            result = r.json()
            print("   ✅ 构建成功")
            print(f"   关系数: {result.get('relationships', 0)}")
            print(f"   概念数: {result.get('concepts', 0)}")
        else:
            print(f"   ❌ 构建失败: {r.status_code}")
            print(f"   错误信息: {r.text}")
            return
    except requests.exceptions.Timeout:
        print("   ⚠️ 请求超时（可能LLM处理时间较长）")
        print("   请检查服务日志")
        return
    except Exception as e:
        print(f"   ❌ 构建异常: {e}")
        return
    
    print()
    
    # 3. 检查构建后状态
    print("3. 检查构建后的知识图谱状态...")
    time.sleep(2)  # 等待数据写入
    stats_after = get_kg_stats()
    print(f"   构建后边数: {stats_after.get('total_edges', 0)}")
    print(f"   构建后节点数: {stats_after.get('total_nodes', 0)}")
    print(f"   边类型分布: {stats_after.get('edges_by_type', {})}")
    print()
    
    # 4. 计算增量
    edges_before = stats_before.get('total_edges', 0)
    edges_after = stats_after.get('total_edges', 0)
    edge_increase = edges_after - edges_before
    
    print("=" * 60)
    print("构建结果")
    print("=" * 60)
    print(f"边数增加: {edge_increase}")
    print(f"当前边数: {edges_after}")
    print(f"目标: >200")
    
    if edges_after >= 200:
        print("✅ 已达到目标（边>200）")
    else:
        print(f"❌ 未达到目标，还差 {200 - edges_after} 条边")
    
    print("=" * 60)

if __name__ == "__main__":
    import sys
    force_rebuild = "--force" in sys.argv
    build_ontology_with_llm(force_rebuild=force_rebuild)

