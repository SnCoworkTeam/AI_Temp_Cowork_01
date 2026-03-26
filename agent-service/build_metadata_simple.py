"""
简化版 SAP OData 智能体元数据构建脚本
直接通过 API 调用构建元数据
"""
import asyncio
import httpx
import json
import os
import sys

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8010")


async def check_service_health(url: str, max_retries: int = 30) -> bool:
    """检查服务健康状态"""
    print(f"检查服务状态: {url}")
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/api/v1/health")
                if response.status_code == 200:
                    print("✅ 服务已就绪")
                    return True
        except Exception:
            if i < max_retries - 1:
                print(f"   等待中... ({i+1}/{max_retries})")
                await asyncio.sleep(2)
    print("❌ 服务未就绪")
    return False


async def build_metadata_via_api():
    """通过 API 触发元数据构建"""
    print("\n" + "="*80)
    print("通过 API 触发 SAP OData 智能体元数据构建")
    print("="*80)
    
    # 检查服务
    if not await check_service_health(AGENT_SERVICE_URL):
        print("\n❌ Agent Service 未就绪，请先启动服务")
        return
    
    # 通过执行一个任务来触发元数据构建
    # 智能体会在首次使用时自动构建元数据
    print("\n通过执行任务触发元数据构建...")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 执行一个简单的发现任务
            task = "查询可用的SAP服务"
            
            print(f"执行任务: {task}")
            
            response = await client.post(
                f"{AGENT_SERVICE_URL}/api/v1/dynamic-workflow/execute",
                json={
                    "user_input": task,
                    "context": {}
                }
            )
            
            if response.status_code == 200:
                print("✅ 任务执行成功")
                result = response.json()
                print(f"执行结果摘要: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
            else:
                print(f"⚠️ 任务执行返回: HTTP {response.status_code}")
                print(f"响应: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def build_metadata_direct():
    """直接构建元数据（需要能够导入模块）"""
    print("\n" + "="*80)
    print("直接构建 SAP OData 智能体元数据")
    print("="*80)
    
    try:
        # 添加路径
        import os
        import sys
        from pathlib import Path
        
        current_dir = Path(__file__).resolve().parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # 尝试导入
        try:
            from src.core.dynamic_execution_engine import DynamicExecutionEngine
        except ImportError:
            print("❌ 无法导入模块，请使用 API 方式构建")
            return
        
        print("✅ 模块导入成功")
        
        # 初始化引擎
        print("\n初始化执行引擎...")
        engine = DynamicExecutionEngine()
        await engine.initialize()
        print("✅ 执行引擎初始化完成")
        
        # 获取 SAP OData 智能体
        if "sap_odata_agent" not in engine.agent_pool:
            print("❌ SAP OData 智能体未找到")
            print(f"可用的智能体: {list(engine.agent_pool.keys())}")
            return
        
        sap_agent = engine.agent_pool["sap_odata_agent"]
        print(f"✅ 找到 SAP OData 智能体: {sap_agent.name}")
        
        # 检查元数据状态
        if hasattr(sap_agent, 'get_metadata_summary'):
            summary = sap_agent.get_metadata_summary()
            print(f"\n当前元数据状态:")
            print(f"   已构建: {summary.get('metadata_built', False)}")
            print(f"   服务数量: {summary.get('total_services', 0)}")
            print(f"   实体数量: {summary.get('total_entities', 0)}")
            
            # 如果未构建，开始构建
            if not summary.get('metadata_built', False):
                print("\n开始构建元数据（限制30个服务）...")
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
                    
                    # 显示更新后的状态
                    updated_summary = sap_agent.get_metadata_summary()
                    print(f"\n更新后的状态:")
                    print(f"   服务数量: {updated_summary.get('total_services', 0)}")
                    print(f"   实体数量: {updated_summary.get('total_entities', 0)}")
                    print(f"   关键词数量: {updated_summary.get('keywords_count', 0)}")
                else:
                    print(f"\n⚠️ 构建未完成: {result.get('message', '')}")
            else:
                print("\n✅ 元数据已构建")
                
                # 显示一些服务信息
                if hasattr(sap_agent, 'get_service_metadata'):
                    metadata = await sap_agent.get_service_metadata()
                    services = metadata.get('services', [])
                    if services:
                        print(f"\n前5个服务:")
                        for service in services[:5]:
                            print(f"   - {service.get('service_name', 'N/A')}: {service.get('entities_count', 0)} 个实体")
        
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("="*80)
    print("SAP OData 智能体元数据构建")
    print("="*80)
    
    # 先尝试直接构建
    await build_metadata_direct()
    
    # 如果直接构建失败，尝试通过 API
    # await build_metadata_via_api()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

