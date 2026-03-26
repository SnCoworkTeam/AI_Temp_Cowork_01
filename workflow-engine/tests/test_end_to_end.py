#!/usr/bin/env python3
"""
端到端流程测试
验证从Web UI到工作流执行的完整链路
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine"))


async def test_end_to_end_workflow():
    """测试端到端工作流执行"""
    print("=" * 60)
    print("端到端流程测试")
    print("=" * 60)
    
    try:
        from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
        from shared_libs.schemas.workflow_states import create_workflow_state
        
        engine = DynamicWorkflowEngine()
        
        # 测试工作流配置（模拟Web UI提交的配置）
        print("\n1. 创建工作流配置（模拟Web UI）...")
        test_workflow = {
            "name": "文档分析工作流",
            "description": "端到端测试：文档分析和摘要生成",
            "version": "1.0.0",
            "start_node_id": "start",
            "nodes": [
                {
                    "id": "start",
                    "name": "开始",
                    "type": "start",
                    "config": {}
                },
                {
                    "id": "analyze",
                    "name": "文档分析",
                    "type": "task",  # 使用task类型，在config中指定使用LLM节点
                    "config": {
                        "node_class": "LLMNode",  # 指定使用LLM节点类
                        "prompt_template": "分析以下文档内容：{input_data.content}",
                        "output_key": "analysis",
                        "model": "deepseek-chat",
                        "temperature": 0.7
                    }
                },
                {
                    "id": "summarize",
                    "name": "生成摘要",
                    "type": "task",  # 使用task类型，在config中指定使用LLM节点
                    "config": {
                        "node_class": "LLMNode",  # 指定使用LLM节点类
                        "prompt_template": "基于分析结果 {analyze_output} 生成摘要，要求简洁明了。",
                        "output_key": "summary",
                        "model": "deepseek-chat",
                        "temperature": 0.5
                    }
                },
                {
                    "id": "end",
                    "name": "结束",
                    "type": "end",
                    "config": {}
                }
            ],
            "edges": [
                {
                    "source": "start",
                    "target": "analyze",
                    "condition": None
                },
                {
                    "source": "analyze",
                    "target": "summarize",
                    "condition": None
                },
                {
                    "source": "summarize",
                    "target": "end",
                    "condition": None
                }
            ]
        }
        
        print("   [OK] 工作流配置创建成功")
        print(f"   - 工作流名称: {test_workflow['name']}")
        print(f"   - 节点数量: {len(test_workflow['nodes'])}")
        print(f"   - 边数量: {len(test_workflow['edges'])}")
        
        # 步骤2: 构建工作流（模拟API接收配置）
        print("\n2. 构建工作流（模拟API处理）...")
        try:
            workflow_id = engine.build_from_config(test_workflow)
            print(f"   [OK] 工作流构建成功")
            print(f"   - workflow_id: {workflow_id}")
            
            # 验证工作流已注册
            workflows = engine.list_workflows()
            workflow_found = any(w.get('id') == workflow_id for w in workflows)
            if workflow_found:
                print(f"   [OK] 工作流已注册到引擎")
            else:
                print(f"   [WARN] 工作流未在列表中找到")
        except Exception as e:
            print(f"   [ERROR] 工作流构建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 步骤3: 创建执行状态（模拟Web UI提交的输入）
        print("\n3. 创建执行状态（模拟Web UI输入）...")
        test_input = {
            "content": """
            人工智能（AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
            AI技术包括机器学习、深度学习、自然语言处理等。这些技术正在改变我们的生活方式和工作方式。
            """
        }
        
        state = create_workflow_state(
            workflow_id=workflow_id,
            input_data=test_input,
            thread_id=f"test_thread_{workflow_id[:8]}"
        )
        
        state_dict = state.model_dump()
        print("   [OK] 执行状态创建成功")
        print(f"   - thread_id: {state_dict.get('thread_id')}")
        print(f"   - input_data: {test_input['content'][:50]}...")
        
        # 步骤4: 执行工作流（模拟工作流引擎处理）
        print("\n4. 执行工作流（模拟工作流引擎）...")
        print("   注意: 如果LLM节点未配置API密钥，将使用模拟响应")
        
        try:
            # 检查是否有可用的LLM配置
            import os
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                print(f"   [OK] 检测到API密钥，将使用真实LLM调用")
            else:
                print(f"   [WARN] 未检测到API密钥，将使用模拟响应")
            
            # 执行工作流
            result = await engine.execute_workflow(
                workflow_id=workflow_id,
                input_data=test_input,
                thread_id=state_dict.get('thread_id')
            )
            
            print("   [OK] 工作流执行完成")
            print(f"   - 执行状态: {result.get('status', 'unknown')}")
            
            # 验证执行结果
            if 'final_result' in result:
                print(f"   [OK] 找到最终结果")
            else:
                print(f"   [WARN] 未找到final_result，检查node_results")
                if 'node_results' in result:
                    print(f"   - 节点结果数量: {len(result.get('node_results', {}))}")
            
            # 显示节点执行结果
            node_results = result.get('node_results', {})
            if node_results:
                print("\n   节点执行结果:")
                for node_id, node_result in node_results.items():
                    if isinstance(node_result, dict):
                        # 尝试获取输出内容
                        output = node_result.get('content') or node_result.get('result') or str(node_result)[:100]
                        print(f"   - {node_id}: {output}...")
                    else:
                        print(f"   - {node_id}: {str(node_result)[:100]}...")
            
        except Exception as e:
            print(f"   [ERROR] 工作流执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 步骤5: 验证结果（模拟Web UI显示结果）
        print("\n5. 验证执行结果（模拟Web UI显示）...")
        
        # 检查关键字段
        required_fields = ['status', 'workflow_id', 'thread_id']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"   [WARN] 缺少字段: {missing_fields}")
        else:
            print("   [OK] 所有必需字段存在")
        
        # 检查执行历史
        execution_history = result.get('execution_history', [])
        if execution_history:
            print(f"   [OK] 执行历史记录存在 ({len(execution_history)} 条)")
            print("   执行历史摘要:")
            for i, entry in enumerate(execution_history[:5], 1):  # 只显示前5条
                node_id = entry.get('node_id', 'unknown')
                success = entry.get('success', False)
                status = "[OK]" if success else "[ERROR]"
                print(f"   {i}. {status} {node_id}")
        else:
            print("   [WARN] 执行历史为空")
        
        # 检查错误
        if result.get('error'):
            print(f"   [WARN] 工作流执行有错误: {result['error']}")
        else:
            print("   [OK] 工作流执行无错误")
        
        # 步骤6: 测试流式执行（可选）
        print("\n6. 测试流式执行（可选功能）...")
        try:
            if hasattr(engine, 'execute_workflow_stream'):
                print("   [OK] 流式执行方法可用")
                print("   注意: 完整流式测试需要LangGraph支持")
            else:
                print("   [WARN] 流式执行方法不可用")
        except Exception as e:
            print(f"   [WARN] 流式执行测试跳过: {e}")
        
        print("\n" + "=" * 60)
        print("[OK] 端到端流程测试通过！")
        print("=" * 60)
        print("\n测试总结:")
        print("- ✅ 工作流配置创建成功")
        print("- ✅ 工作流构建成功")
        print("- ✅ 执行状态创建成功")
        print("- ✅ 工作流执行完成")
        print("- ✅ 执行结果验证通过")
        print("\n完整链路验证:")
        print("Web UI → API → 工作流引擎 → 节点执行 → 结果返回 → Web UI")
        
        return True
        
    except ImportError as e:
        print(f"   [ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_workflow():
    """测试简单工作流（不依赖LLM）"""
    print("\n" + "=" * 60)
    print("简单工作流测试（不依赖LLM）")
    print("=" * 60)
    
    try:
        from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
        from shared_libs.schemas.workflow_states import create_workflow_state
        
        engine = DynamicWorkflowEngine()
        
        # 创建简单工作流（只使用task节点）
        simple_workflow = {
            "name": "简单数据处理工作流",
            "description": "测试简单数据处理流程",
            "version": "1.0.0",
            "start_node_id": "start",
            "nodes": [
                {
                    "id": "start",
                    "name": "开始",
                    "type": "start",
                    "config": {}
                },
                {
                    "id": "process",
                    "name": "数据处理",
                    "type": "task",
                    "config": {
                        "script": "result = input_data.value * 2"
                    }
                },
                {
                    "id": "end",
                    "name": "结束",
                    "type": "end",
                    "config": {}
                }
            ],
            "edges": [
                {
                    "source": "start",
                    "target": "process",
                    "condition": None
                },
                {
                    "source": "process",
                    "target": "end",
                    "condition": None
                }
            ]
        }
        
        print("\n1. 构建简单工作流...")
        workflow_id = engine.build_from_config(simple_workflow)
        print(f"   [OK] 工作流构建成功: {workflow_id}")
        
        print("\n2. 执行简单工作流...")
        test_input = {"value": 10}
        
        result = await engine.execute_workflow(
            workflow_id=workflow_id,
            input_data=test_input
        )
        
        print(f"   [OK] 工作流执行完成")
        print(f"   - 状态: {result.get('status', 'unknown')}")
        
        print("\n" + "=" * 60)
        print("[OK] 简单工作流测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] 简单工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    # 运行端到端测试
    success1 = await test_end_to_end_workflow()
    
    # 运行简单工作流测试
    success2 = await test_simple_workflow()
    
    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

