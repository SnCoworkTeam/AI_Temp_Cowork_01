"""
知识库API测试脚本
测试所有知识库相关的API端点
"""
import requests
import json
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8080/api/knowledge"  # 通过API Gateway
# BASE_URL = "http://localhost:8004/api"  # 直接访问知识库服务

def print_response(title: str, response: requests.Response):
    """打印响应信息"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_create_knowledge_base() -> Dict[str, Any]:
    """测试创建知识库"""
    print("测试创建知识库...")
    data = {
        "name": "测试知识库",
        "description": "这是一个测试知识库",
        "embedding_model": "default",
        "chunk_strategy": "fixed",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "settings": {
            "auto_index": True,
            "enable_search": True
        }
    }
    
    response = requests.post(f"{BASE_URL}/knowledge-bases", json=data)
    print_response("创建知识库", response)
    
    if response.status_code == 200:
        return response.json()
    return {}

def test_list_knowledge_bases():
    """测试获取知识库列表"""
    print("测试获取知识库列表...")
    response = requests.get(f"{BASE_URL}/knowledge-bases?page=1&page_size=10")
    print_response("获取知识库列表", response)
    return response.json() if response.status_code == 200 else {}

def test_get_knowledge_base(kb_id: str):
    """测试获取知识库详情"""
    print(f"测试获取知识库详情 (ID: {kb_id})...")
    response = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}")
    print_response("获取知识库详情", response)
    return response.json() if response.status_code == 200 else {}

def test_update_knowledge_base(kb_id: str):
    """测试更新知识库"""
    print(f"测试更新知识库 (ID: {kb_id})...")
    data = {
        "description": "更新后的描述",
        "chunk_size": 1500,
        "settings": {
            "auto_index": False,
            "enable_search": True,
            "new_setting": "test"
        }
    }
    
    response = requests.put(f"{BASE_URL}/knowledge-bases/{kb_id}", json=data)
    print_response("更新知识库 (PUT)", response)
    
    # 测试PATCH
    patch_data = {
        "description": "PATCH更新的描述"
    }
    response = requests.patch(f"{BASE_URL}/knowledge-bases/{kb_id}", json=patch_data)
    print_response("更新知识库 (PATCH)", response)
    return response.json() if response.status_code == 200 else {}

def test_get_knowledge_base_stats(kb_id: str):
    """测试获取知识库统计信息"""
    print(f"测试获取知识库统计信息 (ID: {kb_id})...")
    response = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}/stats")
    print_response("获取知识库统计信息", response)
    return response.json() if response.status_code == 200 else {}

def test_get_knowledge_base_documents(kb_id: str):
    """测试获取知识库下的文档列表"""
    print(f"测试获取知识库下的文档列表 (ID: {kb_id})...")
    response = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}/documents?page=1&page_size=10")
    print_response("获取知识库下的文档列表", response)
    return response.json() if response.status_code == 200 else {}

def test_delete_knowledge_base(kb_id: str):
    """测试删除知识库"""
    print(f"测试删除知识库 (ID: {kb_id})...")
    response = requests.delete(f"{BASE_URL}/knowledge-bases/{kb_id}")
    print_response("删除知识库", response)
    return response.status_code == 200

def main():
    """主测试函数"""
    print("="*60)
    print("知识库API测试")
    print("="*60)
    print(f"API Base URL: {BASE_URL}")
    print()
    
    # 测试创建知识库
    kb_data = test_create_knowledge_base()
    if not kb_data or 'id' not in kb_data:
        print("❌ 创建知识库失败，无法继续测试")
        return
    
    kb_id = kb_data['id']
    print(f"✅ 创建的知识库ID: {kb_id}")
    
    # 测试获取知识库列表
    test_list_knowledge_bases()
    
    # 测试获取知识库详情
    test_get_knowledge_base(kb_id)
    
    # 测试更新知识库
    test_update_knowledge_base(kb_id)
    
    # 测试获取统计信息
    test_get_knowledge_base_stats(kb_id)
    
    # 测试获取文档列表
    test_get_knowledge_base_documents(kb_id)
    
    # 询问是否删除测试知识库
    print("\n" + "="*60)
    delete = input("是否删除测试知识库? (y/n): ").strip().lower()
    if delete == 'y':
        test_delete_knowledge_base(kb_id)
    else:
        print(f"保留测试知识库，ID: {kb_id}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()



