"""
语义索引健康检查脚本
检查语义索引功能是否正常
"""
import requests
import sys
import os
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_knowledge_base_service() -> bool:
    """检查知识库服务是否运行"""
    print("=" * 60)
    print("检查1: 知识库服务状态")
    print("=" * 60)
    
    try:
        # 检查健康端点
        health_url = "http://localhost:8004/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 知识库服务运行正常: {health_url}")
            return True
        else:
            print(f"⚠️  知识库服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到知识库服务: http://localhost:8004")
        print("   请确保知识库服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 检查知识库服务时出错: {e}")
        return False


def check_document_create_api() -> bool:
    """检查文档创建API是否可用"""
    print("\n" + "=" * 60)
    print("检查2: 文档创建API端点")
    print("=" * 60)
    
    try:
        # 检查API端点是否存在
        api_url = "http://localhost:8004/api/documents/create"
        
        # 发送一个测试请求（不实际创建文档）
        test_data = {
            "title": "测试文档",
            "content": "这是一个测试文档",
            "category": "test",
            "process_async": False
        }
        
        response = requests.post(api_url, json=test_data, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"✅ 文档创建API可用: {api_url}")
            result = response.json()
            document_id = result.get('document_id')
            if document_id:
                print(f"   测试文档ID: {document_id}")
                # 清理测试文档
                delete_url = f"http://localhost:8004/api/documents/{document_id}"
                try:
                    requests.delete(delete_url, timeout=5)
                    print(f"   已清理测试文档")
                except:
                    pass
            return True
        elif response.status_code == 404:
            print(f"❌ 文档创建API端点不存在: {api_url}")
            print("   请检查知识库服务路由配置")
            return False
        else:
            print(f"⚠️  文档创建API响应异常: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到知识库服务API: {api_url}")
        return False
    except Exception as e:
        print(f"❌ 检查文档创建API时出错: {e}")
        return False


def check_sap_metadata_agent() -> bool:
    """检查SAP元数据代理服务是否运行"""
    print("\n" + "=" * 60)
    print("检查3: SAP元数据代理服务状态")
    print("=" * 60)
    
    try:
        health_url = "http://localhost:8015/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ SAP元数据代理服务运行正常: {health_url}")
            return True
        else:
            print(f"⚠️  SAP元数据代理服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到SAP元数据代理服务: http://localhost:8015")
        print("   请确保SAP元数据代理服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 检查SAP元数据代理服务时出错: {e}")
        return False


def check_semantic_index_builder() -> bool:
    """检查语义索引构建器实现"""
    print("\n" + "=" * 60)
    print("检查4: 语义索引构建器实现")
    print("=" * 60)
    
    try:
        from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
        
        # 检查类是否存在
        if SAPSemanticIndexBuilder:
            print("✅ 语义索引构建器类存在")
            
            # 检查关键方法
            required_methods = [
                'build_semantic_index',
                '_create_semantic_document',
                '_store_document'
            ]
            
            all_methods_exist = True
            for method_name in required_methods:
                if hasattr(SAPSemanticIndexBuilder, method_name):
                    print(f"   ✅ 方法存在: {method_name}")
                else:
                    print(f"   ❌ 方法缺失: {method_name}")
                    all_methods_exist = False
            
            # 检查初始化
            try:
                builder = SAPSemanticIndexBuilder()
                print(f"   ✅ 可以初始化构建器")
                print(f"   知识库URL: {builder.knowledge_base_url}")
                
                # 清理
                import asyncio
                asyncio.run(builder.close())
                
                return all_methods_exist
            except Exception as e:
                print(f"   ❌ 初始化构建器失败: {e}")
                return False
        else:
            print("❌ 语义索引构建器类不存在")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入语义索引构建器: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查语义索引构建器时出错: {e}")
        return False


def check_environment_variables() -> bool:
    """检查环境变量配置"""
    print("\n" + "=" * 60)
    print("检查5: 环境变量配置")
    print("=" * 60)
    
    kb_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    print(f"   KNOWLEDGE_BASE_URL: {kb_url}")
    
    # 检查其他可能需要的环境变量
    env_vars = {
        "KNOWLEDGE_BASE_URL": kb_url,
    }
    
    all_ok = True
    for key, value in env_vars.items():
        if value:
            print(f"   ✅ {key}: {value}")
        else:
            print(f"   ⚠️  {key}: 未设置（使用默认值）")
    
    return all_ok


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("语义索引健康检查")
    print("=" * 60)
    print()
    
    checks = [
        ("知识库服务", check_knowledge_base_service),
        ("文档创建API", check_document_create_api),
        ("SAP元数据代理服务", check_sap_metadata_agent),
        ("语义索引构建器", check_semantic_index_builder),
        ("环境变量", check_environment_variables),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 检查 {name} 时发生异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n✅ 所有检查通过，语义索引功能正常！")
        return 0
    else:
        print("\n⚠️  部分检查失败，请修复问题后再执行语义索引构建")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


