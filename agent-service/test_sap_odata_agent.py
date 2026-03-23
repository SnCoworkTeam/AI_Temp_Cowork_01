"""
测试 SAP OData 智能体
测试分析销售订单功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root.parent / "shared_libs") not in sys.path:
    sys.path.insert(0, str(project_root.parent / "shared_libs"))

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def test_sap_odata_agent():
    """测试 SAP OData 智能体"""
    print("="*80)
    print("测试 SAP OData 智能体 - 分析销售订单")
    print("="*80)
    
    try:
        # 导入必要的模块
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        print("\n[1/4] 初始化执行引擎...")
        engine = DynamicExecutionEngine()
        await engine.initialize()
        print("✅ 执行引擎初始化完成")
        
        # 检查 SAP OData 智能体是否存在
        print("\n[2/4] 检查 SAP OData 智能体...")
        if "sap_odata_agent" not in engine.agent_pool:
            print("❌ SAP OData 智能体未在智能体池中找到")
            print(f"   可用的智能体: {list(engine.agent_pool.keys())}")
            return
        
        sap_agent = engine.agent_pool["sap_odata_agent"]
        print(f"✅ 找到 SAP OData 智能体")
        print(f"   智能体ID: {sap_agent.agent_id}")
        print(f"   智能体名称: {sap_agent.name}")
        print(f"   智能体描述: {sap_agent.description}")
        print(f"   能力: {list(sap_agent.capabilities.keys()) if isinstance(sap_agent.capabilities, dict) else sap_agent.capabilities}")
        
        # 检查元数据状态
        print("\n[3/4] 检查元数据状态...")
        if hasattr(sap_agent, 'get_metadata_summary'):
            summary = sap_agent.get_metadata_summary()
            print(f"   元数据已构建: {summary.get('metadata_built', False)}")
            print(f"   服务数量: {summary.get('total_services', 0)}")
            print(f"   实体数量: {summary.get('total_entities', 0)}")
        
        # 测试分析销售订单
        print("\n[4/4] 测试分析销售订单...")
        test_tasks = [
            "查询最近的销售订单",
            "分析销售订单数据",
            "显示销售订单的统计信息",
            "查询9月份的销售订单"
        ]
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n--- 测试任务 {i}/{len(test_tasks)}: {task} ---")
            
            try:
                # 分析任务
                print("   正在分析任务...")
                analysis_result = await sap_agent.analyze_task(
                    task_description=task,
                    context={}
                )
                
                print(f"   分析结果:")
                print(f"     需要SAP操作: {analysis_result.get('needs_sap_operation', False)}")
                print(f"     操作类型: {analysis_result.get('operation_type', 'N/A')}")
                print(f"     选择的工具: {analysis_result.get('selected_tool', 'N/A')}")
                print(f"     业务实体: {analysis_result.get('business_entities', [])}")
                print(f"     SAP服务: {analysis_result.get('sap_service', 'N/A')}")
                
                if analysis_result.get('needs_sap_operation'):
                    print("   正在执行任务...")
                    execution_result = await sap_agent.execute(
                        input_data={"task": task},
                        context={}
                    )
                    
                    print(f"   执行结果:")
                    print(f"     执行成功: {execution_result.get('execution_success', False)}")
                    print(f"     操作类型: {execution_result.get('operation_type', 'N/A')}")
                    print(f"     使用的工具: {execution_result.get('tool_executed', 'N/A')}")
                    
                    # 显示处理后的结果摘要
                    processed = execution_result.get('processed_result', {})
                    if processed:
                        print(f"     结果摘要: {processed.get('summary', 'N/A')}")
                        key_findings = processed.get('key_findings', [])
                        if key_findings:
                            print(f"     关键发现:")
                            for finding in key_findings[:3]:  # 只显示前3个
                                print(f"       - {finding}")
                else:
                    print(f"   ⚠️ 分析结果: {analysis_result.get('reason', 'N/A')}")
                
            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*80)
        print("✅ 测试完成")
        print("="*80)
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n提示: 请确保在正确的目录下运行脚本")
        print("   当前目录:", os.getcwd())
        print("   脚本路径:", Path(__file__).resolve())
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_metadata_build():
    """测试元数据构建功能"""
    print("\n" + "="*80)
    print("测试元数据构建功能")
    print("="*80)
    
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        engine = DynamicExecutionEngine()
        await engine.initialize()
        
        if "sap_odata_agent" not in engine.agent_pool:
            print("❌ SAP OData 智能体未找到")
            return
        
        sap_agent = engine.agent_pool["sap_odata_agent"]
        
        # 检查元数据状态
        if hasattr(sap_agent, 'get_metadata_summary'):
            summary = sap_agent.get_metadata_summary()
            print(f"\n当前元数据状态:")
            print(f"   已构建: {summary.get('metadata_built', False)}")
            print(f"   服务数量: {summary.get('total_services', 0)}")
            print(f"   实体数量: {summary.get('total_entities', 0)}")
            
            # 如果未构建，尝试构建
            if not summary.get('metadata_built', False):
                print("\n开始构建元数据（限制10个服务用于快速测试）...")
                result = await sap_agent.build_metadata(limit_services=10)
                print(f"\n构建结果:")
                print(f"   状态: {result.get('status')}")
                print(f"   服务数量: {result.get('services_count', 0)}")
                print(f"   实体数量: {result.get('entities_count', 0)}")
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
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    # 测试元数据构建
    await test_metadata_build()
    
    # 测试智能体功能
    await test_sap_odata_agent()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
