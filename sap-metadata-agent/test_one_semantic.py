"""
测试单条语义索引构建
用于验证语义索引功能是否正常工作，然后再进行分批构建
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any
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


async def test_one_semantic():
    """测试单条语义索引构建"""
    print("=" * 80)
    print("测试单条语义索引构建")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 初始化客户端
    metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    print(f"元数据服务: {metadata_service_url}")
    print(f"知识库服务: {knowledge_base_url}\n")
    
    metadata_client = MetadataClient(metadata_service_url=metadata_service_url)
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    try:
        # 步骤1: 获取一条数据资产
        print("步骤1: 获取一条SAP数据资产...")
        print("-" * 80)
        
        assets = await metadata_client.list_data_assets(
            limit=1,
            offset=0,
            source_system="SAP"
        )
        
        if not assets:
            print("❌ 未找到SAP数据资产")
            return False
        
        asset = assets[0]
        print(f"✅ 找到数据资产: {asset.get('name', 'unknown')}")
        print(f"   显示名称: {asset.get('display_name', 'N/A')}")
        print()
        
        # 步骤2: 转换为SAP格式
        print("步骤2: 转换为SAP格式...")
        print("-" * 80)
        
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
        
        print(f"✅ 转换完成")
        print()
        
        # 步骤3: 测试知识库连接
        print("步骤3: 测试知识库服务连接...")
        print("-" * 80)
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as test_client:
                health_url = f"{knowledge_base_url}/api/health"
                health_response = await test_client.get(health_url)
                if health_response.status_code == 200:
                    print(f"✅ 知识库服务连接正常")
                else:
                    print(f"⚠️  知识库服务响应异常: {health_response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ 无法连接到知识库服务: {e}")
            return False
        
        print()
        
        # 步骤4: 构建语义索引（单条）
        print("步骤4: 构建语义索引（单条测试）...")
        print("-" * 80)
        
        result = await semantic_builder.build_semantic_index(
            assets=[sap_asset],
            entities=[],
            processes=[]
        )
        
        indexed = result.get("indexed", 0)
        failed = result.get("failed", 0)
        
        print(f"\n结果:")
        print(f"  成功索引: {indexed}")
        print(f"  失败: {failed}")
        
        if indexed > 0:
            print(f"\n✅ 单条语义索引测试成功！")
            print(f"   可以继续进行分批构建")
            return True
        else:
            print(f"\n❌ 单条语义索引测试失败")
            print(f"   请检查知识库服务是否正常运行")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await semantic_builder.close()
        await metadata_client.close()


if __name__ == "__main__":
    try:
        success = asyncio.run(test_one_semantic())
        if success:
            print("\n" + "=" * 80)
            print("测试通过！现在可以运行分批构建:")
            print("  python build_semantic_batch.py --batch-size 10 --max-batches 5")
            print("=" * 80)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


