#!/usr/bin/env python3
"""
阶段一最终测试脚本
"""
import requests
import json
import sys

API_GATEWAY_URL = "http://localhost:8080"
METADATA_SERVICE_URL = "http://localhost:8005"
AGENT_SERVICE_URL = "http://localhost:8010"

def test_knowledge_graph():
    """测试知识图谱状态"""
    print("\n" + "="*60)
    print("测试1: 知识图谱基础关系建立（边>200）")
    print("="*60)
    
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            stats = data.get('statistics', {})
            edges = stats.get('total_edges', 0)
            nodes = stats.get('total_nodes', 0)
            edges_by_type = stats.get('edges_by_type', {})
            
            print(f"\n当前状态:")
            print(f"  节点数: {nodes}")
            print(f"  边数: {edges}")
            print(f"  边类型分布: {edges_by_type}")
            print(f"\n目标: 边数 > 200")
            print(f"结果: {'✅ 达到' if edges > 200 else f'❌ 未达到 (当前: {edges}, 需要再增加 {200 - edges} 条边)'}")
            
            return edges > 200
        else:
            print(f"❌ API错误: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_business_scenario():
    """测试业务场景端到端"""
    print("\n" + "="*60)
    print("测试2: 1个业务场景端到端跑通")
    print("="*60)
    
    try:
        r = requests.post(
            f"{AGENT_SERVICE_URL}/api/scenarios/purchase-order/query",
            json={"po_number": "PO-2024-00123"},
            timeout=15
        )
        
        print(f"\nAPI状态码: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"响应结构: {list(data.keys())}")
            
            if 'data' in data:
                inner = data['data']
                print(f"\n数据字段: {list(inner.keys()) if isinstance(inner, dict) else '非字典'}")
                
                if isinstance(inner, dict):
                    print(f"\n数据完整性检查:")
                    checks = {
                        "订单信息": "order_info" in inner,
                        "收货状态": "receipt_status" in inner,
                        "发票状态": "invoice_status" in inner,
                        "异常预警": "alerts" in inner,
                        "相关文档": "related_documents" in inner
                    }
                    
                    all_passed = True
                    for name, passed in checks.items():
                        status = "✅" if passed else "❌"
                        print(f"  {status} {name}")
                        if not passed:
                            all_passed = False
                    
                    print(f"\n端到端流程: {'✅ 完成' if all_passed else '⚠️ 部分完成'}")
                    return all_passed
                else:
                    print("❌ 数据格式错误")
                    return False
            else:
                print("❌ 响应中缺少data字段")
                return False
        else:
            print(f"❌ API错误: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("阶段一目标完成情况最终测试")
    print("="*60)
    
    result1 = test_knowledge_graph()
    result2 = test_business_scenario()
    
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    print(f"\n目标1: 知识图谱基础关系建立（边>200）")
    print(f"  结果: {'✅ 达到' if result1 else '❌ 未达到'}")
    print(f"\n目标2: 1个业务场景端到端跑通")
    print(f"  结果: {'✅ 达到' if result2 else '❌ 未达到'}")
    
    total = sum([result1, result2])
    print(f"\n总体达成: {total}/2 ({total*50}%)")
    
    if total == 2:
        print("\n🎉 所有目标已达成！")
        return 0
    elif total == 1:
        print("\n⚠️ 部分目标已达成")
        return 1
    else:
        print("\n❌ 目标未达成")
        return 2

if __name__ == "__main__":
    sys.exit(main())




