"""
检查SAP OData智能体是否已注册到元数据服务
"""
import asyncio
import sys
import os
from pathlib import Path

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "shared_libs") not in sys.path:
    sys.path.insert(0, str(project_root / "shared_libs"))

from src.core.dynamic_execution_engine import DynamicExecutionEngine


async def check_sap_odata_metadata():
    """检查SAP OData智能体元数据注册情况"""
    print("="*80)
    print("检查SAP OData智能体元数据注册情况")
    print("="*80)
    
    # 1. 检查智能体池
    print("\n[1/3] 检查智能体池...")
    engine = DynamicExecutionEngine()
    agent_pool = engine.agent_pool
    
    if "sap_odata_agent" in agent_pool:
        print("✅ SAP OData智能体已在智能体池中")
        sap_agent = agent_pool["sap_odata_agent"]
        print(f"   智能体名称: {sap_agent.name}")
        print(f"   智能体描述: {sap_agent.description}")
        print(f"   智能体能力: {list(sap_agent.capabilities.keys())}")
    else:
        print("❌ SAP OData智能体不在智能体池中")
        print("   智能体池中的智能体:")
        for agent_id in agent_pool.keys():
            print(f"     - {agent_id}")
        return
    
    # 2. 初始化引擎（触发注册）
    print("\n[2/3] 初始化执行引擎（触发智能体注册）...")
    try:
        await engine.initialize()
        print("✅ 执行引擎初始化完成")
        
        # 检查注册表
        registered_agents = await engine.agent_registry.list_agents()
        sap_registered = False
        for agent in registered_agents:
            if agent.agent_id == "sap_odata_agent":
                sap_registered = True
                print(f"✅ SAP OData智能体已注册到本地注册表")
                print(f"   智能体ID: {agent.agent_id}")
                print(f"   智能体名称: {agent.name}")
                break
        
        if not sap_registered:
            print("⚠️ SAP OData智能体未在本地注册表中找到")
            print(f"   已注册的智能体数量: {len(registered_agents)}")
            for agent in registered_agents:
                print(f"     - {agent.agent_id}: {agent.name}")
    except Exception as e:
        print(f"⚠️ 初始化时出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 检查metadata-service
    print("\n[3/3] 检查metadata-service...")
    try:
        from src.services.metadata_client import metadata_client
        import httpx
        
        base_url = metadata_client.base_url
        print(f"   Metadata Service URL: {base_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 搜索AI模型
            print("\n   搜索AI模型...")
            response = await client.get(
                f"{base_url}/api/ai-models",
                params={"search": "sap_odata", "limit": 20}
            )
            
            if response.status_code == 200:
                models = response.json()
                if isinstance(models, list):
                    sap_models = [
                        m for m in models 
                        if isinstance(m, dict) and 
                        (m.get("metadata", {}).get("agent_id") == "sap_odata_agent" or
                         "sap" in m.get("name", "").lower() and "odata" in m.get("name", "").lower())
                    ]
                    
                    if sap_models:
                        print(f"   ✅ 找到 {len(sap_models)} 个SAP OData相关的AI模型:")
                        for model in sap_models:
                            print(f"      - ID: {model.get('id')}")
                            print(f"        名称: {model.get('display_name')}")
                            print(f"        状态: {model.get('status')}")
                            print(f"        Agent ID: {model.get('metadata', {}).get('agent_id', 'N/A')}")
                    else:
                        print("   ⚠️ 未找到SAP OData相关的AI模型")
                        print(f"   总共找到 {len(models)} 个AI模型")
                else:
                    print(f"   ⚠️ 响应格式不是列表: {type(models)}")
            else:
                print(f"   ⚠️ 请求失败: {response.status_code} - {response.text[:200]}")
            
            # 搜索业务实体
            print("\n   搜索业务实体...")
            response = await client.get(
                f"{base_url}/api/business-entities",
                params={"search": "sap_odata", "limit": 20}
            )
            
            if response.status_code == 200:
                entities = response.json()
                if isinstance(entities, list):
                    sap_entities = [
                        e for e in entities 
                        if isinstance(e, dict) and 
                        (e.get("metadata", {}).get("agent_id") == "sap_odata_agent" or
                         "sap" in e.get("name", "").lower() and "odata" in e.get("name", "").lower())
                    ]
                    
                    if sap_entities:
                        print(f"   ✅ 找到 {len(sap_entities)} 个SAP OData相关的业务实体:")
                        for entity in sap_entities:
                            print(f"      - ID: {entity.get('id')}")
                            print(f"        名称: {entity.get('display_name')}")
                            print(f"        类型: {entity.get('entity_type')}")
                            print(f"        Agent ID: {entity.get('metadata', {}).get('agent_id', 'N/A')}")
                    else:
                        print("   ⚠️ 未找到SAP OData相关的业务实体")
                        print(f"   总共找到 {len(entities)} 个业务实体")
                else:
                    print(f"   ⚠️ 响应格式不是列表: {type(entities)}")
            else:
                print(f"   ⚠️ 请求失败: {response.status_code} - {response.text[:200]}")
                
    except ImportError:
        print("   ⚠️ metadata_client不可用，跳过metadata-service检查")
    except Exception as e:
        print(f"   ⚠️ 检查metadata-service时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("检查完成")
    print("="*80)
    
    print("\n💡 总结:")
    print("  - SAP OData智能体已在智能体池中")
    print("  - 在服务启动时，会通过engine.initialize()自动注册到:")
    print("    1. 本地AgentRegistry（智能体注册表）")
    print("    2. Metadata Service（作为AI模型和业务实体）")
    print("  - 如果metadata-service中找不到，可能是:")
    print("    1. 服务还未启动")
    print("    2. metadata-service连接失败")
    print("    3. 注册过程中出现错误（检查日志）")


if __name__ == "__main__":
    asyncio.run(check_sap_odata_metadata())

