"""
测试单条语义分析生成
用于验证语义分析功能是否正常工作
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
from src.services.metadata_client import MetadataClient

# 配置日志 - 确保所有日志都输出
logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别以看到所有日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 确保输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# 设置httpx的日志级别
logging.getLogger("httpx").setLevel(logging.DEBUG)


async def test_single_semantic_analysis():
    """
    测试单条语义分析生成
    """
    print("=" * 80)
    print("测试单条语义分析生成")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 初始化客户端
    metadata_client = MetadataClient(
        metadata_service_url=os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")
    )
    
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    print(f"\n知识库服务URL: {knowledge_base_url}")
    print(f"如果使用Docker容器名，请确保设置正确的URL")
    print(f"例如: export KNOWLEDGE_BASE_URL=http://localhost:8004\n")
    
    # 创建语义索引构建器
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    # 打印实际使用的URL
    print(f"语义索引构建器使用的URL: {semantic_builder.knowledge_base_url}\n")
    
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
            print("❌ 未找到SAP数据资产，请先运行元数据发现")
            return False
        
        asset = assets[0]
        metadata = asset.get('metadata') or {}
        print(f"✅ 找到数据资产: {asset.get('name', 'unknown')}")
        print(f"   显示名称: {asset.get('display_name', 'N/A')}")
        print(f"   分类: {asset.get('classification', 'N/A')}")
        print(f"   业务术语: {metadata.get('business_terms', [])}")
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
        print(f"   SAP表名: {sap_asset.get('sap_table_name', 'N/A')}")
        print(f"   SAP模块: {sap_asset.get('sap_module', 'N/A')}")
        print(f"   业务术语数量: {len(sap_asset.get('business_terms', []))}")
        print()
        
        # 步骤3: 创建语义文档
        print("步骤3: 创建语义文档...")
        print("-" * 80)
        
        doc = await semantic_builder._create_semantic_document(sap_asset, "data_asset")
        
        print(f"✅ 语义文档创建成功")
        print(f"   文档ID: {doc.get('id')}")
        print(f"   文档类型: {doc.get('type')}")
        print(f"   文档标题: {doc.get('title')}")
        print(f"   文档内容长度: {len(doc.get('content', ''))} 字符")
        print()
        print("文档内容预览:")
        print("-" * 80)
        content_preview = doc.get('content', '')[:500]  # 只显示前500字符
        print(content_preview)
        if len(doc.get('content', '')) > 500:
            print("... (内容已截断)")
        print()
        
        # 步骤4: 测试知识库服务连接
        print("步骤4: 测试知识库服务连接...")
        print("-" * 80)
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as test_client:
                health_url = f"{knowledge_base_url}/api/health"
                print(f"测试连接: {health_url}")
                health_response = await test_client.get(health_url)
                print(f"健康检查响应: status={health_response.status_code}")
                if health_response.status_code == 200:
                    print(f"✅ 知识库服务连接正常")
                else:
                    print(f"⚠️  知识库服务响应异常: {health_response.text}")
        except Exception as e:
            print(f"❌ 无法连接到知识库服务: {e}")
            print(f"   请确认知识库服务是否运行在: {knowledge_base_url}")
            return False
        
        # 步骤5: 存储到知识库
        print()
        print("步骤5: 存储语义文档到知识库...")
        print("-" * 80)
        print(f"知识库URL: {knowledge_base_url}")
        print(f"请求URL: {knowledge_base_url}/api/documents/create")
        print(f"文档ID: {doc.get('id')}")
        print(f"文档标题: {doc.get('title')}")
        
        print(f"\n[DEBUG] 准备调用 _store_document...")
        print(f"[DEBUG] 文档ID: {doc.get('id')}")
        print(f"[DEBUG] 文档标题: {doc.get('title')}")
        print(f"[DEBUG] semantic_builder对象: {semantic_builder}")
        print(f"[DEBUG] knowledge_base_url: {semantic_builder.knowledge_base_url}")
        
        # 确保执行到这里
        print(f"[DEBUG] 即将调用 await semantic_builder._store_document(doc)")
        
        try:
            result = await semantic_builder._store_document(doc)
            print(f"\n[DEBUG] _store_document 返回结果: {result}")
        except Exception as e:
            print(f"\n[ERROR] _store_document 抛出异常: {e}")
            import traceback
            traceback.print_exc()
            result = False
        
        if result:
            print(f"✅ 语义文档存储成功！")
            print(f"   知识库URL: {knowledge_base_url}")
            print(f"   文档已索引，可用于语义搜索")
        else:
            print(f"❌ 语义文档存储失败")
            print(f"   请检查知识库服务是否正常运行: {knowledge_base_url}")
            return False
        
        # 步骤6: 使用build_semantic_index方法测试
        print()
        print("步骤6: 使用build_semantic_index方法测试...")
        print("-" * 80)
        
        result = await semantic_builder.build_semantic_index(
            assets=[sap_asset],
            entities=[],
            processes=[]
        )
        
        print(f"✅ 语义索引构建完成")
        print(f"   成功索引: {result.get('indexed', 0)}")
        print(f"   失败: {result.get('failed', 0)}")
        print(f"   总计: {result.get('total', 0)}")
        
        # 最终报告
        print()
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if result.get('indexed', 0) > 0:
            print("✅ 语义分析功能正常工作！")
            print()
            print("测试结果:")
            print(f"  - 数据资产获取: ✅")
            print(f"  - 格式转换: ✅")
            print(f"  - 语义文档创建: ✅")
            print(f"  - 文档存储: ✅")
            print(f"  - 索引构建: ✅")
            return True
        else:
            print("❌ 语义分析功能测试失败")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理资源
        await semantic_builder.close()
        await metadata_client.close()


if __name__ == "__main__":
    try:
        success = asyncio.run(test_single_semantic_analysis())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

