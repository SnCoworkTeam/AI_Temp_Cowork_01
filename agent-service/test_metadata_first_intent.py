"""
测试元数据前置意图识别功能
测试场景：邮件发送、SAP查询等
"""
import asyncio
import sys
import os
from pathlib import Path
import time
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_service.src.core.metadata_first_intent_recognizer import MetadataFirstIntentRecognizer
from agent_service.src.core.conversation_agent import TaskType
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_email_sending():
    """测试邮件发送意图识别"""
    print("\n" + "="*60)
    print("测试场景1：邮件发送意图识别")
    print("="*60)
    
    recognizer = MetadataFirstIntentRecognizer()
    
    test_cases = [
        "发送邮件给yubin.liu@pcitc.com，主题是会议通知",
        "给销售部发邮件，说订单完成了",
        "发邮件通知客户订单已发货",
        "send email to yubin.liu@pcitc.com about meeting",
    ]
    
    results = []
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {user_input}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            intent = await recognizer.recognize_intent(user_input)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            print(f"✅ 识别成功")
            print(f"   任务类型: {intent.task_type.value}")
            print(f"   置信度: {intent.confidence:.2f}")
            print(f"   需要的工具: {intent.required_tools}")
            print(f"   需要的服务: {intent.required_services}")
            print(f"   推理: {intent.reasoning}")
            print(f"   耗时: {elapsed_time:.2f}ms")
            
            # 验证结果
            is_correct = (
                intent.task_type == TaskType.TOOL_EXECUTION and
                "send_email" in intent.required_tools
            )
            
            results.append({
                "input": user_input,
                "success": True,
                "task_type": intent.task_type.value,
                "confidence": intent.confidence,
                "required_tools": intent.required_tools,
                "elapsed_time_ms": elapsed_time,
                "correct": is_correct
            })
            
            if is_correct:
                print(f"   ✅ 结果正确")
            else:
                print(f"   ⚠️  结果可能不正确")
                
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            print(f"❌ 识别失败: {str(e)}")
            results.append({
                "input": user_input,
                "success": False,
                "error": str(e),
                "elapsed_time_ms": elapsed_time
            })
    
    return results


async def test_sap_query():
    """测试SAP查询意图识别"""
    print("\n" + "="*60)
    print("测试场景2：SAP查询意图识别")
    print("="*60)
    
    recognizer = MetadataFirstIntentRecognizer()
    
    test_cases = [
        "查询销售订单",
        "查一下采购订单",
        "分析一下销售数据",
        "查询SAP系统中的客户信息",
        "sales order query",
    ]
    
    results = []
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {user_input}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            intent = await recognizer.recognize_intent(user_input)
            elapsed_time = (time.time() - start_time) * 1000
            
            print(f"✅ 识别成功")
            print(f"   任务类型: {intent.task_type.value}")
            print(f"   置信度: {intent.confidence:.2f}")
            print(f"   需要的工具: {intent.required_tools}")
            print(f"   需要的服务: {intent.required_services}")
            print(f"   推理: {intent.reasoning}")
            print(f"   耗时: {elapsed_time:.2f}ms")
            
            # 验证结果
            is_correct = (
                intent.task_type == TaskType.TOOL_EXECUTION and
                (len(intent.required_tools) > 0 or len(intent.required_services) > 0)
            )
            
            results.append({
                "input": user_input,
                "success": True,
                "task_type": intent.task_type.value,
                "confidence": intent.confidence,
                "required_tools": intent.required_tools,
                "required_services": intent.required_services,
                "elapsed_time_ms": elapsed_time,
                "correct": is_correct
            })
            
            if is_correct:
                print(f"   ✅ 结果正确")
            else:
                print(f"   ⚠️  结果可能不正确")
                
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            print(f"❌ 识别失败: {str(e)}")
            results.append({
                "input": user_input,
                "success": False,
                "error": str(e),
                "elapsed_time_ms": elapsed_time
            })
    
    return results


async def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "="*60)
    print("测试场景3：缓存性能测试")
    print("="*60)
    
    recognizer = MetadataFirstIntentRecognizer()
    
    test_input = "发送邮件给yubin.liu@pcitc.com"
    
    # 第一次调用（应该检索元数据）
    print(f"\n第一次调用（无缓存）: {test_input}")
    start_time = time.time()
    intent1 = await recognizer.recognize_intent(test_input)
    time1 = (time.time() - start_time) * 1000
    print(f"   耗时: {time1:.2f}ms")
    
    # 第二次调用（应该使用缓存）
    print(f"\n第二次调用（有缓存）: {test_input}")
    start_time = time.time()
    intent2 = await recognizer.recognize_intent(test_input)
    time2 = (time.time() - start_time) * 1000
    print(f"   耗时: {time2:.2f}ms")
    
    # 计算加速比
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n📊 性能提升: {speedup:.2f}x")
    print(f"   时间节省: {time1 - time2:.2f}ms ({(1 - time2/time1)*100:.1f}%)")
    
    # 验证结果一致性
    if intent1.task_type == intent2.task_type:
        print(f"   ✅ 结果一致")
    else:
        print(f"   ⚠️  结果不一致")
    
    return {
        "first_call_ms": time1,
        "second_call_ms": time2,
        "speedup": speedup,
        "time_saved_ms": time1 - time2,
        "results_consistent": intent1.task_type == intent2.task_type
    }


async def test_mixed_scenarios():
    """测试混合场景"""
    print("\n" + "="*60)
    print("测试场景4：混合场景测试")
    print("="*60)
    
    recognizer = MetadataFirstIntentRecognizer()
    
    test_cases = [
        ("简单查询", "今天天气怎么样", TaskType.SIMPLE_QUERY),
        ("知识搜索", "搜索一下AI相关的文档", TaskType.KNOWLEDGE_SEARCH),
        ("工作流", "创建一个数据处理工作流", TaskType.WORKFLOW_TASK),
        ("复杂分析", "分析一下销售趋势", TaskType.COMPLEX_ANALYSIS),
    ]
    
    results = []
    for scenario_name, user_input, expected_type in test_cases:
        print(f"\n场景: {scenario_name}")
        print(f"输入: {user_input}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            intent = await recognizer.recognize_intent(user_input)
            elapsed_time = (time.time() - start_time) * 1000
            
            print(f"   任务类型: {intent.task_type.value}")
            print(f"   预期类型: {expected_type.value}")
            print(f"   置信度: {intent.confidence:.2f}")
            print(f"   耗时: {elapsed_time:.2f}ms")
            
            is_correct = intent.task_type == expected_type
            if is_correct:
                print(f"   ✅ 类型匹配")
            else:
                print(f"   ⚠️  类型不匹配")
            
            results.append({
                "scenario": scenario_name,
                "input": user_input,
                "expected_type": expected_type.value,
                "actual_type": intent.task_type.value,
                "confidence": intent.confidence,
                "elapsed_time_ms": elapsed_time,
                "correct": is_correct
            })
            
        except Exception as e:
            print(f"   ❌ 识别失败: {str(e)}")
            results.append({
                "scenario": scenario_name,
                "input": user_input,
                "success": False,
                "error": str(e)
            })
    
    return results


async def generate_report(email_results, sap_results, cache_results, mixed_results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    
    # 邮件发送测试统计
    email_success = sum(1 for r in email_results if r.get("success") and r.get("correct"))
    email_total = len(email_results)
    email_accuracy = (email_success / email_total * 100) if email_total > 0 else 0
    email_avg_time = sum(r.get("elapsed_time_ms", 0) for r in email_results if r.get("success")) / email_total if email_total > 0 else 0
    
    print(f"\n📧 邮件发送测试:")
    print(f"   准确率: {email_accuracy:.1f}% ({email_success}/{email_total})")
    print(f"   平均耗时: {email_avg_time:.2f}ms")
    
    # SAP查询测试统计
    sap_success = sum(1 for r in sap_results if r.get("success") and r.get("correct"))
    sap_total = len(sap_results)
    sap_accuracy = (sap_success / sap_total * 100) if sap_total > 0 else 0
    sap_avg_time = sum(r.get("elapsed_time_ms", 0) for r in sap_results if r.get("success")) / sap_total if sap_total > 0 else 0
    
    print(f"\n📊 SAP查询测试:")
    print(f"   准确率: {sap_accuracy:.1f}% ({sap_success}/{sap_total})")
    print(f"   平均耗时: {sap_avg_time:.2f}ms")
    
    # 缓存性能
    if cache_results:
        print(f"\n⚡ 缓存性能:")
        print(f"   首次调用: {cache_results['first_call_ms']:.2f}ms")
        print(f"   缓存调用: {cache_results['second_call_ms']:.2f}ms")
        print(f"   性能提升: {cache_results['speedup']:.2f}x")
        print(f"   时间节省: {cache_results['time_saved_ms']:.2f}ms")
    
    # 混合场景测试统计
    mixed_success = sum(1 for r in mixed_results if r.get("correct"))
    mixed_total = len(mixed_results)
    mixed_accuracy = (mixed_success / mixed_total * 100) if mixed_total > 0 else 0
    mixed_avg_time = sum(r.get("elapsed_time_ms", 0) for r in mixed_results if r.get("success") else 0) / mixed_total if mixed_total > 0 else 0
    
    print(f"\n🔄 混合场景测试:")
    print(f"   准确率: {mixed_accuracy:.1f}% ({mixed_success}/{mixed_total})")
    print(f"   平均耗时: {mixed_avg_time:.2f}ms")
    
    # 总体统计
    total_success = email_success + sap_success + mixed_success
    total_tests = email_total + sap_total + mixed_total
    overall_accuracy = (total_success / total_tests * 100) if total_tests > 0 else 0
    overall_avg_time = (email_avg_time * email_total + sap_avg_time * sap_total + mixed_avg_time * mixed_total) / total_tests if total_tests > 0 else 0
    
    print(f"\n📈 总体统计:")
    print(f"   总准确率: {overall_accuracy:.1f}% ({total_success}/{total_tests})")
    print(f"   平均耗时: {overall_avg_time:.2f}ms")
    
    # 保存详细报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "email_tests": {
            "accuracy": email_accuracy,
            "avg_time_ms": email_avg_time,
            "results": email_results
        },
        "sap_tests": {
            "accuracy": sap_accuracy,
            "avg_time_ms": sap_avg_time,
            "results": sap_results
        },
        "cache_performance": cache_results,
        "mixed_tests": {
            "accuracy": mixed_accuracy,
            "avg_time_ms": mixed_avg_time,
            "results": mixed_results
        },
        "overall": {
            "accuracy": overall_accuracy,
            "avg_time_ms": overall_avg_time,
            "total_tests": total_tests,
            "total_success": total_success
        }
    }
    
    report_file = "metadata_first_intent_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存到: {report_file}")


async def main():
    """主测试函数"""
    print("="*60)
    print("元数据前置意图识别功能测试")
    print("="*60)
    
    try:
        # 测试邮件发送
        email_results = await test_email_sending()
        
        # 测试SAP查询
        sap_results = await test_sap_query()
        
        # 测试缓存性能
        cache_results = await test_cache_performance()
        
        # 测试混合场景
        mixed_results = await test_mixed_scenarios()
        
        # 生成报告
        await generate_report(email_results, sap_results, cache_results, mixed_results)
        
        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
        print(f"\n❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())


