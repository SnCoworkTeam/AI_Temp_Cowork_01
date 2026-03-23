#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器上的文档上传和处理功能
"""
import requests
import json
import os
import sys
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 服务器配置
SERVER_URL = "http://43.143.139.197:8004"
API_GATEWAY_URL = "http://43.143.139.197:8080"

def test_health():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试 1: 健康检查")
    print("="*60)
    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

def test_get_knowledge_bases():
    """测试获取知识库列表"""
    print("\n" + "="*60)
    print("测试 2: 获取知识库列表")
    print("="*60)
    try:
        response = requests.get(f"{SERVER_URL}/api/knowledge-bases", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应类型: {type(data)}")
        print(f"响应内容: {data}")

        # 检查是否是列表
        if isinstance(data, list):
            print(f"知识库数量: {len(data)}")
            if data:
                print(f"第一个知识库: {data[0]}")
            return response.status_code == 200 and len(data) > 0, data
        # 检查是否是字典且包含knowledge_bases
        elif isinstance(data, dict) and 'knowledge_bases' in data:
            kbs = data['knowledge_bases']
            print(f"知识库数量: {len(kbs)}")
            if kbs:
                print(f"第一个知识库: {kbs[0]}")
            return response.status_code == 200 and len(kbs) > 0, kbs
        else:
            print(f"意外的响应格式")
            return False, []
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []

def test_upload_document(kb_id):
    """测试文档上传"""
    print("\n" + "="*60)
    print(f"测试 3: 上传文档到知识库 {kb_id}")
    print("="*60)

    # 创建一个测试文档
    test_content = """
# 测试文档

这是一个测试文档，用于验证服务器上的文档上传和处理功能。

## 功能测试
- 文档上传
- 文档解析
- 向量化处理
- 知识库集成

## 系统架构
本系统采用微服务架构，包含以下核心服务：
1. API网关
2. 知识库服务
3. 向量协调服务
4. 元数据服务
"""

    # 保存为临时文件
    test_file = Path("/tmp/test_doc.md")
    test_file.write_text(test_content, encoding='utf-8')

    try:
        # 上传文档
        with open(test_file, 'rb') as f:
            files = {
                'file': ('test_doc.md', f, 'text/markdown')
            }
            data = {
                'knowledge_base_id': kb_id
            }

            print(f"正在上传文档到: {SERVER_URL}/api/documents/upload")
            response = requests.post(
                f"{SERVER_URL}/api/documents/upload",
                files=files,
                data=data,
                timeout=30
            )

            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")

            if response.status_code == 200:
                result = response.json()
                print(f"上传成功!")
                print(f"文档ID: {result.get('document_id')}")
                return True, result.get('document_id')
            else:
                print(f"上传失败: {response.text}")
                return False, None

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_get_documents(kb_id):
    """测试获取文档列表"""
    print("\n" + "="*60)
    print(f"测试 4: 获取知识库 {kb_id} 的文档列表")
    print("="*60)
    try:
        response = requests.get(
            f"{SERVER_URL}/api/documents",
            params={"knowledge_base_id": kb_id},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应类型: {type(data)}")
        print(f"响应内容 (前500字符): {str(data)[:500]}")

        # 检查是否是列表
        if isinstance(data, list):
            print(f"文档数量: {len(data)}")
            if data:
                print(f"最新文档: {data[0]}")
            return response.status_code == 200 and len(data) > 0, data
        # 检查是否是字典且包含documents
        elif isinstance(data, dict) and 'documents' in data:
            docs = data['documents']
            print(f"文档数量: {len(docs)}")
            if docs:
                print(f"最新文档: {docs[0]}")
            return response.status_code == 200 and len(docs) > 0, docs
        else:
            print(f"意外的响应格式")
            return False, []
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []

def test_search_documents(kb_id, query="测试"):
    """测试文档搜索"""
    print("\n" + "="*60)
    print(f"测试 5: 在知识库 {kb_id} 中搜索: {query}")
    print("="*60)
    try:
        # 使用正确的搜索端点
        response = requests.post(
            f"{SERVER_URL}/api/search/semantic",
            json={
                "query": query,
                "knowledge_base_id": kb_id,
                "top_k": 3
            },
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"搜索结果数量: {len(data.get('results', []))}")
            if data.get('results'):
                print(f"第一个结果: {data['results'][0]}")
            return True
        else:
            print(f"搜索失败: {response.text}")
            return False
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("服务器文档处理功能测试")
    print("="*60)

    # 测试健康检查
    if not test_health():
        print("\n❌ 健康检查失败，服务可能未运行")
        return

    # 获取知识库列表
    success, knowledge_bases = test_get_knowledge_bases()
    if not success or not knowledge_bases:
        print("\n❌ 无法获取知识库列表")
        return

    # 使用第一个知识库进行测试
    kb_id = knowledge_bases[0].get('id')
    kb_name = knowledge_bases[0].get('name')
    print(f"\n使用知识库: {kb_name} (ID: {kb_id})")

    # 测试文档上传
    success, doc_id = test_upload_document(kb_id)
    if not success:
        print("\n❌ 文档上传失败")
        print("\n检查可能的问题:")
        print("1. 文件解析器是否正常工作")
        print("2. 向量化服务是否可用")
        print("3. 数据库连接是否正常")
        return

    # 测试获取文档列表
    success, docs = test_get_documents(kb_id)
    if not success:
        print("\n❌ 获取文档列表失败")
        return

    # 测试文档搜索
    if not test_search_documents(kb_id, "测试"):
        print("\n❌ 文档搜索失败")
        return

    print("\n" + "="*60)
    print("✅ 所有测试通过!")
    print("="*60)

if __name__ == "__main__":
    main()
