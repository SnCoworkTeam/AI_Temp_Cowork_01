"""
检查语义索引构建状态
"""
import requests
import json
from datetime import datetime

def check_metadata_service():
    """检查元数据服务中的数据资产数量"""
    print("=" * 80)
    print("1. 检查元数据服务中的SAP数据资产")
    print("=" * 80)
    
    try:
        # 获取总数
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 1, "source_system": "SAP"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                total = len(data)
            else:
                # 尝试获取总数
                response2 = requests.get(
                    "http://localhost:8005/api/data-assets",
                    params={"limit": 1000, "source_system": "SAP"},
                    timeout=10
                )
                if response2.status_code == 200:
                    data2 = response2.json()
                    total = len(data2) if isinstance(data2, list) else 0
                else:
                    total = 0
        else:
            total = 0
        
        print(f"✓ 元数据服务响应正常")
        print(f"  找到的SAP数据资产: {total} (可能更多)")
        
        # 获取一些示例
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 5, "source_system": "SAP"},
            timeout=10
        )
        if response.status_code == 200:
            assets = response.json()
            if isinstance(assets, list) and len(assets) > 0:
                print(f"  示例资产:")
                for i, asset in enumerate(assets[:3], 1):
                    print(f"    {i}. {asset.get('name', 'N/A')}")
        
        return total
    except Exception as e:
        print(f"✗ 检查元数据服务失败: {e}")
        return 0


def check_knowledge_base():
    """检查知识库中的文档数量"""
    print("\n" + "=" * 80)
    print("2. 检查知识库中的文档")
    print("=" * 80)
    
    try:
        # 获取文档列表
        response = requests.get(
            "http://localhost:8004/api/documents",
            params={"page": 1, "page_size": 100},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            documents = data.get("documents", [])
            
            print(f"✓ 知识库响应正常")
            print(f"  总文档数: {total}")
            
            # 统计SAP元数据相关的文档
            sap_docs = [d for d in documents if "sap_metadata" in d.get("category", "").lower() or 
                       any("sap" in tag.lower() for tag in d.get("tags", []))]
            
            print(f"  SAP元数据相关文档: {len(sap_docs)}")
            
            # 显示一些示例
            if sap_docs:
                print(f"  示例文档:")
                for i, doc in enumerate(sap_docs[:5], 1):
                    status = doc.get("status", "unknown")
                    title = doc.get("filename", doc.get("metadata", {}).get("title", "N/A"))
                    print(f"    {i}. {title} (状态: {status})")
            
            # 统计不同状态的文档
            statuses = {}
            for doc in documents:
                status = doc.get("status", "unknown")
                statuses[status] = statuses.get(status, 0) + 1
            
            if statuses:
                print(f"  文档状态统计:")
                for status, count in statuses.items():
                    print(f"    {status}: {count}")
            
            return total, len(sap_docs)
        else:
            print(f"✗ 知识库响应错误: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return 0, 0
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到知识库服务 (http://localhost:8004)")
        print(f"  请确保知识库服务正在运行")
        return 0, 0
    except Exception as e:
        print(f"✗ 检查知识库失败: {e}")
        return 0, 0


def check_semantic_index_api():
    """检查语义索引API状态"""
    print("\n" + "=" * 80)
    print("3. 检查语义索引构建API")
    print("=" * 80)
    
    try:
        # 尝试调用API（短超时，只检查是否响应）
        response = requests.post(
            "http://localhost:8015/api/sap-metadata/discover",
            json={
                "include_database": False,
                "include_odata": False,
                "include_bapi": False,
                "build_semantic_index": True,
                "sync_to_metadata_service": False,
                "limit": 10  # 只处理少量数据用于测试
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            semantic_index = result.get("metadata", {}).get("semantic_index", {})
            indexed = semantic_index.get("indexed", 0)
            failed = semantic_index.get("failed", 0)
            
            print(f"✓ API响应正常")
            print(f"  最近一次索引结果:")
            print(f"    成功: {indexed}")
            print(f"    失败: {failed}")
            
            return indexed, failed
        else:
            print(f"✗ API响应错误: {response.status_code}")
            print(f"  响应: {response.text[:500]}")
            return 0, 0
    except requests.exceptions.Timeout:
        print(f"⚠ API调用超时（可能正在处理大量数据）")
        return None, None
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到SAP元数据代理服务 (http://localhost:8015)")
        print(f"  请确保服务正在运行")
        return None, None
    except Exception as e:
        print(f"✗ 检查API失败: {e}")
        return None, None


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("语义索引构建状态检查")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 检查元数据服务
    metadata_count = check_metadata_service()
    
    # 2. 检查知识库
    kb_total, kb_sap = check_knowledge_base()
    
    # 3. 检查API状态
    api_indexed, api_failed = check_semantic_index_api()
    
    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"元数据服务中的SAP资产: {metadata_count}")
    print(f"知识库总文档数: {kb_total}")
    print(f"知识库中SAP相关文档: {kb_sap}")
    
    if api_indexed is not None:
        print(f"最近API索引成功: {api_indexed}")
        print(f"最近API索引失败: {api_failed}")
    
    # 计算进度
    if metadata_count > 0 and kb_sap > 0:
        progress = (kb_sap / metadata_count) * 100
        print(f"\n索引进度: {kb_sap}/{metadata_count} ({progress:.1f}%)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断检查")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

