#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景二:异常采购处理演示脚本
演示质量问题识别、诊断、处理和多系统协同的完整流程
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入演示数据
DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"

def load_demo_data():
    """加载演示数据"""
    suppliers = json.load(open(DEMO_DATA_DIR / "suppliers.json", "r", encoding="utf-8"))
    quality_issues = json.load(open(DEMO_DATA_DIR / "quality_issues.json", "r", encoding="utf-8"))
    po_history = []
    with open(DEMO_DATA_DIR / "po_history.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()
        headers = lines[0].strip().split(",")
        for line in lines[1:]:
            values = line.strip().split(",")
            po_history.append(dict(zip(headers, values)))
    return suppliers, quality_issues, po_history

def find_supplier_by_name(suppliers: List[Dict], name: str) -> Dict:
    """根据名称查找供应商"""
    for supplier in suppliers:
        if name in supplier["name"]:
            return supplier
    return None

def find_quality_issues_by_supplier(quality_issues: List[Dict], supplier_code: str) -> List[Dict]:
    """查找供应商的质量问题记录"""
    return [issue for issue in quality_issues if issue["supplier_code"] == supplier_code]

def find_related_orders(po_history: List[Dict], supplier_code: str, status: str = "completed") -> List[Dict]:
    """查找相关的采购订单"""
    return [po for po in po_history if po.get("supplier_code") == supplier_code and po.get("status") == status]

def demonstrate_quality_issue_handling():
    """演示质量问题处理流程"""
    
    print("=" * 80)
    print("场景二：异常采购处理（智能诊断与解决）")
    print("=" * 80)
    print()
    
    # 加载演示数据
    suppliers, quality_issues, po_history = load_demo_data()
    
    # 1. 用户输入
    user_input = "供应商苏州精密零件最近一批货质量有问题，我们需要暂停付款并调查。"
    print(f"【用户输入】")
    print(f"  {user_input}")
    print()
    
    # 2. AI意图分析与关联
    print("【步骤1】AI意图分析与关联")
    print("-" * 80)
    print("  识别活动: '质量问题处理'")
    print("  关联历史数据:")
    
    supplier_name = "苏州精密零件"
    supplier = find_supplier_by_name(suppliers, supplier_name)
    
    if supplier:
        supplier_code = supplier["supplier_code"]
        print(f"    * 找到供应商: {supplier['name']} ({supplier_code})")
        
        # 查找质量问题记录
        issues = find_quality_issues_by_supplier(quality_issues, supplier_code)
        print(f"    * 发现最近3个月有 {len(issues)} 次质量问题记录")
        
        # 显示质量问题
        for issue in issues[:3]:  # 显示最近3次
            print(f"      - {issue['issue_date']}: {issue['issue_type']} ({issue['severity']})")
            if issue['po_number']:
                print(f"        影响订单: {issue['po_number']}")
        
        # 查找相关订单
        related_orders = find_related_orders(po_history, supplier_code, "completed")
        pending_orders = find_related_orders(po_history, supplier_code, "pending")
        
        print(f"    * 关联未结清订单: {len(pending_orders)} 个待处理订单")
        for order in pending_orders[:3]:
            print(f"      - {order['po_number']}: {order['material_name']}, 金额: ¥{float(order['total_amount']):,.2f}")
        print()
        
        # 3. 智能诊断
        print("【步骤2】智能诊断")
        print("-" * 80)
        
        # 分析问题模式
        high_severity_count = sum(1 for issue in issues if issue['severity'] == 'high')
        medium_severity_count = sum(1 for issue in issues if issue['severity'] == 'medium')
        
        print("  问题模式分析:")
        print(f"    * 问题类型: 连续质量不合格")
        print(f"    * 严重问题: {high_severity_count} 次")
        print(f"    * 中等问题: {medium_severity_count} 次")
        
        # 评估风险
        if high_severity_count > 0 or len(issues) >= 3:
            risk_level = "高"
            print(f"    * 风险等级: {risk_level} (影响生产)")
        else:
            risk_level = "中"
            print(f"    * 风险等级: {risk_level}")
        
        print()
        print("  建议措施:")
        print("    1. 暂停对该供应商的所有付款")
        print("    2. 通知供应商质量部门")
        print("    3. 创建调查任务")
        if risk_level == "高":
            print("    4. 评估更换供应商")
        print()
        
        # 4. 多系统协同执行
        print("【步骤3】多系统协同执行")
        print("-" * 80)
        
        # 检查质量记录
        print("  [系统] 检查供应商质量记录...")
        quality_score = supplier.get("quality_score", 4.2)
        print(f"    ✓ 质量评分: {quality_score}/5.0")
        print(f"    ✓ 确认 {len(issues)} 次质量问题")
        print()
        
        # 暂停付款
        print("  [系统] 暂停付款处理...")
        affected_po_numbers = [order['po_number'] for order in pending_orders]
        hold_id = f"HOLD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"    ✓ 付款状态已更新为'暂停'")
        print(f"    ✓ 暂停记录ID: {hold_id}")
        print(f"    ✓ 受影响订单数: {len(affected_po_numbers)}")
        for po_num in affected_po_numbers[:3]:
            print(f"      - {po_num}")
        print()
        
        # 创建调查任务
        print("  [系统] 创建调查任务...")
        task_id = f"QC-{datetime.now().strftime('%Y%m%d')}-{len(issues)+1:03d}"
        print(f"    ✓ 任务#{task_id}已创建")
        print(f"    ✓ 分配给: 质量部")
        print(f"    ✓ 优先级: {risk_level}")
        print()
        
        # 发送通知
        print("  [系统] 发送通知邮件...")
        print(f"    ✓ 已通知供应商联系人: {supplier.get('contact_email', 'N/A')}")
        print(f"    ✓ 已通知内部质量团队")
        print(f"    ✓ 已通知采购经理")
        print()
        
        # 5. 结果与建议
        print("【步骤4】处理结果与后续建议")
        print("-" * 80)
        print(f"  已暂停订单: {', '.join(affected_po_numbers[:3])}{'...' if len(affected_po_numbers) > 3 else ''}")
        print(f"  调查任务: {task_id} (分配给质量部)")
        print(f"  通知已发送: 供应商联系人、内部质量团队")
        print()
        
        if risk_level == "高":
            print("  AI建议:")
            print("    * 考虑将未来订单的20%分配给备选供应商")
            print("    * 要求供应商提供质量改进计划")
            print("    * 加强质量抽检频率")
        else:
            print("  AI建议:")
            print("    * 要求供应商提供质量改进措施")
            print("    * 加强质量监控")
        print()
        
        return {
            "payment_hold_orders": affected_po_numbers,
            "investigation_task": task_id,
            "risk_level": risk_level,
            "recommendations": ["diversify_supplier", "quality_improvement_plan"],
            "hold_id": hold_id
        }
    else:
        print("  ❌ 错误: 未找到供应商")
        return None

if __name__ == "__main__":
    try:
        result = demonstrate_quality_issue_handling()
        if result:
            print("=" * 80)
            print("✅ 场景二演示完成！")
            print("=" * 80)
            sys.exit(0)
        else:
            print("=" * 80)
            print("❌ 场景二演示失败！")
            print("=" * 80)
            sys.exit(1)
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

