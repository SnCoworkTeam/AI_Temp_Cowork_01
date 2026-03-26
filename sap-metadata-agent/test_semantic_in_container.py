"""
在容器内测试语义分析
这个脚本可以在Docker容器内运行，直接测试知识库服务连接
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import httpx

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
from src.services.metadata_client import MetadataClient

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 在容器内，使用服务名而不是localhost
CONTAINER_KB_URL = "http://knowledge-base:8004"
LOCAL_KB_URL = "http://localhost:8004"


async def test_in_container():
    """
    在容器内测试语义分析
    """
    print("=" * 80)
    print("容器内语义分析测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 检测是否在容器内
    in_container = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "true"
    print(f"运行环境: {'Docker容器' if in_container else '本地环境'}")
    
    # 选择URL
    if in_container:
        knowledge_base_url = CONTAINER_KB_URL
        metadata_service_url = "http://metadata-service:8005"
    else:
        knowledge_base_url = LOCAL_KB_URL
        metadata_service_url = "http://localhost:8005"
    
    print(f"知识库URL: {knowledge_base_url}")
    print(f"元数据服务URL: {metadata_service_url}\n")
    
    # 初始化客户端
    metadata_client = MetadataClient(metadata_service_url=metadata_service_url)
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    try:
        # 步骤1: 测试知识库服务连接
        print("步骤1: 测试知识库服务连接...")
        print("-" * 80)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试根路径
            try:
                root_url = f"{knowledge_base_url}/"
                print(f"  测试根路径: {root_url}")
                response = await client.get(root_url)
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"  ✅ 根路径可访问")
                    print(f"  响应: {response.json()}")
            except Exception as e:
                print(f"  ❌ 根路径测试失败: {e}")
                return False
            
            # 测试健康检查
            try:
                health_url = f"{knowledge_base_url}/api/health"
                print(f"\n  测试健康检查: {health_url}")
                response = await client.get(health_url)
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"  ✅ 健康检查成功")
                    health_data = response.json()
                    print(f"  服务状态: {health_data.get('status', 'unknown')}")
                else:
                    print(f"  ⚠️  状态码异常: {response.text[:200]}")
                    return False
            except Exception as e:
                print(f"  ❌ 健康检查失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # 步骤2: 获取一条数据资产
        print("\n步骤2: 获取一条SAP数据资产...")
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
        metadata = asset.get("metadata") or {}
        schema_info = asset.get("schema_info") or {}
        
        print(f"✅ 找到数据资产: {asset.get('name', 'unknown')}")
        print(f"   显示名称: {asset.get('display_name', 'N/A')}")
        print(f"   分类: {asset.get('classification', 'N/A')}")
        
        # 步骤3: 转换为SAP格式
        print("\n步骤3: 转换为SAP格式...")
        print("-" * 80)
        
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
        print(f"   业务术语数量: {len(sap_asset.get('business_terms', []))}")
        
        # 步骤4: 创建语义文档
        print("\n步骤4: 创建语义文档...")
        print("-" * 80)
        
        doc = await semantic_builder._create_semantic_document(sap_asset, "data_asset")
        
        print(f"✅ 语义文档创建成功")
        print(f"   文档ID: {doc.get('id')}")
        print(f"   文档标题: {doc.get('title')}")
        print(f"   内容长度: {len(doc.get('content', ''))} 字符")
        
        # 步骤5: 直接测试HTTP请求
        print("\n步骤5: 直接测试HTTP请求到知识库...")
        print("-" * 80)
        
        request_data = {
            "title": doc.get('title', 'Untitled'),
            "content": doc.get('content', ''),
            "category": "sap_metadata",
            "tags": doc.get('metadata', {}).get('tags', []),
            "metadata": doc.get('metadata', {}),
            "process_async": False
        }
        
        create_url = f"{knowledge_base_url}/api/documents/create"
        print(f"请求URL: {create_url}")
        print(f"请求数据: title={request_data['title']}, content_length={len(request_data['content'])}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                print(f"\n发送POST请求...")
                response = await client.post(create_url, json=request_data)
                print(f"响应状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 文档创建成功！")
                    print(f"   文档ID: {result.get('document_id', 'unknown')}")
                    print(f"   状态: {result.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ 文档创建失败")
                    print(f"   状态码: {response.status_code}")
                    print(f"   响应内容: {response.text[:500]}")
                    return False
            except httpx.ConnectError as e:
                print(f"❌ 连接错误: {e}")
                print(f"   请检查:")
                print(f"   1. 知识库服务是否运行")
                print(f"   2. URL是否正确: {create_url}")
                print(f"   3. 网络连接是否正常")
                import traceback
                traceback.print_exc()
                return False
            except httpx.TimeoutException:
                print(f"❌ 请求超时")
                print(f"   知识库服务可能正在处理，但响应太慢")
                return False
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                import traceback
                traceback.print_exc()
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
        success = asyncio.run(test_in_container())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

