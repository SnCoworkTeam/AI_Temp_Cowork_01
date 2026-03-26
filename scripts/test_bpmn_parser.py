#!/usr/bin/env python3
"""
测试BPMN解析器
"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'workflow-engine', 'src'))
sys.path.insert(0, os.path.join(project_root, 'shared_libs'))

from workflow_engine.src.core.bpmn_converter import BPMNConverter

def test_procure_to_pay():
    """测试采购到付款流程"""
    bpmn_file = os.path.join(project_root, 'workflow-engine', 'bpmn', 'procure_to_pay.bpmn')
    
    if not os.path.exists(bpmn_file):
        print(f"BPMN文件不存在: {bpmn_file}")
        return
    
    print("=" * 60)
    print("测试BPMN解析器 - 采购到付款流程")
    print("=" * 60)
    print()
    
    try:
        converter = BPMNConverter()
        workflow_def = converter.convert_from_file(bpmn_file, validate=True)
        
        print(f"✅ 解析成功！")
        print(f"   工作流名称: {workflow_def.name}")
        print(f"   节点数量: {len(workflow_def.nodes)}")
        print(f"   连接线数量: {len(workflow_def.connections)}")
        print(f"   起始节点: {workflow_def.start_node_id}")
        print(f"   结束节点: {workflow_def.end_node_ids}")
        print()
        
        # 统计AI节点
        ai_nodes = [n for n in workflow_def.nodes if n.node_type in ['agent', 'llm']]
        print(f"   AI节点数量: {len(ai_nodes)}")
        for node in ai_nodes:
            print(f"     - {node.name} ({node.node_type}): {node.config.get('agent_id', 'N/A')}")
        print()
        
        # 验证报告
        report = converter.get_validation_report()
        print("验证报告:")
        print(f"   有效: {report['valid']}")
        print(f"   错误数: {report['error_count']}")
        print(f"   警告数: {report['warning_count']}")
        
        if report['errors']:
            print("   错误:")
            for error in report['errors']:
                print(f"     - {error}")
        
        if report['warnings']:
            print("   警告:")
            for warning in report['warnings']:
                print(f"     - {warning}")
        
        print()
        print("=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 解析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_procure_to_pay()




