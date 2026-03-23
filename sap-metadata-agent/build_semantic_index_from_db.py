"""
从数据库中的现有SAP元数据构建语义索引
适用于元数据已存储在数据库中的情况
"""
import requests
import json
import sys
import os
from datetime import datetime
from typing import Optional

API_URL = "http://localhost:8015/api/sap-metadata/discover"
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")

def check_metadata_count() -> Optional[dict]:
    """检查数据库中的元数据数量"""
    print("=" * 60)
    print("检查数据库中的SAP元数据")
    print("=" * 60)
    
    try:
        # 检查数据资产数量
        assets_url = f"{METADATA_SERVICE_URL}/api/data-assets"
        params = {
            "source_system": "SAP",
            "limit": 1,
            "offset": 0
        }
        
        response = requests.get(assets_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 处理不同的响应格式
            if isinstance(data, dict):
                total_assets = data.get("total", len(data.get("data", [])))
            elif isinstance(data, list):
                total_assets = len(data)
            else:
                total_assets = 0
            print(f"✅ 数据资产总数: {total_assets:,}")
        else:
            print(f"⚠️  无法获取数据资产数量: {response.status_code}")
            total_assets = None
        
        # 检查业务实体数量
        entities_url = f"{METADATA_SERVICE_URL}/api/business-entities"
        params = {
            "limit": 1,
            "offset": 0
        }
        
        response = requests.get(entities_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 处理不同的响应格式
            if isinstance(data, dict):
                total_entities = data.get("total", len(data.get("data", [])))
            elif isinstance(data, list):
                total_entities = len(data)
            else:
                total_entities = 0
            print(f"✅ 业务实体总数: {total_entities:,}")
        else:
            print(f"⚠️  无法获取业务实体数量: {response.status_code}")
            total_entities = None
        
        return {
            "assets": total_assets,
            "entities": total_entities
        }
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到元数据服务: {METADATA_SERVICE_URL}")
        print("   请确保元数据服务正在运行")
        return None
    except Exception as e:
        print(f"❌ 检查元数据时出错: {e}")
        return None


def build_semantic_index_from_existing_metadata(knowledge_base_id: Optional[str] = None) -> bool:
    """
    从现有元数据构建语义索引
    
    Args:
        knowledge_base_id: 可选的知识库ID
    """
    print("\n" + "=" * 60)
    print("开始从现有SAP元数据构建语义索引")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if knowledge_base_id:
        print(f"目标知识库ID: {knowledge_base_id}")
    print()
    
    try:
        # 构建请求体：只构建语义索引，不发现新元数据
        body = {
            "include_database": False,  # 不从数据库发现（使用现有数据）
            "include_odata": False,     # 不从OData发现（使用现有数据）
            "include_bapi": False,      # 不发现BAPI
            "build_semantic_index": True,  # 构建语义索引
            "sync_to_metadata_service": False  # 不同步（数据已存在）
        }
        
        # 如果提供了知识库ID，添加到请求中
        if knowledge_base_id:
            body["knowledge_base_id"] = knowledge_base_id
        
        print("正在调用SAP元数据代理API...")
        print(f"   API URL: {API_URL}")
        print(f"   请求参数:")
        print(f"   - include_database: False (使用现有元数据)")
        print(f"   - include_odata: False (使用现有元数据)")
        print(f"   - build_semantic_index: True")
        if knowledge_base_id:
            print(f"   - knowledge_base_id: {knowledge_base_id}")
        print()
        
        print("开始构建语义索引（这可能需要较长时间，请耐心等待）...")
        print()
        
        # 发送请求（超时时间设置为1小时，因为数据量可能很大）
        response = requests.post(API_URL, json=body, timeout=3600)
        response.raise_for_status()
        
        result = response.json()
        index_result = result.get('metadata', {}).get('semantic_index', {})
        
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        total = index_result.get('total', 0)
        
        print("\n" + "=" * 60)
        print("语义索引构建完成")
        print("=" * 60)
        print(f"   索引成功: {indexed:,}")
        print(f"   索引失败: {failed:,}")
        print(f"   总计: {total:,}")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if indexed > 0:
            print(f"\n✅ 语义索引构建成功！")
            print(f"   已成功索引 {indexed:,} 个文档到知识库")
            if knowledge_base_id:
                print(f"   文档已关联到知识库: {knowledge_base_id}")
            return True
        else:
            print(f"\n⚠️  没有文档被索引")
            if failed > 0:
                print(f"   失败原因可能是:")
                print(f"   - 知识库服务连接问题")
                print(f"   - 文档处理失败")
                print(f"   - 元数据格式问题")
            else:
                print(f"   可能的原因:")
                print(f"   - 元数据服务中没有SAP元数据")
                print(f"   - 元数据格式不正确")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（超过1小时）")
        print(f"   数据量可能过大，建议分批处理")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 无法连接到SAP元数据代理服务: {API_URL}")
        print(f"   请确保服务正在运行")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP错误: {e.response.status_code}")
        if e.response.text:
            try:
                error_data = e.response.json()
                print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   响应内容: {e.response.text[:500]}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("从现有SAP元数据构建语义索引")
    print("=" * 60)
    print()
    
    # 检查元数据数量
    metadata_count = check_metadata_count()
    if metadata_count:
        total = (metadata_count.get("assets", 0) or 0) + (metadata_count.get("entities", 0) or 0)
        if total == 0:
            print("\n⚠️  数据库中没有SAP元数据")
            print("   请先执行元数据发现，然后再构建语义索引")
            return 1
        else:
            print(f"\n✅ 找到 {total:,} 条SAP元数据，准备构建语义索引")
    else:
        print("\n⚠️  无法检查元数据数量，但继续尝试构建...")
    
    # 检查是否提供了知识库ID
    knowledge_base_id = None
    if len(sys.argv) > 1:
        knowledge_base_id = sys.argv[1]
        print(f"\n使用指定的知识库ID: {knowledge_base_id}")
    
    # 构建语义索引
    print()
    success = build_semantic_index_from_existing_metadata(knowledge_base_id)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

