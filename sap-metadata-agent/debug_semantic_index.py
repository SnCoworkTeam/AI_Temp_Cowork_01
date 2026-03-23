"""
调试语义索引构建问题
"""
import requests
import json

def test_step_by_step():
    """逐步测试语义索引构建流程"""
    print("=" * 80)
    print("调试语义索引构建问题")
    print("=" * 80)
    
    # 步骤1: 检查是否能从元数据服务加载数据
    print("\n步骤1: 检查从元数据服务加载数据")
    print("-" * 80)
    try:
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 5, "source_system": "SAP"},
            timeout=10
        )
        if response.status_code == 200:
            assets = response.json()
            count = len(assets) if isinstance(assets, list) else 0
            print(f"✓ 成功获取 {count} 个SAP资产")
            if count > 0:
                print(f"  示例: {assets[0].get('name', 'N/A')}")
            return count > 0
        else:
            print(f"✗ 获取失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False
    
    # 步骤2: 测试API调用（只构建语义索引，不发现新数据）
    print("\n步骤2: 测试语义索引构建API（limit=3）")
    print("-" * 80)
    try:
        response = requests.post(
            "http://localhost:8015/api/sap-metadata/discover",
            json={
                "include_database": False,
                "include_odata": False,
                "include_bapi": False,
                "build_semantic_index": True,
                "sync_to_metadata_service": False,
                "limit": 3  # 只处理3个用于测试
            },
            timeout=120
        )
        
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查返回的数据
            data_assets = result.get("data_assets", [])
            business_entities = result.get("business_entities", [])
            semantic_index = result.get("metadata", {}).get("semantic_index", {})
            
            print(f"✓ API调用成功")
            print(f"  返回的数据资产数: {len(data_assets)}")
            print(f"  返回的业务实体数: {len(business_entities)}")
            print(f"  语义索引结果: {semantic_index}")
            
            if len(data_assets) == 0:
                print(f"\n⚠️  问题: 没有加载任何数据资产")
                print(f"   可能原因:")
                print(f"   1. 元数据服务中没有SAP资产")
                print(f"   2. 资产加载逻辑有问题（检查orchestrator第93-126行）")
                print(f"   3. 资产转换失败")
            
            if semantic_index.get("indexed", 0) == 0 and semantic_index.get("failed", 0) == 0:
                print(f"\n⚠️  问题: 语义索引结果为空")
                print(f"   可能原因:")
                print(f"   1. 没有资产传递给语义索引构建器")
                print(f"   2. 语义索引构建器没有执行")
                print(f"   3. 构建过程中出现错误但被捕获")
            
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
        import traceback
        traceback.print_exc()
        return False


def check_orchestrator_logic():
    """检查编排器逻辑"""
    print("\n步骤3: 分析编排器逻辑")
    print("-" * 80)
    print("根据代码分析:")
    print("  1. 当 build_semantic_index=True 且 include_database=False 且 include_odata=False 时")
    print("     编排器会从元数据服务加载现有资产（第93行）")
    print("  2. 如果加载成功，资产会被传递给语义索引构建器（第287行）")
    print("  3. 语义索引构建器会为每个资产创建文档并存储到知识库")
    print("\n可能的问题:")
    print("  - 资产加载失败（metadata_client.list_data_assets返回空）")
    print("  - 资产转换失败（SAPDataAsset创建失败）")
    print("  - 知识库API调用失败")


if __name__ == "__main__":
    test_step_by_step()
    check_orchestrator_logic()
    
    print("\n" + "=" * 80)
    print("建议")
    print("=" * 80)
    print("1. 检查sap-metadata-agent服务的日志")
    print("2. 检查知识库服务是否正常")
    print("3. 使用分批处理方式构建语义索引")
    print("=" * 80)

