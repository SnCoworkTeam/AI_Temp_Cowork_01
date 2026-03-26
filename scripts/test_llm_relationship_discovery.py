#!/usr/bin/env python3
"""
测试LLM增强关系发现是否启用
"""

import requests
import json

METADATA_SERVICE_URL = "http://localhost:8005"

def test_llm_enabled():
    """测试LLM增强是否启用"""
    print("=" * 60)
    print("测试LLM增强关系发现")
    print("=" * 60)
    print()
    
    # 1. 检查服务状态
    print("1. 检查metadata-service状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/health", timeout=5)
        if r.status_code == 200:
            print("   ✅ metadata-service运行正常")
        else:
            print(f"   ❌ metadata-service状态异常: {r.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 无法连接metadata-service: {e}")
        return
    print()
    
    # 2. 检查知识图谱当前状态
    print("2. 检查知识图谱当前状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            print(f"   当前边数: {stats.get('total_edges', 0)}")
            print(f"   边类型分布: {stats.get('edges_by_type', {})}")
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
    print()
    
    # 3. 测试构建本体（启用LLM）
    print("3. 测试构建本体（启用LLM增强）...")
    print("   请求参数: use_llm=True, force_rebuild=False")
    try:
        payload = {
            "use_llm": True,
            "force_rebuild": False,
            "priority_entities": None
        }
        print("   发送请求...")
        r = requests.post(
            f"{METADATA_SERVICE_URL}/api/ontology/build",
            json=payload,
            timeout=300  # 5分钟超时
        )
        
        if r.status_code == 200:
            result = r.json()
            print("   ✅ 构建成功")
            print(f"   关系数: {result.get('relationships', 0)}")
            print(f"   概念数: {result.get('concepts', 0)}")
        else:
            print(f"   ❌ 构建失败: {r.status_code}")
            print(f"   错误信息: {r.text}")
    except requests.exceptions.Timeout:
        print("   ⚠️ 请求超时（可能LLM处理时间较长）")
    except Exception as e:
        print(f"   ❌ 构建异常: {e}")
    print()
    
    # 4. 检查构建后的知识图谱状态
    print("4. 检查构建后的知识图谱状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            print(f"   构建后边数: {stats.get('total_edges', 0)}")
            print(f"   边类型分布: {stats.get('edges_by_type', {})}")
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
    print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_llm_enabled()





