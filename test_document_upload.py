#!/usr/bin/env python3
"""
测试文档上传和处理过程
功能：上传f5业务蓝图报告，监控处理过程，查看日志
"""

import requests
import time
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8004/api"
TEST_FILE = "F5业务蓝图报告_TJJ_SD_V1.1.docx"
TIMEOUT = 30

def check_service():
    """检查知识库服务是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 知识库服务正在运行")
            return True
        else:
            print(f"✗ 知识库服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到知识库服务，请确保服务已启动")
        print("  启动命令: docker-compose up -d knowledge-base")
        return False
    except Exception as e:
        print(f"✗ 检查服务时出错: {str(e)}")
        return False

def check_file():
    """检查测试文件是否存在"""
    if not Path(TEST_FILE).exists():
        print(f"✗ 测试文件不存在: {TEST_FILE}")
        return False
    
    file_size = Path(TEST_FILE).stat().st_size / (1024 * 1024)  # MB
    print(f"✓ 找到测试文件: {TEST_FILE} (大小: {file_size:.2f} MB)")
    return True

def upload_document():
    """上传文档"""
    print(f"\n正在上传文档: {TEST_FILE}")
    
    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'process_async': 'true'
            }
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data,
                timeout=TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get('document_id')
                status = result.get('status')
                
                print(f"✓ 文档上传成功")
                print(f"  文档ID: {document_id}")
                print(f"  初始状态: {status}")
                return document_id
            else:
                print(f"✗ 上传失败: {response.status_code}")
                print(f"  响应: {response.text}")
                return None
                
    except Exception as e:
        print(f"✗ 上传时出错: {str(e)}")
        return None

def get_document_status(document_id):
    """获取文档状态"""
    try:
        response = requests.get(f"{BASE_URL}/documents/{document_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  获取状态失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"  查询状态时出错: {str(e)}")
        return None

def monitor_processing(document_id, max_wait_time=600):
    """监控文档处理过程"""
    print(f"\n开始监控文档处理过程（最多等待{max_wait_time}秒）...")
    print("按Ctrl+C可提前退出")
    print("-" * 60)
    
    start_time = time.time()
    last_status = None
    check_interval = 5
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_time:
                print(f"\n⚠ 已达到最大等待时间（{max_wait_time}秒），停止监控")
                break
            
            doc_info = get_document_status(document_id)
            if not doc_info:
                print(f"  [等待中] 无法获取文档状态... ({int(elapsed)}秒)")
                time.sleep(check_interval)
                continue
            
            current_status = doc_info.get('status', 'unknown')
            chunk_count = doc_info.get('total_chunks', 0)
            error_message = doc_info.get('error_message')
            
            if current_status != last_status:
                print(f"  [状态变化] {last_status or 'N/A'} -> {current_status} (块数: {chunk_count}, 耗时: {int(elapsed)}秒)")
                last_status = current_status
            else:
                print(f"  [监控中] 状态: {current_status}, 块数: {chunk_count}, 耗时: {int(elapsed)}秒", end='\r')
            
            # 检查是否完成
            if current_status == 'completed':
                print(f"\n\n✓ 文档处理完成！")
                print(f"  最终状态: {current_status}")
                print(f"  总块数: {chunk_count}")
                print(f"  总耗时: {elapsed:.2f}秒")
                return True
            elif current_status == 'failed':
                print(f"\n\n✗ 文档处理失败！")
                print(f"  状态: {current_status}")
                if error_message:
                    print(f"  错误信息: {error_message}")
                return False
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\n\n用户中断监控")
        doc_info = get_document_status(document_id)
        if doc_info:
            print(f"当前状态: {doc_info.get('status', 'unknown')}")
            print(f"当前块数: {doc_info.get('total_chunks', 0)}")
        return False

def show_recent_logs(lines=50):
    """显示最近的服务日志"""
    print(f"\n{'='*60}")
    print("知识库服务最新日志（最近50行）")
    print('='*60)
    
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'logs', 'enterprise-ai-knowledge-base', '--tail', str(lines)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("无法获取日志（可能需要手动执行: docker logs enterprise-ai-knowledge-base --tail 50）")
    except Exception as e:
        print(f"获取日志时出错: {str(e)}")
        print("请手动执行: docker logs enterprise-ai-knowledge-base --tail 50")

def main():
    print("="*60)
    print("知识库文档上传测试")
    print("="*60)
    
    # 1. 检查服务
    print("\n1. 检查知识库服务...")
    if not check_service():
        sys.exit(1)
    
    # 2. 检查文件
    print("\n2. 检查测试文件...")
    if not check_file():
        sys.exit(1)
    
    # 3. 上传文档
    print("\n3. 上传文档...")
    document_id = upload_document()
    if not document_id:
        sys.exit(1)
    
    # 4. 监控处理
    print("\n4. 监控处理过程...")
    success = monitor_processing(document_id)
    
    # 5. 显示日志
    show_recent_logs()
    
    if success:
        print("\n" + "="*60)
        print("测试完成！文档处理成功")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("测试完成，但文档处理可能未完成或失败")
        print("请查看上面的日志了解详情")
        print("="*60)

if __name__ == "__main__":
    main()

