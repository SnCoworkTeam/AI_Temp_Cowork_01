"""
知识库功能测试脚本
测试所有知识库API功能
"""
import requests
import json
import sys
from typing import Dict, Any

# 配置
BASE_URL = "http://43.143.139.197:8080/api/knowledge"
TIMEOUT = 30

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(success: bool, message: str, data: Any = None):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status}: {message}")
    if data and success:
        if isinstance(data, dict):
            print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   响应: {data}")

def test_document_list():
    """测试文档列表API"""
    print_section("1. 测试文档列表API")
    
    try:
        # 测试1: 获取所有文档
        response = requests.get(
            f"{BASE_URL}/documents",
            params={"limit": 5, "page": 1},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            total = data.get("total", 0)
            
            print_result(True, f"获取文档列表成功，共 {total} 个文档")
            
            # 检查total_chunks字段
            if documents:
                print(f"\n   前5个文档的chunks数量:")
                for doc in documents[:5]:
                    doc_id = doc.get("id", "N/A")[:8]
                    filename = doc.get("filename", "N/A")
                    status = doc.get("status", "N/A")
                    total_chunks = doc.get("total_chunks", 0)
                    print(f"   - {filename} ({status}): {total_chunks} chunks")
                
                # 验证total_chunks是否正确
                processed_docs = [d for d in documents if d.get("status") == "processed"]
                if processed_docs:
                    has_chunks = any(d.get("total_chunks", 0) > 0 for d in processed_docs)
                    if has_chunks:
                        print_result(True, "total_chunks字段正确显示")
                    else:
                        print_result(False, "processed文档的total_chunks仍为0")
                else:
                    print_result(False, "没有processed状态的文档")
            else:
                print_result(False, "文档列表为空")
        else:
            print_result(False, f"请求失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_document_detail():
    """测试文档详情API"""
    print_section("2. 测试文档详情API")
    
    try:
        # 先获取一个文档ID
        response = requests.get(
            f"{BASE_URL}/documents",
            params={"limit": 1, "status": "processed"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            if documents:
                doc_id = documents[0].get("id")
                filename = documents[0].get("filename")
                
                # 获取文档详情
                detail_response = requests.get(
                    f"{BASE_URL}/documents/{doc_id}",
                    timeout=TIMEOUT
                )
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    total_chunks = detail_data.get("total_chunks", 0)
                    print_result(True, f"获取文档详情成功: {filename}")
                    print(f"   文档ID: {doc_id}")
                    print(f"   状态: {detail_data.get('status', 'N/A')}")
                    print(f"   Chunks数量: {total_chunks}")
                    print(f"   文件大小: {detail_data.get('file_size', 0)} bytes")
                    
                    if total_chunks > 0:
                        print_result(True, "文档详情中的total_chunks正确")
                    else:
                        print_result(False, "文档详情中的total_chunks为0")
                else:
                    print_result(False, f"获取文档详情失败: {detail_response.status_code}")
            else:
                print_result(False, "没有可用的processed文档")
        else:
            print_result(False, f"获取文档列表失败: {response.status_code}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_semantic_search():
    """测试语义搜索功能"""
    print_section("3. 测试语义搜索功能")
    
    try:
        # 测试语义搜索
        search_data = {
            "query": "采购订单管理",
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/search/semantic",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            print_result(True, f"语义搜索成功，返回 {len(results)} 个结果")
            
            if results:
                print(f"\n   搜索结果:")
                for i, result in enumerate(results[:5], 1):
                    doc_id = result.get("document_id", "N/A")[:8]
                    filename = result.get("filename", "N/A")
                    score = result.get("score", 0)
                    content = result.get("content", "")[:100]
                    print(f"   {i}. {filename} (相似度: {score:.4f})")
                    print(f"      内容: {content}...")
                
                print_result(True, "语义搜索功能正常")
            else:
                print_result(False, "语义搜索返回空结果")
        else:
            print_result(False, f"语义搜索失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_vector_search():
    """测试向量搜索功能"""
    print_section("4. 测试向量搜索功能")
    
    try:
        # 测试向量搜索
        search_data = {
            "query": "供应商管理",
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/search/vector",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            print_result(True, f"向量搜索成功，返回 {len(results)} 个结果")
            
            if results:
                print(f"\n   搜索结果:")
                for i, result in enumerate(results[:5], 1):
                    doc_id = result.get("document_id", "N/A")[:8]
                    filename = result.get("filename", "N/A")
                    score = result.get("score", 0)
                    content = result.get("content", "")[:100]
                    print(f"   {i}. {filename} (相似度: {score:.4f})")
                    print(f"      内容: {content}...")
                
                print_result(True, "向量搜索功能正常")
            else:
                print_result(False, "向量搜索返回空结果")
        else:
            print_result(False, f"向量搜索失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_health_check():
    """测试健康检查"""
    print_section("5. 测试健康检查")
    
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "健康检查通过")
            print(f"   状态: {data.get('status', 'N/A')}")
        else:
            print_result(False, f"健康检查失败: {response.status_code}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_document_upload():
    """测试文档上传功能"""
    print_section("6. 测试文档上传功能")
    
    try:
        # 创建一个测试文档内容
        test_content = """
# 测试文档

这是一个用于测试知识库功能的文档。

## 内容

本文档包含以下内容：
1. 采购订单管理流程
2. 供应商管理规范
3. 物料主数据管理

## 采购订单管理

采购订单是企业采购管理的重要组成部分，包括订单创建、审批、执行等环节。

## 供应商管理

供应商管理涉及供应商的注册、评估、合作等全生命周期管理。
"""
        
        # 准备文件上传
        files = {
            'file': ('test_document.md', test_content.encode('utf-8'), 'text/markdown')
        }
        
        data = {
            'knowledge_base_id': None,  # 可选
            'tags': 'test,上传测试',
            'category': '测试文档'
        }
        
        print("   上传测试文档...")
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get("document_id") or result.get("id")
            filename = result.get("filename", "N/A")
            
            print_result(True, f"文档上传成功: {filename}")
            print(f"   文档ID: {document_id}")
            print(f"   状态: {result.get('status', 'N/A')}")
            
            # 返回文档ID用于后续测试
            return document_id
        else:
            print_result(False, f"文档上传失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")
        return None

def test_document_processing(document_id: str = None):
    """测试文档处理功能"""
    print_section("7. 测试文档处理功能")
    
    try:
        # 如果没有提供document_id，尝试获取一个processing状态的文档
        if not document_id:
            response = requests.get(
                f"{BASE_URL}/documents",
                params={"limit": 1, "status": "processing"},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                if documents:
                    document_id = documents[0].get("id")
                else:
                    print_result(False, "没有processing状态的文档用于测试")
                    return
        
        if not document_id:
            print_result(False, "没有可用的文档ID")
            return
        
        print(f"   监控文档处理: {document_id[:8]}...")
        
        # 检查文档处理进度
        progress_response = requests.get(
            f"{BASE_URL}/documents/{document_id}/progress",
            timeout=TIMEOUT
        )
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            print_result(True, "获取文档处理进度成功")
            print(f"   当前阶段: {progress_data.get('current_stage', 'N/A')}")
            print(f"   进度: {progress_data.get('progress', 0)}%")
            print(f"   状态: {progress_data.get('status', 'N/A')}")
            
            # 显示处理步骤
            steps = progress_data.get('steps', [])
            if steps:
                print(f"\n   处理步骤:")
                for step in steps:
                    step_name = step.get('name', 'N/A')
                    completed = step.get('completed', 0)
                    total = step.get('total', 0)
                    status = step.get('status', 'N/A')
                    print(f"   - {step_name}: {completed}/{total} ({status})")
        else:
            print_result(False, f"获取处理进度失败: {progress_response.status_code}")
        
        # 等待一段时间后检查文档状态
        import time
        print(f"\n   等待5秒后检查文档状态...")
        time.sleep(5)
        
        # 检查文档最终状态
        detail_response = requests.get(
            f"{BASE_URL}/documents/{document_id}",
            timeout=TIMEOUT
        )
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            status = detail_data.get("status", "N/A")
            total_chunks = detail_data.get("total_chunks", 0)
            
            print_result(True, f"文档状态: {status}")
            print(f"   Chunks数量: {total_chunks}")
            
            if status == "processed" and total_chunks > 0:
                print_result(True, "文档处理成功，chunks已生成")
            elif status == "processing":
                print_result(False, "文档仍在处理中，可能需要更多时间")
            elif status == "failed":
                print_result(False, "文档处理失败")
        else:
            print_result(False, f"获取文档详情失败: {detail_response.status_code}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def test_document_status():
    """测试文档状态统计"""
    print_section("8. 测试文档状态统计")
    
    try:
        # 获取所有状态的文档
        response = requests.get(
            f"{BASE_URL}/documents",
            params={"limit": 100},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            total = data.get("total", 0)
            
            # 统计各状态的文档数量
            status_count = {}
            chunks_count = 0
            
            for doc in documents:
                status = doc.get("status", "unknown")
                status_count[status] = status_count.get(status, 0) + 1
                chunks_count += doc.get("total_chunks", 0)
            
            print_result(True, f"文档统计: 共 {total} 个文档")
            print(f"\n   状态分布:")
            for status, count in status_count.items():
                print(f"   - {status}: {count} 个")
            
            print(f"\n   总chunks数: {chunks_count}")
            
            # 检查processed文档
            processed_count = status_count.get("processed", 0)
            if processed_count > 0:
                print_result(True, f"有 {processed_count} 个processed文档")
            else:
                print_result(False, "没有processed文档")
                
        else:
            print_result(False, f"获取文档列表失败: {response.status_code}")
            
    except Exception as e:
        print_result(False, f"测试异常: {str(e)}")

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  知识库功能测试")
    print("="*60)
    print(f"\n测试目标: {BASE_URL}")
    
    # 运行所有测试
    test_health_check()
    test_document_list()
    test_document_detail()
    test_document_status()
    
    # 测试文档上传和处理
    uploaded_doc_id = test_document_upload()
    if uploaded_doc_id:
        test_document_processing(uploaded_doc_id)
    else:
        # 如果没有新上传的文档，测试现有文档的处理
        test_document_processing()
    
    test_semantic_search()
    test_vector_search()
    
    print_section("测试完成")
    print("所有测试已完成，请查看上述结果。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试异常: {str(e)}")
        sys.exit(1)

