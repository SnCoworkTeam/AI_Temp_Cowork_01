#!/usr/bin/env python3
"""
服务器端F5文档处理测试 - 带内存监控
在服务器上运行此脚本来测试内存优化效果
"""
import asyncio
import httpx
import os
import sys
import time
import json
import subprocess

# API配置
API_BASE_URL = "http://localhost:8004"
DOCUMENT_PATH = "/tmp/F5_document.docx"

def get_memory_info():
    """获取内存信息"""
    try:
        # 获取容器内存使用
        result = subprocess.run([
            "docker", "stats", "--no-stream", "--format",
            "{{.MemUsage}}", "enterprise-ai-knowledge-base"
        ], capture_output=True, text=True, check=True)
        container_memory = result.stdout.strip()

        # 获取系统内存
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()

        total_kb = 0
        available_kb = 0
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                total_kb = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                available_kb = int(line.split()[1])

        total_gb = total_kb / 1024 / 1024
        available_gb = available_kb / 1024 / 1024
        used_gb = total_gb - available_gb

        return {
            "container_memory": container_memory,
            "system_total_gb": total_gb,
            "system_used_gb": used_gb,
            "system_available_gb": available_gb
        }
    except Exception as e:
        return {"error": str(e)}

async def test_f5_document_processing():
    """测试F5文档处理"""
    print("=" * 80)
    print("F5文档处理测试 - 内存优化版本")
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

    # 获取初始内存状态
    initial_memory = get_memory_info()
    print("💾 初始内存状态:")
    print(f"   容器内存: {initial_memory.get('container_memory', 'N/A')}")
    print(f"   系统内存: {initial_memory.get('system_used_gb', 0):.2f}GB / {initial_memory.get('system_total_gb', 0):.2f}GB")
    print()

    async with httpx.AsyncClient(timeout=600.0) as client:
        # 1. 上传文档
        print("📤 步骤 1: 上传文档...")
        upload_start = time.time()

        with open(DOCUMENT_PATH, "rb") as f:
            files = {"file": ("F5_document.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {
                "process_async": "false",  # 同步处理
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

                # 2. 监控处理过程
                print("⏳ 步骤 2: 监控文档处理...")
                process_start = time.time()

                max_wait = 600  # 最多等待10分钟
                check_interval = 10  # 每10秒检查一次

                memory_readings = []

                for i in range(max_wait // check_interval):
                    await asyncio.sleep(check_interval)

                    # 获取当前内存状态
                    current_memory = get_memory_info()
                    memory_readings.append(current_memory)

                    # 获取文档状态
                    try:
                        status_response = await client.get(
                            f"{API_BASE_URL}/api/knowledge-base/documents/{document_id}"
                        )

                        if status_response.status_code == 200:
                            doc_info = status_response.json()
                            status = doc_info.get('status')

                            elapsed = (i + 1) * check_interval
                            container_mem = current_memory.get('container_memory', 'N/A')
                            system_mem = current_memory.get('system_used_gb', 0)

                            print(f"   [{elapsed}s] 状态: {status} | 容器: {container_mem} | 系统: {system_mem:.2f}GB")

                            if status == "processed":
                                process_time = time.time() - process_start
                                print()
                                print("✅ 文档处理完成!")
                                print(f"   耗时: {process_time:.2f}秒")
                                print(f"   总块数: {doc_info.get('total_chunks', 0)}")

                                # 显示最终内存状态
                                final_memory = get_memory_info()
                                print()
                                print("📊 内存使用分析:")
                                print(f"   初始容器内存: {initial_memory.get('container_memory', 'N/A')}")
                                print(f"   最终容器内存: {final_memory.get('container_memory', 'N/A')}")
                                print(f"   初始系统内存: {initial_memory.get('system_used_gb', 0):.2f}GB")
                                print(f"   最终系统内存: {final_memory.get('system_used_gb', 0):.2f}GB")
                                print()

                                # 显示文档详情
                                print("📋 文档详情:")
                                print(f"   文件名: {doc_info.get('filename')}")
                                print(f"   文件类型: {doc_info.get('file_type')}")
                                print(f"   文件大小: {doc_info.get('file_size')} bytes")
                                print(f"   分块数量: {doc_info.get('total_chunks')}")
                                print(f"   质量评分: {doc_info.get('quality_score', 'N/A')}")

                                metadata = doc_info.get('metadata', {})
                                if metadata:
                                    print(f"   元数据keys: {list(metadata.keys())}")

                                break

                            elif status == "failed":
                                print()
                                print("❌ 文档处理失败!")
                                break

                    except Exception as e:
                        print(f"   [{(i + 1) * check_interval}s] 检查状态时出错: {str(e)}")

                else:
                    print()
                    print("⚠️  处理超时!")

                # 3. 测试搜索功能
                if document_id:
                    print()
                    print("🔍 步骤 3: 测试搜索功能...")
                    search_queries = [
                        "业务流程",
                        "销售订单",
                        "系统架构"
                    ]

                    for query in search_queries:
                        try:
                            search_response = await client.post(
                                f"{API_BASE_URL}/api/knowledge-base/search",
                                json={
                                    "query": query,
                                    "top_k": 3,
                                    "threshold": 0.3
                                }
                            )

                            if search_response.status_code == 200:
                                search_results = search_response.json()
                                results = search_results.get('results', [])
                                print(f"   查询: '{query}' - 找到 {len(results)} 个结果")

                                if results:
                                    top_result = results[0]
                                    score = top_result.get('score', 0)
                                    content = top_result.get('content', '')[:100]
                                    print(f"     最相关结果 (相似度: {score:.4f}): {content}...")
                            else:
                                print(f"   查询 '{query}' 失败: {search_response.status_code}")
                        except Exception as e:
                            print(f"   查询 '{query}' 出错: {str(e)}")

                # 保存内存监控数据
                with open('/tmp/memory_monitoring.json', 'w') as f:
                    json.dump(memory_readings, f, indent=2)
                print()
                print("📝 内存监控数据已保存到: /tmp/memory_monitoring.json")

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
    asyncio.run(test_f5_document_processing())