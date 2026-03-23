#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控F5业务蓝图报告文档处理进度
"""
import requests
import json
import time
import sys
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_URL = "http://43.143.139.197:8004"

def get_processing_documents(kb_id="46b77fb0-9d26-45af-aa7e-63c1ad5abf42"):
    """获取正在处理的文档"""
    try:
        response = requests.get(
            f"{SERVER_URL}/api/documents",
            params={"knowledge_base_id": kb_id},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            # 查找F5相关的文档
            f5_docs = [doc for doc in docs if 'F5' in doc.get('filename', '')]
            processing_docs = [doc for doc in docs if doc.get('status') == 'processing']
            return f5_docs, processing_docs
        return [], []
    except Exception as e:
        print(f"错误: {str(e)}")
        return [], []

def monitor_document_processing():
    """监控文档处理进度"""
    print("="*80)
    print("F5业务蓝图报告 - 文档处理监控")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    last_status = {}
    check_count = 0

    while True:
        check_count += 1
        print(f"\n[检查 #{check_count}] {datetime.now().strftime('%H:%M:%S')}")

        f5_docs, processing_docs = get_processing_documents()

        # 显示F5相关文档
        if f5_docs:
            print(f"\n找到 {len(f5_docs)} 个F5相关文档:")
            for doc in f5_docs:
                doc_id = doc.get('id')
                filename = doc.get('filename')
                status = doc.get('status')
                chunks = doc.get('total_chunks', 0)
                uploaded_at = doc.get('uploaded_at', '')

                status_icon = {
                    'processing': '⏳',
                    'processed': '✅',
                    'failed': '❌',
                    'pending': '⏸️'
                }.get(status, '❓')

                print(f"  {status_icon} {filename}")
                print(f"     ID: {doc_id[:8]}...")
                print(f"     状态: {status}")
                print(f"     块数: {chunks}")
                print(f"     上传时间: {uploaded_at[:19] if uploaded_at else 'N/A'}")

                # 检测状态变化
                if doc_id in last_status and last_status[doc_id] != status:
                    print(f"     ⚠️ 状态变化: {last_status[doc_id]} -> {status}")

                last_status[doc_id] = status
        else:
            print("  未找到F5相关文档")

        # 显示所有正在处理的文档
        if processing_docs:
            print(f"\n正在处理的文档总数: {len(processing_docs)}")
            for doc in processing_docs:
                if 'F5' not in doc.get('filename', ''):
                    print(f"  ⏳ {doc.get('filename')}")

        # 检查是否所有F5文档都处理完成
        f5_processing = [doc for doc in f5_docs if doc.get('status') == 'processing']
        f5_processed = [doc for doc in f5_docs if doc.get('status') == 'processed']
        f5_failed = [doc for doc in f5_docs if doc.get('status') == 'failed']

        if f5_docs and not f5_processing:
            print("\n" + "="*80)
            if f5_processed:
                print("✅ F5文档处理完成!")
                for doc in f5_processed:
                    print(f"   - {doc.get('filename')}: {doc.get('total_chunks')} 个块")
            if f5_failed:
                print("❌ F5文档处理失败:")
                for doc in f5_failed:
                    print(f"   - {doc.get('filename')}")
            print("="*80)
            break

        # 每5秒检查一次
        time.sleep(5)

if __name__ == "__main__":
    try:
        monitor_document_processing()
    except KeyboardInterrupt:
        print("\n\n监控已停止")
