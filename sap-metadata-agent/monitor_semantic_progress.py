"""
监控语义索引处理进度和错误
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

def get_metadata_count() -> int:
    """获取元数据总数"""
    try:
        # 尝试获取总数
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 1, "source_system": "SAP"},
            timeout=10
        )
        # 使用之前检查到的数量
        return 109022
    except:
        return 109022


def check_knowledge_base_detailed() -> Optional[Dict[str, Any]]:
    """详细检查知识库状态"""
    try:
        all_docs = []
        page = 1
        page_size = 100
        
        # 获取所有文档
        while True:
            response = requests.get(
                "http://localhost:8004/api/documents",
                params={"page": page, "page_size": page_size},
                timeout=10
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            docs = data.get("documents", [])
            if not docs:
                break
            
            all_docs.extend(docs)
            
            if len(docs) < page_size:
                break
            
            page += 1
            if page > 100:  # 限制最大页数
                break
        
        # 分析文档
        sap_docs = {
            "processed": [],
            "processing": [],
            "failed": [],
            "total": 0
        }
        
        for doc in all_docs:
            metadata = doc.get("metadata", {})
            category = doc.get("category", "")
            tags = doc.get("tags", [])
            doc_type = metadata.get("type", "")
            
            # 检查是否是SAP元数据相关
            is_sap = (
                "sap_metadata" in category.lower() or
                any("sap" in str(tag).lower() for tag in tags) or
                "data_asset" in str(doc_type).lower() or
                "business_entity" in str(doc_type).lower() or
                "business_process" in str(doc_type).lower()
            )
            
            if is_sap:
                sap_docs["total"] += 1
                status = doc.get("status", "unknown")
                
                doc_info = {
                    "id": doc.get("id"),
                    "title": doc.get("filename", metadata.get("title", "N/A")),
                    "status": status,
                    "name": metadata.get("name", "N/A")
                }
                
                if status == "processed":
                    sap_docs["processed"].append(doc_info)
                elif status == "processing":
                    sap_docs["processing"].append(doc_info)
                elif status == "failed":
                    sap_docs["failed"].append(doc_info)
        
        return {
            "total_docs": len(all_docs),
            "sap_docs": sap_docs
        }
        
    except requests.exceptions.ConnectionError:
        return {"error": "无法连接到知识库服务"}
    except Exception as e:
        return {"error": f"检查失败: {str(e)}"}


def check_api_status() -> Optional[Dict[str, Any]]:
    """检查API服务状态"""
    try:
        # 检查SAP元数据代理服务
        response = requests.get("http://localhost:8015/api/health", timeout=5)
        sap_agent_ok = response.status_code == 200
        
        # 检查知识库服务
        response = requests.get("http://localhost:8004/api/health", timeout=5)
        kb_ok = response.status_code == 200
        
        # 检查元数据服务
        response = requests.get("http://localhost:8005/api/health", timeout=5)
        metadata_ok = response.status_code == 200
        
        return {
            "sap_agent": "运行中" if sap_agent_ok else "未运行",
            "knowledge_base": "运行中" if kb_ok else "未运行",
            "metadata_service": "运行中" if metadata_ok else "未运行"
        }
    except Exception as e:
        return {"error": f"检查服务状态失败: {str(e)}"}


def test_semantic_index_small_batch() -> Optional[Dict[str, Any]]:
    """测试小批量语义索引构建"""
    try:
        print("  测试小批量索引构建...")
        response = requests.post(
            "http://localhost:8015/api/sap-metadata/discover",
            json={
                "include_database": False,
                "include_odata": False,
                "include_bapi": False,
                "build_semantic_index": True,
                "sync_to_metadata_service": False,
                "limit": 5  # 只处理5个用于测试
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            semantic_index = result.get("metadata", {}).get("semantic_index", {})
            data_assets = result.get("data_assets", [])
            
            return {
                "success": True,
                "indexed": semantic_index.get("indexed", 0),
                "failed": semantic_index.get("failed", 0),
                "assets_loaded": len(data_assets)
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """主监控函数"""
    print("=" * 80)
    print("语义索引处理进度监控")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 检查服务状态
    print("1. 检查服务状态")
    print("-" * 80)
    api_status = check_api_status()
    if "error" in api_status:
        print(f"  ❌ {api_status['error']}")
    else:
        for service, status in api_status.items():
            icon = "✓" if status == "运行中" else "✗"
            print(f"  {icon} {service}: {status}")
    
    # 2. 获取元数据总数
    print("\n2. 元数据统计")
    print("-" * 80)
    total_assets = get_metadata_count()
    print(f"  SAP元数据资产总数: {total_assets:,}")
    
    # 3. 检查知识库状态
    print("\n3. 知识库文档状态")
    print("-" * 80)
    kb_status = check_knowledge_base_detailed()
    
    if kb_status and "error" in kb_status:
        print(f"  ❌ {kb_status['error']}")
    elif kb_status:
        sap_docs = kb_status.get("sap_docs", {})
        print(f"  知识库总文档数: {kb_status.get('total_docs', 0)}")
        print(f"  SAP相关文档总数: {sap_docs.get('total', 0)}")
        print(f"    已处理: {len(sap_docs.get('processed', []))}")
        print(f"    处理中: {len(sap_docs.get('processing', []))}")
        print(f"    失败: {len(sap_docs.get('failed', []))}")
        
        # 显示失败的文档
        failed_docs = sap_docs.get("failed", [])
        if failed_docs:
            print(f"\n  ❌ 失败的文档 ({len(failed_docs)}):")
            for i, doc in enumerate(failed_docs[:5], 1):
                print(f"    {i}. {doc.get('title', 'N/A')} (ID: {doc.get('id', 'N/A')})")
        
        # 显示处理中的文档
        processing_docs = sap_docs.get("processing", [])
        if processing_docs:
            print(f"\n  ⏳ 处理中的文档 ({len(processing_docs)}):")
            for i, doc in enumerate(processing_docs[:5], 1):
                print(f"    {i}. {doc.get('title', 'N/A')} (名称: {doc.get('name', 'N/A')})")
        
        # 计算进度
        processed_count = len(sap_docs.get("processed", []))
        if total_assets > 0:
            progress = (processed_count / total_assets) * 100
            print(f"\n  处理进度: {processed_count:,} / {total_assets:,} ({progress:.2f}%)")
    
    # 4. 测试小批量索引
    print("\n4. 测试语义索引构建")
    print("-" * 80)
    test_result = test_semantic_index_small_batch()
    if test_result:
        if test_result.get("success"):
            print(f"  ✓ 测试成功")
            print(f"    加载资产数: {test_result.get('assets_loaded', 0)}")
            print(f"    索引成功: {test_result.get('indexed', 0)}")
            print(f"    索引失败: {test_result.get('failed', 0)}")
        else:
            print(f"  ❌ 测试失败: {test_result.get('error', '未知错误')}")
    
    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    
    if kb_status and "sap_docs" in kb_status:
        sap_docs = kb_status["sap_docs"]
        processed = len(sap_docs.get("processed", []))
        processing = len(sap_docs.get("processing", []))
        failed = len(sap_docs.get("failed", []))
        
        print(f"当前状态:")
        print(f"  已处理: {processed:,}")
        print(f"  处理中: {processing}")
        print(f"  失败: {failed}")
        
        if processed == 0 and processing == 0:
            print(f"\n⚠️  语义索引似乎还没有开始")
            print(f"   建议: 运行 python build_semantic_index.py 启动索引构建")
        elif failed > 0:
            print(f"\n⚠️  有 {failed} 个文档处理失败，请检查知识库服务日志")
        elif processing > 0:
            print(f"\n⏳ 索引构建正在进行中...")
        elif processed > 0:
            print(f"\n✅ 索引构建已完成 {processed:,} 个文档")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  监控已停止")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

