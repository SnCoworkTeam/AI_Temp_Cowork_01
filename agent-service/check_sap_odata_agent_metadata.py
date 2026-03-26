"""
检查SAP OData智能体是否已注册到元数据服务
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "shared_libs") not in sys.path:
    sys.path.insert(0, str(project_root / "shared_libs"))

from src.core.dynamic_execution_engine import DynamicExecutionEngine
from src.core.agents.sap_odata_agent import SAPODataAgent


async def check_sap_odata_agent_metadata():
    """检查SAP OData智能体元数据注册情况"""
    print("="*80)
    print("检查SAP OData智能体元数据注册情况")
    print("="*80)
    
    # 1. 检查智能体池
    print("\n[1/4] 检查智能体池...")
    engine = DynamicExecutionEngine()
    agent_pool = engine.agent_pool
    
    if "sap_odata_agent" in agent_pool:
        print("✅ SAP OData智能体已在智能体池中")
        sap_agent = agent_pool["sap_odata_agent"]
        print(f"   智能体名称: {sap_agent.name}")
        print(f"   智能体描述: {sap_agent.description}")
        print(f"   智能体能力: {sap_agent.capabilities}")
    else:
        print("❌ SAP OData智能体不在智能体池中")
        print("   智能体池中的智能体:")
        for agent_id in agent_pool.keys():
            print(f"     - {agent_id}")
        return
    
    # 2. 检查智能体注册表
    print("\n[2/4] 检查智能体注册表...")
    try:
        await engine.initialize()  # 这会触发_register_agents_to_registry
        print("✅ 执行引擎初始化完成")
        
        # 检查注册表
        registered_agents = await engine.agent_registry.list_agents()
        sap_registered = False
        for agent in registered_agents:
            if agent.agent_id == "sap_odata_agent":
                sap_registered = True
                print(f"✅ SAP OData智能体已注册到注册表")
                print(f"   智能体ID: {agent.agent_id}")
                print(f"   智能体名称: {agent.name}")
                break
        
        if not sap_registered:
            print("⚠️ SAP OData智能体未在注册表中找到")
            print(f"   已注册的智能体数量: {len(registered_agents)}")
            for agent in registered_agents:
                print(f"     - {agent.agent_id}: {agent.name}")
    except Exception as e:
        print(f"⚠️ 检查注册表时出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 检查metadata-service（如果可用）
    print("\n[3/4] 检查metadata-service...")
    try:
        from src.services.metadata_client import metadata_client
        
        # 搜索SAP OData智能体作为AI模型
        import httpx
        base_url = metadata_client.base_url
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 搜索AI模型
            response = await client.get(
                f"{base_url}/api/ai-models",
                params={"search": "sap_odata_agent", "limit": 10}
            )
            
            if response.status_code == 200:
                models = response.json()
                sap_model = None
                for model in models:
                    if isinstance(model, dict) and model.get("metadata", {}).get("agent_id") == "sap_odata_agent":
                        sap_model = model
                        break
                
                if sap_model:
                    print("✅ SAP OData智能体已注册为AI模型")
                    print(f"   模型ID: {sap_model.get('id')}")
                    print(f"   模型名称: {sap_model.get('display_name')}")
                    print(f"   状态: {sap_model.get('status')}")
                else:
                    print("⚠️ SAP OData智能体未在AI模型中找到")
            
            # 搜索业务实体
            response = await client.get(
                f"{base_url}/api/business-entities",
                params={"search": "sap_odata_agent", "limit": 10}
            )
            
            if response.status_code == 200:
                entities = response.json()
                sap_entity = None
                for entity in entities:
                    if isinstance(entity, dict) and entity.get("metadata", {}).get("agent_id") == "sap_odata_agent":
                        sap_entity = entity
                        break
                
                if sap_entity:
                    print("✅ SAP OData智能体已注册为业务实体")
                    print(f"   实体ID: {sap_entity.get('id')}")
                    print(f"   实体名称: {sap_entity.get('display_name')}")
                else:
                    print("⚠️ SAP OData智能体未在业务实体中找到")
                    
    except ImportError:
        print("⚠️ metadata_client不可用，跳过metadata-service检查")
    except Exception as e:
        print(f"⚠️ 检查metadata-service时出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 检查动态工作流设计器
    print("\n[4/4] 检查动态工作流设计器...")
    designer = engine.workflow_designer
    designer_pool = designer.agent_pool
    
    if "sap_odata_agent" in designer_pool:
        print("✅ SAP OData智能体已在工作流设计器智能体池中")
        agent_info = designer_pool["sap_odata_agent"]
        print(f"   名称: {agent_info.get('name')}")
        print(f"   描述: {agent_info.get('description')}")
        print(f"   能力: {agent_info.get('capabilities')}")
    else:
        print("❌ SAP OData智能体不在工作流设计器智能体池中")
        print("   智能体池中的智能体:")
        for agent_id in designer_pool.keys():
            print(f"     - {agent_id}")
    
    print("\n" + "="*80)
    print("检查完成")
    print("="*80)
    
    # 总结
    print("\n总结:")
    checks = [
        ("智能体池", "sap_odata_agent" in agent_pool),
        ("工作流设计器", "sap_odata_agent" in designer_pool),
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    print("\n💡 提示:")
    print("  - 如果智能体在智能体池中，会在服务启动时自动注册到metadata-service")
    print("  - 确保agent-service的main.py中调用了await engine.initialize()")
    print("  - 确保metadata-service正在运行且可访问")


if __name__ == "__main__":
    asyncio.run(check_sap_odata_agent_metadata())

