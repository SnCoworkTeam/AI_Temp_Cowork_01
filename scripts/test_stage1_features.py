"""
阶段一功能测试脚本
测试知识图谱构建增强、业务场景、反馈API、价值指标API
"""
import requests
import json
import time
from datetime import datetime

# 服务地址（根据docker-compose.yml中的端口映射）
API_GATEWAY_URL = "http://localhost:8080"  # 映射到8080
METADATA_SERVICE_URL = "http://localhost:8005"  # 映射到8005
AGENT_SERVICE_URL = "http://localhost:8010"  # 映射到8010

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_knowledge_graph_build():
    """测试知识图谱构建增强"""
    print_section("测试1: 知识图谱构建增强")
    
    # 测试1.1: 带priority_entities的构建
    print("1.1 测试priority_entities参数...")
    response = requests.post(
        f"{METADATA_SERVICE_URL}/api/ontology/build",
        json={
            "use_llm": True,
            "priority_entities": ["物料", "供应商", "采购订单"],
            "force_rebuild": False
        },
        timeout=300
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功: {result.get('concepts', 0)} 个概念, {result.get('relationships', 0)} 个关系")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试1.2: 统计API（/stats别名）
    print("\n1.2 测试统计API（/stats别名）...")
    response = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        stats = result.get("statistics", {})
        print(f"   ✅ 成功: {stats.get('total_nodes', 0)} 个节点, {stats.get('total_edges', 0)} 个边")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试1.3: force_rebuild
    print("\n1.3 测试force_rebuild参数...")
    response = requests.post(
        f"{METADATA_SERVICE_URL}/api/ontology/build",
        json={
            "use_llm": True,
            "force_rebuild": True
        },
        timeout=300
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功: 强制重建完成")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_business_scenario():
    """测试业务场景"""
    print_section("测试2: 采购订单查询场景")
    
    print("2.1 测试采购订单查询...")
    response = requests.post(
        f"{AGENT_SERVICE_URL}/api/scenarios/purchase-order/query",
        json={
            "po_number": "PO-2024-00123"
        },
        timeout=60
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        print(f"   ✅ 成功:")
        print(f"      - 订单信息: {data.get('order_info', {}).get('po_number', 'N/A')}")
        print(f"      - 收货状态: {data.get('receipt_status', {}).get('completion_rate', 0):.1f}%")
        print(f"      - 发票状态: {data.get('invoice_status', {}).get('completion_rate', 0):.1f}%")
        print(f"      - 异常数量: {len(data.get('alerts', []))}")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_feedback_api():
    """测试反馈API"""
    print_section("测试3: 反馈API")
    
    query_id = f"test_query_{int(time.time())}"
    
    # 测试3.1: 提交反馈
    print("3.1 测试提交反馈...")
    response = requests.post(
        f"{API_GATEWAY_URL}/api/feedback/submit",
        json={
            "query_id": query_id,
            "feedback_type": "positive",
            "query": "测试查询",
            "comment": "测试反馈"
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功: 反馈ID {result.get('feedback_id')}")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试3.2: 记录查询日志
    print("\n3.2 测试记录查询日志...")
    response = requests.post(
        f"{API_GATEWAY_URL}/api/feedback/log-query",
        json={
            "query_id": query_id,
            "query": "测试查询",
            "success": True,
            "response_time_ms": 150,
            "result_count": 5
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ 成功: 查询日志已记录")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试3.3: 获取反馈统计
    print("\n3.3 测试获取反馈统计...")
    response = requests.get(f"{API_GATEWAY_URL}/api/feedback/stats?time_range=7d")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功:")
        print(f"      - 总反馈数: {result.get('total_feedback', 0)}")
        print(f"      - 满意度: {result.get('satisfaction_rate', 0):.1f}%")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试3.4: 获取质量统计
    print("\n3.4 测试获取质量统计...")
    response = requests.get(f"{API_GATEWAY_URL}/api/feedback/quality-stats?time_range=7d")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功:")
        print(f"      - 总查询数: {result.get('total_queries', 0)}")
        print(f"      - 成功率: {result.get('success_rate', 0):.1f}%")
        print(f"      - 平均响应时间: {result.get('avg_response_time_ms', 0):.2f}ms")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_value_metrics_api():
    """测试价值指标API"""
    print_section("测试4: 价值指标API")
    
    # 测试4.1: 记录时间节省
    print("4.1 测试记录时间节省...")
    response = requests.post(
        f"{API_GATEWAY_URL}/api/value-metrics/record-time",
        json={
            "operation": "purchase_order_query",
            "time_saved": 300.0,
            "user_id": "test_user"
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功: 指标ID {result.get('metric_id')}")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试4.2: 记录错误减少
    print("\n4.2 测试记录错误减少...")
    response = requests.post(
        f"{API_GATEWAY_URL}/api/value-metrics/record-error",
        json={
            "operation": "purchase_order_query",
            "error_reduced": 2,
            "user_id": "test_user"
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功: 指标ID {result.get('metric_id')}")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试4.3: 获取时间节省统计
    print("\n4.3 测试获取时间节省统计...")
    response = requests.get(f"{API_GATEWAY_URL}/api/value-metrics/time-savings?time_range=7d")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功:")
        print(f"      - 总操作数: {result.get('total_operations', 0)}")
        print(f"      - 总节省时间: {result.get('total_time_saved_hours', 0):.2f} 小时")
        print(f"      - 平均节省时间: {result.get('avg_time_saved_seconds', 0):.2f} 秒")
    else:
        print(f"   ❌ 失败: {response.text}")
    
    # 测试4.4: 获取错误减少统计
    print("\n4.4 测试获取错误减少统计...")
    response = requests.get(f"{API_GATEWAY_URL}/api/value-metrics/error-reduction?time_range=7d")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 成功:")
        print(f"      - 总操作数: {result.get('total_operations', 0)}")
        print(f"      - 总减少错误: {result.get('total_errors_reduced', 0)}")
    else:
        print(f"   ❌ 失败: {response.text}")

def test_unified_search_traceability():
    """测试统一搜索的答案溯源"""
    print_section("测试5: 统一搜索答案溯源增强")
    
    print("5.1 测试统一搜索（检查答案溯源字段）...")
    response = requests.post(
        f"{API_GATEWAY_URL}/api/unified/search",
        json={
            "query": "采购订单",
            "limit": 5
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        results = result.get("results", [])
        if results:
            first_result = results[0]
            print(f"   ✅ 成功: 找到 {len(results)} 个结果")
            print(f"   ✅ 答案溯源字段:")
            print(f"      - source_document: {first_result.get('source_document', 'N/A')}")
            print(f"      - confidence_score: {first_result.get('confidence_score', 'N/A')}")
            print(f"      - extraction_method: {first_result.get('extraction_method', 'N/A')}")
        else:
            print(f"   ⚠️  未找到结果")
    else:
        print(f"   ❌ 失败: {response.text}")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  阶段一功能测试")
    print("="*60)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Gateway: {API_GATEWAY_URL}")
    print(f"Metadata Service: {METADATA_SERVICE_URL}")
    print(f"Agent Service: {AGENT_SERVICE_URL}")
    
    try:
        # 测试知识图谱构建增强
        test_knowledge_graph_build()
        
        # 测试业务场景
        test_business_scenario()
        
        # 测试反馈API
        test_feedback_api()
        
        # 测试价值指标API
        test_value_metrics_api()
        
        # 测试统一搜索答案溯源
        test_unified_search_traceability()
        
        print_section("测试完成")
        print("✅ 所有测试已完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

