#!/usr/bin/env python3
"""
检查文档处理进度
用于查看文档是否已开始向量化
"""
import sys
import requests
import json
from datetime import datetime

def check_document_progress(document_id: str, base_url: str = "http://localhost:8004"):
    """检查文档处理进度"""
    
    print("=" * 60)
    print("文档处理进度检查")
    print("=" * 60)
    print(f"文档ID: {document_id}")
    print(f"服务地址: {base_url}")
    print()
    
    try:
        # 查询处理进度
        progress_url = f"{base_url}/api/documents/{document_id}/progress"
        print(f"查询进度: {progress_url}")
        response = requests.get(progress_url, timeout=5)
        
        if response.status_code == 200:
            progress = response.json()
            
            print("✅ 处理进度信息：")
            print(f"   当前阶段: {progress.get('stage', 'unknown')}")
            print(f"   进度百分比: {progress.get('progress_percentage', 0):.1f}%")
            print(f"   当前步骤: {progress.get('current_step', 'unknown')}")
            
            total_steps = progress.get('total_steps', 0)
            completed_steps = progress.get('completed_steps', 0)
            
            if total_steps > 0:
                print(f"   完成进度: {completed_steps}/{total_steps} 块")
            
            estimated_time = progress.get('estimated_time_remaining')
            if estimated_time:
                print(f"   预估剩余时间: {estimated_time:.1f} 秒")
            
            started_at = progress.get('started_at')
            if started_at:
                print(f"   开始时间: {started_at}")
            
            updated_at = progress.get('updated_at')
            if updated_at:
                print(f"   更新时间: {updated_at}")
            
            # 判断是否在向量化
            stage = progress.get('stage', '')
            print()
            print("📊 阶段分析：")
            
            if stage == 'embedding':
                print("   ✅ 正在向量化！")
                print(f"   📈 向量化进度: {completed_steps}/{total_steps} 块")
                if total_steps > 0:
                    embedding_progress = (completed_steps / total_steps) * 100
                    print(f"   📈 向量化百分比: {embedding_progress:.1f}%")
            elif stage == 'chunking':
                print("   ⏳ 还在分块阶段，尚未开始向量化")
            elif stage == 'storing':
                print("   ✅ 向量化已完成，正在存储")
            elif stage == 'completed':
                print("   ✅ 处理已完成！")
            elif stage == 'failed':
                error = progress.get('error', '未知错误')
                print(f"   ❌ 处理失败: {error}")
            else:
                print(f"   ℹ️  当前阶段: {stage}")
            
            # 显示详细信息
            details = progress.get('details', {})
            if details:
                print()
                print("📋 详细信息：")
                for key, value in details.items():
                    print(f"   {key}: {value}")
            
        elif response.status_code == 404:
            print("❌ 未找到进度信息")
            print("   可能的原因：")
            print("   - 文档ID不正确")
            print("   - 文档处理已完成，进度信息已清除")
            print("   - 文档尚未开始处理")
        else:
            print(f"❌ 查询失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print(f"   请确保服务运行在: {base_url}")
        print("   检查服务状态: curl http://localhost:8004/api/health")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 同时查询文档详情
    print()
    print("=" * 60)
    print("文档详情")
    print("=" * 60)
    
    try:
        doc_url = f"{base_url}/api/documents/{document_id}"
        response = requests.get(doc_url, timeout=5)
        
        if response.status_code == 200:
            doc = response.json()
            print(f"文件名: {doc.get('filename', 'unknown')}")
            print(f"状态: {doc.get('status', 'unknown')}")
            print(f"文件类型: {doc.get('file_type', 'unknown')}")
            print(f"文件大小: {doc.get('file_size', 0)} 字节")
            print(f"总块数: {doc.get('total_chunks', 0)}")
            
            uploaded_at = doc.get('uploaded_at')
            if uploaded_at:
                print(f"上传时间: {uploaded_at}")
            
            processed_at = doc.get('processed_at')
            if processed_at:
                print(f"处理完成时间: {processed_at}")
            else:
                print("处理完成时间: (处理中)")
        else:
            print(f"❌ 无法获取文档详情: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 查询文档详情失败: {str(e)}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_document_progress.py <document_id> [base_url]")
        print()
        print("示例:")
        print("  python check_document_progress.py abc-123-def-456")
        print("  python check_document_progress.py abc-123-def-456 http://localhost:8004")
        sys.exit(1)
    
    document_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8004"
    
    check_document_progress(document_id, base_url)


