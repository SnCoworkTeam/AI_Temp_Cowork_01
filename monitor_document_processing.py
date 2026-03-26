#!/usr/bin/env python3
"""
实时监控文档处理进度和性能
"""
import asyncio
import httpx
import time
import subprocess
import sys
from datetime import datetime

API_BASE = "http://43.143.139.197:8080"
DOCUMENT_PATH = "test_document_performance.md"

async def monitor_document_processing(doc_id):
    """实时监控文档处理"""
    print("\n" + "="*80)
    print("📊 文档处理实时监控")
    print("="*80)

    start_time = time.time()
    last_status = None
    memory_readings = []

    async with httpx.AsyncClient(timeout=300.0) as client:
        for i in range(120):  # 最多监控10分钟（每5秒检查一次）
            await asyncio.sleep(5)
            elapsed = time.time() - start_time

            try:
                # 获取文档状态
                response = await client.get(f"{API_BASE}/api/knowledge/documents/{doc_id}")
                if response.status_code == 200:
                    doc = response.json()
                    status = doc.get('status')
                    chunks = doc.get('total_chunks', 0)

                    # 获取内存使用（通过SSH）
                    memory_cmd = f"docker stats --no-stream --format '{{{{.MemUsage}}}}' enterprise-ai-knowledge-base"
                    result = subprocess.run(
                        ["ssh", "-i", "enterprise_ai_platform.pem", "-o", "StrictHostKeyChecking=no",
                         "ubuntu@43.143.139.197", memory_cmd],
                        capture_output=True, text=True, timeout=10
                    )
                    memory = result.stdout.strip() if result.returncode == 0 else "N/A"
                    memory_readings.append({"time": elapsed, "memory": memory, "status": status})

                    if status != last_status:
                        print(f"\n[{elapsed:.1f}s] 状态变化: {last_status} → {status}")
                        last_status = status

                    print(f"[{elapsed:.1f}s] 状态: {status} | Chunks: {chunks} | 内存: {memory}")

                    if status == "processed":
                        print("\n✅ 文档处理完成!")
                        print(f"   总耗时: {elapsed:.1f}秒")
                        print(f"   总Chunks: {chunks}")
                        print(f"   最终内存: {memory}")
                        return True
                    elif status == "failed":
                        print("\n❌ 文档处理失败!")
                        return False

            except Exception as e:
                print(f"[{elapsed:.1f}s] 监控错误: {str(e)}")

        print("\n⚠️  监控超时（10分钟）")
        return False

async def upload_and_monitor():
    """上传文档并监控处理过程"""
    print("="*80)
    print("🧪 知识库文档处理性能测试")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"文档: {DOCUMENT_PATH}")
    print()

    # 1. 检查文档
    import os
    if not os.path.exists(DOCUMENT_PATH):
        print(f"❌ 测试文档不存在: {DOCUMENT_PATH}")
        return

    file_size = os.path.getsize(DOCUMENT_PATH)
    print(f"📄 文档大小: {file_size / 1024:.2f} KB")

    # 2. 获取初始内存
    print("\n💾 获取初始内存状态...")
    memory_cmd = "docker stats --no-stream --format 'table {{.Name}}\\t{{.MemUsage}}\\t{{.CPUPerc}}' enterprise-ai-knowledge-base"
    result = subprocess.run(
        ["ssh", "-i", "enterprise_ai_platform.pem", "-o", "StrictHostKeyChecking=no",
         "ubuntu@43.143.139.197", memory_cmd],
        capture_output=True, text=True, timeout=10
    )
    print(result.stdout)

    # 3. 上传文档
    print("\n📤 上传文档...")
    upload_start = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            with open(DOCUMENT_PATH, 'rb') as f:
                files = {'file': (os.path.basename(DOCUMENT_PATH), f, 'text/markdown')}
                data = {'process_async': 'false'}  # 同步处理以便监控

                response = await client.post(
                    f"{API_BASE}/api/knowledge/documents/upload",
                    files=files,
                    data=data
                )

                upload_time = time.time() - upload_start

                if response.status_code == 200:
                    result = response.json()
                    doc_id = result.get('document_id')
                    print(f"✅ 上传成功! (耗时: {upload_time:.2f}秒)")
                    print(f"   文档ID: {doc_id}")
                    print(f"   状态: {result.get('status')}")

                    # 4. 开始监控处理过程
                    print("\n⏳ 开始监控文档处理...")
                    await monitor_document_processing(doc_id)

                else:
                    print(f"❌ 上传失败: {response.status_code}")
                    print(f"   响应: {response.text}")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(upload_and_monitor())
