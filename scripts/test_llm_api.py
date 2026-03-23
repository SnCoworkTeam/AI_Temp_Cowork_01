#!/usr/bin/env python3
"""
测试LLM API是否正常工作
"""

import requests
import json
import os

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def test_llm_api():
    """测试LLM API"""
    print("=" * 60)
    print("测试LLM API")
    print("=" * 60)
    print()
    
    print(f"LLM Base URL: {LLM_BASE_URL}")
    print(f"API Key: {'已设置' if OPENAI_API_KEY else '未设置'}")
    print()
    
    # 测试不同的端点
    endpoints = [
        f"{LLM_BASE_URL}/v1/chat/completions",
        f"{LLM_BASE_URL}/chat/completions",
        f"{LLM_BASE_URL}/api/v1/chat/completions",
        f"{LLM_BASE_URL}/api/chat/completions",
    ]
    
    test_prompt = "分析以下两个业务实体之间的关系：实体1: 物料, 实体2: 供应商。返回JSON格式：{\"relationship_type\": \"related_to\", \"confidence\": 0.9, \"reason\": \"原因\"}"
    
    for endpoint in endpoints:
        print(f"测试端点: {endpoint}")
        try:
            headers = {
                "Content-Type": "application/json"
            }
            if OPENAI_API_KEY:
                headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个业务实体关系分析专家。分析两个业务实体之间的关系，返回JSON格式。"
                    },
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ],
                "temperature": 0.3
            }
            
            r = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            print(f"  状态码: {r.status_code}")
            if r.status_code == 200:
                result = r.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  ✅ 成功！响应: {content[:100]}...")
                print()
                return endpoint, True
            else:
                print(f"  ❌ 失败: {r.text[:200]}")
        except Exception as e:
            print(f"  ❌ 异常: {e}")
        
        print()
    
    return None, False

if __name__ == "__main__":
    endpoint, success = test_llm_api()
    if success:
        print("=" * 60)
        print(f"✅ LLM API测试成功！可用端点: {endpoint}")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ LLM API测试失败，所有端点都无法访问")
        print("=" * 60)




