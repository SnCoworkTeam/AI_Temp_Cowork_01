"""
测试F5业务蓝图文档处理 - 带内存优化
"""
import asyncio
import httpx
import os
import sys
import time
from pathlib import Path

# API配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002")
DOCUMENT_PATH = "F5业务蓝图报告_TJJ_SD_V1.1.docx"


async def upload_and_process_document():
    """上传并处理F5文档"""
    print("=" * 80)
    print("F5业务蓝图文档处理测试 - 带内存优化")
    print("=" * 80)
    print()

    # 检查文件是否存在
    if not os.path.exists(DOCUMENT_PATH):
        print(f"❌ 错误: 文件不存在: {DOCUMENT_PATH}")
        return

    file_size_mb = os.path.getsize(DOCUMENT_PATH) / 1024 / 1024
    print(f"📄 文档信息:")
    print(f"   文件名: {DOCUMENT_PATH}")
    print(f"   大小: {file_size_mb:.2f} MB")
    print()

    async with httpx.AsyncClient(timeout=600.0) as client:
        # 1. 上传文档
        print("📤 步骤 1: 上传文档...")
        upload_start = time.time()

        with open(DOCUMENT_PATH, "rb") as f:
            files = {"file": (os.path.basename(DOCUMENT_PATH), f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {
                "process_async": "false",  # 同步处理以便监控
            }

            try:
                response = await client.post(
                    f"{API_BASE_URL}/api/knowledge-base/documents/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                result = response.json()

                upload_time = time.time() - upload_start
                print(f"✅ 文档上传成功!")
                print(f"   文档ID: {result.get('document_id')}")
                print(f"   状态: {result.get('status')}")
                print(f"   耗时: {upload_time:.2f}秒")
                print()

                document_id = result.get('document_id')

                # 2. 等待处理完成并监控进度
                print("⏳ 步骤 2: 处理文档并监控内存使用...")
                process_start = time.time()

                max_wait = 600  # 最多等待10分钟
                check_interval = 5  # 每5秒检查一次

                for i in range(max_wait // check_interval):
                    await asyncio.sleep(check_interval)

                    # 获取文档状态
                    status_response = await client.get(
                        f"{API_BASE_URL}/api/knowledge-base/documents/{document_id}"
                    )

                    if status_response.status_code == 200:
                        doc_info = status_response.json()
                        status = doc_info.get('status')

                        elapsed = (i + 1) * check_interval
                        print(f"   [{elapsed}s] 状态: {status}")

                        if status == "processed":
                            process_time = time.time() - process_start
                            print()
                            print("✅ 文档处理完成!")
                            print(f"   耗时: {process_time:.2f}秒")
                            print(f"   总块数: {doc_info.get('total_chunks', 0)}")
                            print()

                            # 3. 显示文档详情
                            print("📊 文档详情:")
                            print(f"   文件名: {doc_info.get('filename')}")
                            print(f"   文件类型: {doc_info.get('file_type')}")
                            print(f"   文件大小: {doc_info.get('file_size')} bytes")
                            print(f"   分块数量: {doc_info.get('total_chunks')}")
                            print(f"   质量评分: {doc_info.get('quality_score', 'N/A')}")

                            metadata = doc_info.get('metadata', {})
                            if metadata:
                                print(f"   元数据:")
                                for key, value in metadata.items():
                                    if key not in ['quality_details', 'custom_metadata']:
                                        print(f"     - {key}: {value}")

                            break

                        elif status == "failed":
                            print()
                            print("❌ 文档处理失败!")
                            break

                else:
                    print()
                    print("⚠️  处理超时!")

                # 4. 测试搜索功能
                print()
                print("🔍 步骤 3: 测试搜索功能...")
                search_queries = [
                    "业务流程",
                    "销售订单",
                    "系统架构"
                ]

                for query in search_queries:
                    search_response = await client.post(
                        f"{API_BASE_URL}/api/knowledge-base/search",
                        json={
                            "query": query,
                            "top_k": 3,
                            "threshold": 0.5
                        }
                    )

                    if search_response.status_code == 200:
                        search_results = search_response.json()
                        results = search_results.get('results', [])
                        print(f"   查询: '{query}' - 找到 {len(results)} 个结果")

                        if results:
                            top_result = results[0]
                            print(f"     最相关结果 (相似度: {top_result.get('score', 0):.4f}):")
                            content = top_result.get('content', '')[:100]
                            print(f"     {content}...")

                print()
                print("=" * 80)
                print("测试完成!")
                print("=" * 80)

            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP错误: {e.response.status_code}")
                print(f"   响应: {e.response.text}")
            except Exception as e:
                print(f"❌ 错误: {str(e)}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(upload_and_process_document())
