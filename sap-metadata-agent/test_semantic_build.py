"""
测试语义分析构建功能
使用默认参数测试少量数据，验证功能是否正常
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
from src.services.metadata_client import MetadataClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_semantic_build():
    """测试语义分析构建功能"""
    print("=" * 80)
    print("语义分析构建功能测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 检查环境变量
    metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    print("配置信息:")
    print(f"  元数据服务: {metadata_service_url}")
    print(f"  知识库服务: {knowledge_base_url}\n")
    
    # 步骤1: 检查服务连接
    print("步骤1: 检查服务连接...")
    print("-" * 80)
    
    import httpx
    
    # 检查元数据服务
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{metadata_service_url}/health")
            if response.status_code == 200:
                print(f"  ✅ 元数据服务连接正常")
            else:
                print(f"  ⚠️  元数据服务响应异常: {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ 元数据服务连接失败: {e}")
        print(f"     请确保元数据服务正在运行: {metadata_service_url}")
        return False
    
    # 检查知识库服务
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{knowledge_base_url}/api/health")
            if response.status_code == 200:
                print(f"  ✅ 知识库服务连接正常")
            else:
                print(f"  ⚠️  知识库服务响应异常: {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ 知识库服务连接失败: {e}")
        print(f"     请确保知识库服务正在运行: {knowledge_base_url}")
        return False
    
    print()
    
    # 步骤2: 获取测试数据
    print("步骤2: 获取测试数据...")
    print("-" * 80)
    
    metadata_client = MetadataClient(metadata_service_url=metadata_service_url)
    
    try:
        # 获取少量数据资产用于测试
        assets = await metadata_client.list_data_assets(
            limit=3,  # 只测试3个
            offset=0,
            source_system="SAP"
        )
        
        if not assets:
            print("  ⚠️  未找到SAP数据资产")
            print("     请先运行SAP元数据发现和构建")
            return False
        
        print(f"  ✅ 找到 {len(assets)} 个SAP数据资产用于测试")
        for i, asset in enumerate(assets, 1):
            print(f"     {i}. {asset.get('name', 'unknown')} - {asset.get('display_name', 'N/A')}")
        
    except Exception as e:
        print(f"  ❌ 获取数据资产失败: {e}")
        logger.error(f"获取数据资产失败: {e}", exc_info=True)
        return False
    
    print()
    
    # 步骤3: 测试语义索引构建
    print("步骤3: 测试语义索引构建...")
    print("-" * 80)
    
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    try:
        # 转换为SAP格式
        sap_assets = []
        for asset in assets:
            metadata = asset.get("metadata") or {}
            schema_info = asset.get("schema_info") or {}
            sap_asset = {
                "name": asset.get("name", ""),
                "display_name": asset.get("display_name", ""),
                "description": asset.get("description", ""),
                "asset_type": asset.get("asset_type", "table"),
                "sap_table_name": metadata.get("sap_table_name"),
                "sap_module": metadata.get("sap_module"),
                "odata_service": metadata.get("odata_service"),
                "odata_entity": metadata.get("odata_entity"),
                "schema_info": schema_info,
                "classification": asset.get("classification", ""),
                "tags": asset.get("tags", []),
                "business_terms": metadata.get("business_terms", []),
                "semantic_relationships": metadata.get("semantic_relationships", []),
                "metadata": metadata
            }
            sap_assets.append(sap_asset)
        
        print(f"  准备索引 {len(sap_assets)} 个数据资产...")
        
        # 构建语义索引
        result = await semantic_builder.build_semantic_index(
            assets=sap_assets,
            entities=[],
            processes=[]
        )
        
        indexed = result.get("indexed", 0)
        failed = result.get("failed", 0)
        
        print(f"  ✅ 测试完成")
        print(f"     成功索引: {indexed}")
        print(f"     失败: {failed}")
        
        if indexed > 0:
            print(f"\n  ✅ 语义索引构建功能正常！")
        else:
            print(f"\n  ⚠️  没有文档被成功索引，请检查知识库服务")
            return False
        
    except Exception as e:
        print(f"  ❌ 语义索引构建失败: {e}")
        logger.error(f"语义索引构建失败: {e}", exc_info=True)
        return False
    finally:
        await semantic_builder.close()
        await metadata_client.close()
    
    # 步骤4: 验证索引结果
    print()
    print("步骤4: 验证索引结果...")
    print("-" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 查询知识库中的SAP元数据文档
            response = await client.get(
                f"{knowledge_base_url}/api/documents",
                params={"category": "sap_metadata", "limit": 10}
            )
            
            if response.status_code == 200:
                docs = response.json()
                if isinstance(docs, dict) and "items" in docs:
                    docs = docs["items"]
                elif isinstance(docs, dict) and "data" in docs:
                    docs = docs["data"]
                
                sap_docs = [doc for doc in docs if doc.get("category") == "sap_metadata"]
                print(f"  ✅ 知识库中找到 {len(sap_docs)} 个SAP元数据文档")
                
                if len(sap_docs) > 0:
                    print(f"     示例文档:")
                    for doc in sap_docs[:3]:
                        print(f"       - {doc.get('title', 'N/A')}")
            else:
                print(f"  ⚠️  查询知识库失败: {response.status_code}")
                
    except Exception as e:
        print(f"  ⚠️  验证索引结果时出错: {e}")
        # 不影响测试结果
    
    # 最终报告
    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("✅ 测试通过！可以开始完整构建了")
    print()
    print("下一步:")
    print("  python build_semantic_analysis.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_semantic_build())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

