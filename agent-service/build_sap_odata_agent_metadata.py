"""
构建 SAP OData 智能体元数据脚本
重启服务并触发元数据构建
"""
import asyncio
import sys
import os
import httpx
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root.parent / "shared_libs") not in sys.path:
    sys.path.insert(0, str(project_root.parent / "shared_libs"))
if str(project_root.parent / "database" / "src") not in sys.path:
    sys.path.insert(0, str(project_root.parent / "database" / "src"))

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8010")
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")


async def check_service_health(url: str, service_name: str, max_retries: int = 30, retry_delay: int = 2) -> bool:
    """检查服务健康状态"""
    print(f"\n检查 {service_name} 服务状态...")
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/v1/health")
                if response.status_code == 200:
                    print(f"✅ {service_name} 服务已就绪")
                    return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"   等待中... ({i+1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ {service_name} 服务未就绪: {e}")
                return False
    return False


async def trigger_metadata_build() -> dict:
    """触发 SAP OData 智能体元数据构建"""
    print("\n" + "="*80)
    print("触发 SAP OData 智能体元数据构建")
    print("="*80)
    
    try:
        # 方法1: 通过 API 触发（如果存在）
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 尝试调用智能体执行接口，触发元数据构建
            # 由于没有专门的构建接口，我们通过执行一个简单的发现任务来触发
            print("\n[方法1] 通过执行任务触发元数据构建...")
            
            # 获取 SAP OData 智能体实例并调用 build_metadata
            # 使用相对导入路径
            import sys
            import os
            # 确保可以导入 src 模块
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            from src.core.dynamic_execution_engine import DynamicExecutionEngine
            
            engine = DynamicExecutionEngine()
            await engine.initialize()
            
            if "sap_odata_agent" not in engine.agent_pool:
                print("❌ SAP OData 智能体未在智能体池中找到")
                return {"success": False, "error": "Agent not found"}
            
            sap_agent = engine.agent_pool["sap_odata_agent"]
            
            print(f"✅ 找到 SAP OData 智能体: {sap_agent.name}")
            print(f"   智能体ID: {sap_agent.agent_id}")
            
            # 检查元数据构建状态
            metadata_summary = sap_agent.get_metadata_summary()
            print(f"\n当前元数据状态:")
            print(f"   已构建: {metadata_summary.get('metadata_built', False)}")
            print(f"   正在构建: {metadata_summary.get('metadata_building', False)}")
            print(f"   服务数量: {metadata_summary.get('total_services', 0)}")
            print(f"   实体数量: {metadata_summary.get('total_entities', 0)}")
            
            # 如果未构建，开始构建
            if not metadata_summary.get('metadata_built', False):
                print("\n开始构建元数据...")
                print("注意: 首次构建可能需要较长时间，建议限制服务数量")
                
                # 首次构建限制为30个服务，避免超时
                result = await sap_agent.build_metadata(
                    force_rebuild=False,
                    limit_services=30
                )
                
                print(f"\n构建结果:")
                print(f"   状态: {result.get('status')}")
                print(f"   服务数量: {result.get('services_count', 0)}")
                print(f"   实体数量: {result.get('entities_count', 0)}")
                print(f"   消息: {result.get('message', '')}")
                
                if result.get('status') == 'success':
                    print("\n✅ 元数据构建成功！")
                    
                    # 获取更新后的摘要
                    updated_summary = sap_agent.get_metadata_summary()
                    print(f"\n更新后的元数据状态:")
                    print(f"   服务数量: {updated_summary.get('total_services', 0)}")
                    print(f"   实体数量: {updated_summary.get('total_entities', 0)}")
                    print(f"   关键词数量: {updated_summary.get('keywords_count', 0)}")
                    
                    return {
                        "success": True,
                        "result": result,
                        "summary": updated_summary
                    }
                else:
                    print(f"\n⚠️ 元数据构建未完成: {result.get('message', '')}")
                    return {
                        "success": False,
                        "result": result
                    }
            else:
                print("\n✅ 元数据已构建，跳过重复构建")
                print("如需重新构建，请使用 force_rebuild=True")
                
                return {
                    "success": True,
                    "message": "Metadata already built",
                    "summary": metadata_summary
                }
                
    except Exception as e:
        print(f"\n❌ 构建元数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def verify_metadata_in_service() -> bool:
    """验证智能体是否已注册到元数据服务"""
    print("\n" + "="*80)
    print("验证 SAP OData 智能体在元数据服务中的注册")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 检查 AI 模型
            print("\n[1] 检查 AI 模型注册...")
            response = await client.get(
                f"{METADATA_SERVICE_URL}/api/ai-models",
                params={"name": "agent_sap_odata_agent"}
            )
            
            if response.status_code == 200:
                models = response.json()
                if isinstance(models, list) and len(models) > 0:
                    model = models[0]
                    print(f"✅ 找到 AI 模型: {model.get('display_name', 'N/A')}")
                    print(f"   模型ID: {model.get('id', 'N/A')}")
                    print(f"   状态: {model.get('status', 'N/A')}")
                else:
                    print("⚠️ 未找到 AI 模型注册")
            else:
                print(f"⚠️ 查询 AI 模型失败: HTTP {response.status_code}")
            
            # 检查业务实体
            print("\n[2] 检查业务实体注册...")
            response = await client.get(
                f"{METADATA_SERVICE_URL}/api/business-entities",
                params={"name": "sap_odata_agent"}
            )
            
            if response.status_code == 200:
                entities = response.json()
                if isinstance(entities, list) and len(entities) > 0:
                    entity = entities[0]
                    print(f"✅ 找到业务实体: {entity.get('name', 'N/A')}")
                    print(f"   实体ID: {entity.get('id', 'N/A')}")
                else:
                    print("⚠️ 未找到业务实体注册")
            else:
                print(f"⚠️ 查询业务实体失败: HTTP {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"⚠️ 验证时出错: {e}")
        return False


async def main():
    """主函数"""
    print("="*80)
    print("SAP OData 智能体元数据构建脚本")
    print("="*80)
    print(f"Agent Service URL: {AGENT_SERVICE_URL}")
    print(f"Metadata Service URL: {METADATA_SERVICE_URL}")
    
    # 1. 检查服务健康状态
    print("\n[步骤 1/3] 检查服务健康状态...")
    agent_service_ok = await check_service_health(AGENT_SERVICE_URL, "Agent Service")
    metadata_service_ok = await check_service_health(METADATA_SERVICE_URL, "Metadata Service")
    
    if not agent_service_ok:
        print("\n❌ Agent Service 未就绪，请先启动服务")
        print("\n重启服务命令:")
        print("  docker-compose restart agent-service")
        print("  或")
        print("  docker-compose up -d agent-service")
        return
    
    # 2. 触发元数据构建
    print("\n[步骤 2/3] 触发元数据构建...")
    build_result = await trigger_metadata_build()
    
    if not build_result.get("success"):
        print("\n❌ 元数据构建失败")
        if "error" in build_result:
            print(f"   错误: {build_result['error']}")
        return
    
    # 3. 验证注册
    print("\n[步骤 3/3] 验证元数据服务注册...")
    await verify_metadata_in_service()
    
    print("\n" + "="*80)
    print("✅ 完成！")
    print("="*80)
    print("\n提示:")
    print("  - 如需构建更多服务的元数据，可以调用:")
    print("    await agent.build_metadata(force_rebuild=True, limit_services=100)")
    print("  - 查看元数据摘要:")
    print("    summary = agent.get_metadata_summary()")
    print("  - 获取服务元数据:")
    print("    metadata = await agent.get_service_metadata()")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

