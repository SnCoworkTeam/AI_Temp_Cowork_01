#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景一:标准采购订单创建演示脚本
演示从自然语言输入到采购订单创建的完整流程
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
    materials = json.load(open(DEMO_DATA_DIR / "materials.json", "r", encoding="utf-8"))
    return suppliers, materials

def find_supplier_by_name(suppliers: List[Dict], name: str) -> Dict:
    """根据名称查找供应商"""
    for supplier in suppliers:
        if name in supplier["name"]:
            return supplier
    return None

def find_material_by_code(materials: List[Dict], code: str) -> Dict:
    """根据编码查找物料"""
    for material in materials:
        if material["material_code"] == code:
            return material
    return None

def calculate_delivery_date(days: int = 7) -> str:
    """计算交货日期（下周五）"""
    today = datetime.now()
    # 找到下周五
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7  # 如果今天是周五，则下周
    next_friday = today + timedelta(days=days_until_friday)
    return next_friday.strftime("%Y-%m-%d")

def demonstrate_standard_procurement():
    """演示标准采购订单创建流程"""
    
    print("=" * 80)
    print("场景一：标准采购订单创建（自动化执行）")
    print("=" * 80)
    print()
    
    # 加载演示数据
    suppliers, materials = load_demo_data()
    
    # 1. 用户输入
    user_input = "为苏州精密零件有限公司采购100件铝合金板MAT001，金额不超过5万，下周五前交货。"
    print(f"【用户输入】")
    print(f"  {user_input}")
    print()
    
    # 2. AI意图分析
    print("【步骤1】AI意图分析")
    print("-" * 80)
    print("  识别活动: '创建采购订单'")
    print("  提取实体:")
    
    # 解析用户输入
    supplier_name = "苏州精密零件有限公司"
    material_code = "MAT001"
    quantity = 100
    
    supplier = find_supplier_by_name(suppliers, supplier_name)
    material = find_material_by_code(materials, material_code)
    delivery_date = calculate_delivery_date()
    
    if supplier and material:
        print(f"    * 供应商: {supplier['name']} ({supplier['supplier_code']})")
        print(f"    * 物料: {material['name']} ({material['material_code']})")
        print(f"    * 数量: {quantity}件")
        print(f"    * 交货日期: {delivery_date} (下周五)")
        print(f"    * 金额限制: ¥50,000")
        print()
        
        # 计算金额
        unit_price = material["unit_price"]
        total_amount = unit_price * quantity
        
        print(f"  计算金额:")
        print(f"    * 单价: ¥{unit_price:.2f}/件")
        print(f"    * 数量: {quantity}件")
        print(f"    * 总金额: ¥{total_amount:.2f}")
        print()
        
        # 3. 能力匹配
        print("【步骤2】能力匹配")
        print("-" * 80)
        print("  匹配组件: SAP采购订单创建组件 (component:sap:create_po)")
        print("  匹配工作流: 标准采购流程 (workflow:standard_procurement)")
        print()
        
        # 4. 执行过程
        print("【步骤3】执行过程")
        print("-" * 80)
        
        # 验证供应商
        print("  [系统] 验证供应商信息...")
        print(f"    ✓ 供应商存在: {supplier['supplier_code']}")
        print(f"    ✓ 供应商状态: {supplier['status']}")
        print(f"    ✓ 信用额度: ¥{supplier['credit_limit']:,.0f}")
        print()
        
        # 检查物料
        print("  [系统] 检查物料可用性...")
        print(f"    ✓ 物料存在: {material['material_code']}")
        print(f"    ✓ 当前库存: {material['current_stock']}件")
        print(f"    ✓ 安全库存: {material['safety_stock']}件")
        print()
        
        # 预算检查
        print("  [系统] 验证预算...")
        if total_amount < 50000:
            print(f"    ✓ 金额 ¥{total_amount:,.2f} < ¥50,000 → 免审批")
            requires_approval = False
        else:
            print(f"    ⚠ 金额 ¥{total_amount:,.2f} ≥ ¥50,000 → 需要审批")
            requires_approval = True
        print()
        
        # 创建订单
        print("  [系统] 调用SAP ME21N创建订单...")
        po_number = f"4500000{datetime.now().strftime('%H%M%S')}"
        print(f"    ✓ 采购订单创建成功!")
        print(f"    ✓ 订单号: {po_number}")
        print(f"    ✓ 状态: 已保存")
        print()
        
        # 5. 结果展示
        print("【步骤4】执行结果")
        print("-" * 80)
        print(f"  采购订单号: {po_number}")
        print(f"  供应商: {supplier['name']} ({supplier['supplier_code']})")
        print(f"  物料: {material['name']} ({material['material_code']})")
        print(f"  数量: {quantity}件")
        print(f"  单价: ¥{unit_price:.2f}/件")
        print(f"  总金额: ¥{total_amount:,.2f}")
        print(f"  交货日期: {delivery_date}")
        print(f"  状态: {'已保存（待审批）' if requires_approval else '已保存'}")
        print()
        
        if not requires_approval:
            print("  ✓ 确认邮件已发送给采购员和供应商")
        else:
            print("  ⚠ 订单已提交审批，审批通过后将发送确认邮件")
        print()
        
        return {
            "po_number": po_number,
            "status": "success",
            "workflow_used": "standard_procurement",
            "total_amount": total_amount,
            "requires_approval": requires_approval
        }
    else:
        print("  ❌ 错误: 未找到供应商或物料")
        return None

if __name__ == "__main__":
    try:
        result = demonstrate_standard_procurement()
        if result:
            print("=" * 80)
            print("✅ 场景一演示完成！")
            print("=" * 80)
            sys.exit(0)
        else:
            print("=" * 80)
            print("❌ 场景一演示失败！")
            print("=" * 80)
            sys.exit(1)
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

