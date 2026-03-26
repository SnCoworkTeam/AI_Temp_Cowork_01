"""
测试 SAP OData 智能体 - 构建元数据并测试分析销售订单
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def main():
    """主函数：构建元数据并测试"""
    print("="*80)
    print("SAP OData 智能体测试 - 构建元数据并分析销售订单")
    print("="*80)
    
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        # 1. 初始化引擎
        print("\n[步骤 1/4] 初始化执行引擎...")
        engine = DynamicExecutionEngine()
        await engine.initialize()
        print("✅ 执行引擎初始化完成")
        
        # 2. 获取 SAP OData 智能体
        print("\n[步骤 2/4] 获取 SAP OData 智能体...")
        if "sap_odata_agent" not in engine.agent_pool:
            print("❌ SAP OData 智能体未找到")
            print(f"可用的智能体: {list(engine.agent_pool.keys())}")
            return
        
        sap_agent = engine.agent_pool["sap_odata_agent"]
        print(f"✅ 找到 SAP OData 智能体: {sap_agent.name}")
        print(f"   智能体ID: {sap_agent.agent_id}")
        
        # 3. 构建元数据（如果未构建）
        print("\n[步骤 3/4] 检查并构建元数据...")
        if hasattr(sap_agent, 'get_metadata_summary'):
            summary = sap_agent.get_metadata_summary()
            print(f"   当前状态: 已构建={summary.get('metadata_built', False)}, "
                  f"服务数={summary.get('total_services', 0)}, "
                  f"实体数={summary.get('total_entities', 0)}")
            
            if not summary.get('metadata_built', False):
                print("   开始构建元数据（限制20个服务，快速测试）...")
                result = await sap_agent.build_metadata(
                    force_rebuild=False,
                    limit_services=20
                )
                print(f"   构建结果: {result.get('status')}, "
                      f"服务数={result.get('services_count', 0)}, "
                      f"实体数={result.get('entities_count', 0)}")
                
                if result.get('status') == 'success':
                    print("   ✅ 元数据构建成功")
                else:
                    print(f"   ⚠️ 构建未完成: {result.get('message', '')}")
            else:
                print("   ✅ 元数据已构建，跳过")
        
        # 4. 测试分析销售订单
        print("\n[步骤 4/4] 测试分析销售订单...")
        test_tasks = [
            "查询最近的销售订单",
            "分析销售订单数据",
            "显示销售订单的统计信息"
        ]
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n--- 测试 {i}/{len(test_tasks)}: {task} ---")
            
            try:
                # 分析任务
                print("   分析任务中...")
                analysis = await sap_agent.analyze_task(
                    task_description=task,
                    context={}
                )
                
                needs_op = analysis.get('needs_sap_operation', False)
                op_type = analysis.get('operation_type', 'N/A')
                tool = analysis.get('selected_tool', 'N/A')
                
                print(f"   分析结果:")
                print(f"     需要SAP操作: {needs_op}")
                print(f"     操作类型: {op_type}")
                print(f"     选择的工具: {tool}")
                
                if needs_op and tool != 'N/A':
                    print("   执行任务中...")
                    result = await sap_agent.execute(
                        input_data={"task": task},
                        context={}
                    )
                    
                    success = result.get('execution_success', False)
                    print(f"   执行结果: {'✅ 成功' if success else '❌ 失败'}")
                    
                    if success:
                        processed = result.get('processed_result', {})
                        if processed:
                            summary_text = processed.get('summary', '')
                            if summary_text:
                                print(f"   结果摘要: {summary_text[:200]}...")
                    else:
                        error = result.get('error', '')
                        if error:
                            print(f"   错误: {error[:200]}")
                else:
                    reason = analysis.get('reason', 'N/A')
                    print(f"   ⚠️ 跳过执行: {reason}")
                    
            except Exception as e:
                print(f"   ❌ 测试失败: {str(e)[:200]}")
        
        print("\n" + "="*80)
        print("✅ 测试完成")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

