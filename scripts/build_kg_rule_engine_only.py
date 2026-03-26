#!/usr/bin/env python3
"""
使用规则引擎构建知识图谱（不启用LLM）
"""

import requests
import time

METADATA_SERVICE_URL = "http://localhost:8005"

def build_with_rule_engine_only():
    """使用规则引擎构建知识图谱"""
    print("=" * 60)
    print("使用规则引擎构建知识图谱（不启用LLM）")
    print("=" * 60)
    print()
    
    # 1. 检查当前状态
    print("1. 检查当前知识图谱状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=10)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_before = stats.get('total_edges', 0)
            print(f"   构建前边数: {edges_before}")
        else:
            edges_before = 0
    except Exception as e:
        print(f"   ⚠️ 无法获取当前状态: {e}")
        edges_before = 0
    print()
    
    # 2. 构建知识图谱（只使用规则引擎）
    print("2. 开始构建知识图谱（只使用规则引擎，不启用LLM）...")
    payload = {
        "use_llm": False,  # 不启用LLM
        "force_rebuild": False,
        "priority_entities": None
    }
    
    try:
        print("   发送请求...")
        r = requests.post(
            f"{METADATA_SERVICE_URL}/api/ontology/build",
            json=payload,
            timeout=600  # 10分钟超时
        )
        
        if r.status_code == 200:
            result = r.json()
            print("   ✅ 构建成功")
            print(f"   关系数: {result.get('relationships', 0)}")
            print(f"   概念数: {result.get('concepts', 0)}")
        else:
            print(f"   ❌ 构建失败: {r.status_code}")
            print(f"   错误信息: {r.text[:500]}")
            return
    except requests.exceptions.Timeout:
        print("   ⚠️ 请求超时")
        return
    except Exception as e:
        print(f"   ❌ 构建异常: {e}")
        return
    
    print()
    
    # 3. 检查构建后状态
    print("3. 检查构建后的知识图谱状态...")
    time.sleep(3)
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=10)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_after = stats.get('total_edges', 0)
            print(f"   构建后边数: {edges_after}")
            print(f"   边数增加: {edges_after - edges_before}")
            print(f"   边类型分布: {stats.get('edges_by_type', {})}")
            
            if edges_after >= 200:
                print("   ✅ 已达到目标（边>200）！")
                return True
            else:
                print(f"   ⚠️ 未达到目标，还差 {200 - edges_after} 条边")
                return False
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
        return False

if __name__ == "__main__":
    success = build_with_rule_engine_only()
    print()
    print("=" * 60)
    if success:
        print("✅ 构建成功，已达到目标！")
    else:
        print("⚠️ 构建完成，但未达到目标，需要继续完善数据")
    print("=" * 60)





