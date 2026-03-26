"""
同步所有智能体元数据到metadata-service
检查并同步动态工作流引擎中的所有智能体
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def sync_agents_metadata():
    """同步所有智能体元数据到metadata-service"""
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        from src.core.agents.state_manager import InMemoryStateStore
        from src.services.metadata_client import metadata_client
        
        # 初始化执行引擎
        engine = DynamicExecutionEngine(
            enable_learning=False,
            enable_state_persistence=False,
            state_store=InMemoryStateStore()
        )
        
        # 初始化智能体
        await engine.initialize()
        
        # 获取所有智能体
        agents = engine.agent_pool
        logger.info(f"Found {len(agents)} agents in agent pool")
        
        synced_count = 0
        failed_count = 0
        results = []
        
        for agent_id, agent in agents.items():
            try:
                # 获取智能体信息
                agent_name = getattr(agent, 'name', agent_id)
                agent_description = getattr(agent, 'description', f"{agent_name}智能体")
                capabilities = getattr(agent, 'capabilities', {})
                
                # 转换capabilities为列表
                if isinstance(capabilities, dict):
                    capabilities_list = list(capabilities.keys()) + list(capabilities.values())
                elif isinstance(capabilities, list):
                    capabilities_list = capabilities
                else:
                    capabilities_list = [str(capabilities)]
                
                # 获取配置和元数据
                config = getattr(agent, 'config', {})
                metadata = {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "source": "dynamic_workflow_engine",
                    "builtin": True
                }
                
                # 注册为AI模型
                ai_model_result = await metadata_client.register_agent_as_ai_model(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_description=agent_description,
                    capabilities=capabilities_list,
                    config=config,
                    metadata=metadata,
                    status="active"
                )
                
                # 注册为业务实体
                entity_result = await metadata_client.register_agent_as_business_entity(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_description=agent_description,
                    capabilities=capabilities_list,
                    config=config,
                    metadata=metadata,
                    status="active"
                )
                
                if ai_model_result or entity_result:
                    synced_count += 1
                    results.append({
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "status": "success",
                        "ai_model": ai_model_result is not None,
                        "business_entity": entity_result is not None
                    })
                    logger.info(f"Successfully synced agent: {agent_id} ({agent_name})")
                else:
                    failed_count += 1
                    results.append({
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "status": "failed",
                        "error": "Both registrations failed"
                    })
                    logger.warning(f"Failed to sync agent: {agent_id} ({agent_name})")
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    "agent_id": agent_id,
                    "agent_name": getattr(agent, 'name', agent_id),
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"Error syncing agent {agent_id}: {e}", exc_info=True)
        
        # 输出总结
        print(f"\n{'='*80}")
        print("智能体元数据同步总结")
        print(f"{'='*80}")
        print(f"总计: {len(agents)} 个智能体")
        print(f"成功: {synced_count} 个")
        print(f"失败: {failed_count} 个")
        print(f"成功率: {synced_count/len(agents)*100:.1f}%")
        print(f"\n{'='*80}")
        print("详细结果:")
        print(f"{'='*80}")
        
        for result in results:
            status_icon = "[成功]" if result["status"] == "success" else "[失败]"
            print(f"{status_icon} {result['agent_id']} - {result['agent_name']}")
            if result["status"] == "success":
                print(f"    AI模型: {'是' if result.get('ai_model') else '否'}")
                print(f"    业务实体: {'是' if result.get('business_entity') else '否'}")
            else:
                print(f"    错误: {result.get('error', '未知错误')}")
        
        return synced_count == len(agents)
        
    except Exception as e:
        logger.error(f"Failed to sync agents metadata: {e}", exc_info=True)
        print(f"同步失败: {e}")
        return False


async def check_agents_metadata():
    """检查智能体元数据状态"""
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        from src.core.agents.state_manager import InMemoryStateStore
        
        # 初始化执行引擎
        engine = DynamicExecutionEngine(
            enable_learning=False,
            enable_state_persistence=False,
            state_store=InMemoryStateStore()
        )
        
        # 初始化智能体
        await engine.initialize()
        
        # 获取所有智能体
        agents = engine.agent_pool
        logger.info(f"Found {len(agents)} agents in agent pool")
        
        print(f"\n{'='*80}")
        print("智能体列表")
        print(f"{'='*80}")
        
        for agent_id, agent in agents.items():
            agent_name = getattr(agent, 'name', agent_id)
            agent_description = getattr(agent, 'description', '')
            capabilities = getattr(agent, 'capabilities', {})
            
            print(f"\n智能体ID: {agent_id}")
            print(f"名称: {agent_name}")
            print(f"描述: {agent_description}")
            print(f"能力: {capabilities}")
            print(f"类型: {type(agent).__name__}")
        
        print(f"\n{'='*80}")
        print(f"总计: {len(agents)} 个智能体")
        print(f"{'='*80}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check agents: {e}", exc_info=True)
        print(f"检查失败: {e}")
        return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能体元数据同步工具")
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查智能体列表，不进行同步"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="同步智能体元数据到metadata-service"
    )
    
    args = parser.parse_args()
    
    if args.check:
        await check_agents_metadata()
    elif args.sync:
        success = await sync_agents_metadata()
        sys.exit(0 if success else 1)
    else:
        # 默认先检查，再同步
        print("检查智能体列表...")
        await check_agents_metadata()
        print("\n开始同步智能体元数据...")
        success = await sync_agents_metadata()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)

