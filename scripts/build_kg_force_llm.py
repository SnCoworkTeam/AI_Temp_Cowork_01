#!/usr/bin/env python3
"""
强制使用LLM增强构建知识图谱
确保LLM被调用
"""

import requests
import time
import json

METADATA_SERVICE_URL = "http://localhost:8005"

def build_with_llm():
    """使用LLM增强构建知识图谱"""
    print("=" * 60)
    print("强制使用LLM增强构建知识图谱")
    print("=" * 60)
    print()
    
    # 1. 检查当前状态
    print("1. 检查当前知识图谱状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_before = stats.get('total_edges', 0)
            print(f"   构建前边数: {edges_before}")
        else:
            edges_before = 0
    except:
        edges_before = 0
    print()
    
    # 2. 构建知识图谱（强制使用LLM）
    print("2. 开始构建知识图谱（强制启用LLM）...")
    print("   注意：这将处理所有实体，可能需要10-30分钟")
    print("   可以监控日志: docker-compose logs -f metadata-service")
    print()
    
    payload = {
        "use_llm": True,  # 强制启用LLM
        "force_rebuild": False,
        "priority_entities": None
    }
    
    try:
        print("   发送请求...")
        r = requests.post(
            f"{METADATA_SERVICE_URL}/api/ontology/build",
            json=payload,
            timeout=1800  # 30分钟超时
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
        print("   ⚠️ 请求超时（LLM处理时间较长）")
        print("   请检查服务日志: docker-compose logs metadata-service | grep -i llm")
        print("   构建可能在后台继续，请稍后检查知识图谱状态")
        return
    except Exception as e:
        print(f"   ❌ 构建异常: {e}")
        return
    
    print()
    
    # 3. 检查构建后状态
    print("3. 检查构建后的知识图谱状态...")
    time.sleep(3)
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_after = stats.get('total_edges', 0)
            print(f"   构建后边数: {edges_after}")
            print(f"   边数增加: {edges_after - edges_before}")
            print(f"   边类型分布: {stats.get('edges_by_type', {})}")
            
            if edges_after >= 200:
                print("   ✅ 已达到目标（边>200）！")
            else:
                print(f"   ⚠️ 未达到目标，还差 {200 - edges_after} 条边")
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    build_with_llm()





