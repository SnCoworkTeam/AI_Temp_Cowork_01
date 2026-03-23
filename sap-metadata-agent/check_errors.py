"""
检查语义索引构建的错误
"""
import requests
import json

def check_knowledge_base_errors():
    """检查知识库中的错误文档"""
    try:
        response = requests.get(
            "http://localhost:8004/api/documents",
            params={"page": 1, "page_size": 1000},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            failed_docs = [d for d in documents if d.get("status") == "failed"]
            
            if failed_docs:
                print(f"找到 {len(failed_docs)} 个失败的文档:")
                for doc in failed_docs[:10]:
                    print(f"  - {doc.get('filename', 'N/A')} (ID: {doc.get('id', 'N/A')})")
                    # 尝试获取详细错误信息
                    try:
                        detail_response = requests.get(
                            f"http://localhost:8004/api/documents/{doc.get('id')}",
                            timeout=5
                        )
                        if detail_response.status_code == 200:
                            detail = detail_response.json()
                            print(f"    状态: {detail.get('status', 'N/A')}")
                    except:
                        pass
            else:
                print("没有找到失败的文档")
            
            return failed_docs
        else:
            print(f"无法获取文档列表: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"检查失败: {e}")
        return []


def test_small_batch():
    """测试小批量构建"""
    print("\n测试小批量语义索引构建...")
    try:
        response = requests.post(
            "http://localhost:8015/api/sap-metadata/discover",
            json={
                "include_database": False,
                "include_odata": False,
                "include_bapi": False,
                "build_semantic_index": True,
                "sync_to_metadata_service": False,
                "limit": 3
            },
            timeout=120
        )
        
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            semantic_index = result.get("metadata", {}).get("semantic_index", {})
            data_assets = result.get("data_assets", [])
            
            print(f"✓ API调用成功")
            print(f"  加载的资产数: {len(data_assets)}")
            print(f"  索引成功: {semantic_index.get('indexed', 0)}")
            print(f"  索引失败: {semantic_index.get('failed', 0)}")
            
            if len(data_assets) == 0:
                print(f"\n⚠️  警告: 没有加载任何资产")
                print(f"   可能原因:")
                print(f"   1. 元数据服务中没有SAP资产")
                print(f"   2. 资产加载逻辑有问题")
            
            return True
        else:
            print(f"✗ API调用失败: HTTP {response.status_code}")
            print(f"  响应: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"✗ 请求超时（可能正在处理大量数据）")
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("检查语义索引错误")
    print("=" * 80)
    
    print("\n1. 检查知识库中的失败文档")
    print("-" * 80)
    failed = check_knowledge_base_errors()
    
    print("\n2. 测试小批量构建")
    print("-" * 80)
    test_small_batch()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

