"""
执行SAP元数据语义索引构建
"""
import requests
import json
import sys
import os
from datetime import datetime
from typing import Optional

API_URL = "http://localhost:8015/api/sap-metadata/discover"
KNOWLEDGE_BASE_URL = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")

def check_services() -> bool:
    """检查服务是否运行"""
    print("=" * 60)
    print("检查服务状态")
    print("=" * 60)
    
    # 检查知识库服务
    try:
        response = requests.get(f"{KNOWLEDGE_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 知识库服务运行正常: {KNOWLEDGE_BASE_URL}")
        else:
            print(f"⚠️  知识库服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 知识库服务未运行或无法访问: {KNOWLEDGE_BASE_URL}")
        print(f"   错误: {e}")
        return False
    
    # 检查SAP元数据代理服务
    try:
        response = requests.get("http://localhost:8015/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ SAP元数据代理服务运行正常: http://localhost:8015")
        else:
            print(f"⚠️  SAP元数据代理服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SAP元数据代理服务未运行或无法访问: http://localhost:8015")
        print(f"   错误: {e}")
        return False
    
    return True


def build_semantic_index(knowledge_base_id: Optional[str] = None) -> bool:
    """
    构建语义索引
    
    Args:
        knowledge_base_id: 可选的知识库ID，用于将文档关联到指定知识库
    """
    print("\n" + "=" * 60)
    print("开始构建SAP元数据语义索引")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if knowledge_base_id:
        print(f"目标知识库ID: {knowledge_base_id}")
    print()
    
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False
        }
        
        # 如果提供了知识库ID，添加到请求中
        if knowledge_base_id:
            body["knowledge_base_id"] = knowledge_base_id
        
        print("正在调用SAP元数据代理API...")
        print(f"   API URL: {API_URL}")
        print(f"   请求参数: {json.dumps(body, indent=2, ensure_ascii=False)}")
        print()
        
        response = requests.post(API_URL, json=body, timeout=1800)  # 30分钟超时
        response.raise_for_status()
        
        result = response.json()
        index_result = result.get('metadata', {}).get('semantic_index', {})
        
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        total = index_result.get('total', 0)
        
        print("\n" + "=" * 60)
        print("语义索引构建完成")
        print("=" * 60)
        print(f"   索引成功: {indexed}")
        print(f"   索引失败: {failed}")
        print(f"   总计: {total}")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if indexed > 0:
            print(f"\n✅ 语义索引构建成功！")
            print(f"   已成功索引 {indexed} 个文档到知识库")
            if knowledge_base_id:
                print(f"   文档已关联到知识库: {knowledge_base_id}")
            return True
        else:
            print(f"\n⚠️  没有文档被索引")
            if failed > 0:
                print(f"   可能的原因:")
                print(f"   - 没有可用的SAP元数据")
                print(f"   - 知识库服务连接问题")
                print(f"   - 文档处理失败")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（超过30分钟）")
        print(f"   这可能是由于数据量过大或服务响应慢")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 无法连接到SAP元数据代理服务: {API_URL}")
        print(f"   请确保服务正在运行")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP错误: {e.response.status_code}")
        if e.response.text:
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
    print("SAP元数据语义索引构建工具")
    print("=" * 60)
    print()
    
    # 检查服务（非阻塞，仅警告）
    services_ok = check_services()
    if not services_ok:
        print("\n⚠️  服务检查失败，但继续尝试构建...")
        print("   如果构建失败，请确保以下服务正在运行:")
        print("   1. 知识库服务 (http://localhost:8004)")
        print("   2. SAP元数据代理服务 (http://localhost:8015)")
        print()
    
    # 检查是否提供了知识库ID
    knowledge_base_id = None
    if len(sys.argv) > 1:
        knowledge_base_id = sys.argv[1]
        print(f"\n使用指定的知识库ID: {knowledge_base_id}")
    
    # 构建语义索引
    success = build_semantic_index(knowledge_base_id)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

