#!/usr/bin/env python3
"""
简单测试LLM增强关系发现
只测试少量实体对，验证LLM是否正常工作
"""

import requests
import json
import time

METADATA_SERVICE_URL = "http://localhost:8005"

def test_llm_relationship_discovery():
    """测试LLM增强关系发现"""
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
            return False
    except Exception as e:
        print(f"   ❌ 无法连接metadata-service: {e}")
        return False
    print()
    
    # 2. 获取当前知识图谱状态
    print("2. 获取当前知识图谱状态...")
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_before = stats.get('total_edges', 0)
            print(f"   当前边数: {edges_before}")
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
            edges_before = 0
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
        edges_before = 0
    print()
    
    # 3. 测试构建本体（启用LLM，但只处理少量实体）
    print("3. 测试构建本体（启用LLM增强）...")
    print("   注意：这将处理所有实体，可能需要较长时间")
    print("   如果只想测试，建议先完善数据后再构建")
    print()
    
    response = input("   是否继续？(y/n): ")
    if response.lower() != 'y':
        print("   已取消")
        return False
    
    try:
        payload = {
            "use_llm": True,
            "force_rebuild": False,
            "priority_entities": None
        }
        print("   发送请求（可能需要10-30分钟）...")
        print("   可以在另一个终端运行: docker-compose logs -f metadata-service")
        print()
        
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
            return False
    except requests.exceptions.Timeout:
        print("   ⚠️ 请求超时（LLM处理时间较长）")
        print("   请检查服务日志: docker-compose logs metadata-service | grep -i llm")
        return False
    except Exception as e:
        print(f"   ❌ 构建异常: {e}")
        return False
    
    print()
    
    # 4. 检查构建后的知识图谱状态
    print("4. 检查构建后的知识图谱状态...")
    time.sleep(2)
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges_after = stats.get('total_edges', 0)
            print(f"   构建后边数: {edges_after}")
            print(f"   边数增加: {edges_after - edges_before}")
            print(f"   边类型分布: {stats.get('edges_by_type', {})}")
            
            if edges_after > edges_before:
                print("   ✅ LLM增强关系发现正常工作！")
                return True
            else:
                print("   ⚠️ 边数未增加，可能LLM未发现新关系")
                return False
        else:
            print(f"   ⚠️ 无法获取知识图谱统计: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️ 获取知识图谱统计异常: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_relationship_discovery()
    print()
    print("=" * 60)
    if success:
        print("✅ LLM增强关系发现测试成功")
    else:
        print("❌ LLM增强关系发现测试失败或未完成")
    print("=" * 60)





