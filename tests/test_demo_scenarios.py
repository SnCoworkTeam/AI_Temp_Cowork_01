#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示场景测试
测试场景一和场景二的演示脚本
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from demos.demo_scenario_1_standard_procurement import (
    load_demo_data,
    find_supplier_by_name,
    find_material_by_code,
    calculate_delivery_date,
    demonstrate_standard_procurement
)
from demos.demo_scenario_2_quality_issue import (
    find_quality_issues_by_supplier,
    find_related_orders,
    demonstrate_quality_issue_handling
)


class TestDemoScenario1:
    """测试场景一：标准采购订单创建"""
    
    def test_load_demo_data(self):
        """测试加载演示数据"""
        suppliers, materials = load_demo_data()
        assert len(suppliers) > 0, "供应商数据应该存在"
        assert len(materials) > 0, "物料数据应该存在"
    
    def test_find_supplier_by_name(self):
        """测试根据名称查找供应商"""
        suppliers, _ = load_demo_data()
        supplier = find_supplier_by_name(suppliers, "苏州精密零件")
        assert supplier is not None, "应该找到供应商"
        assert supplier["supplier_code"] == "SUP_001", "供应商编码应该正确"
    
    def test_find_material_by_code(self):
        """测试根据编码查找物料"""
        _, materials = load_demo_data()
        material = find_material_by_code(materials, "MAT001")
        assert material is not None, "应该找到物料"
        assert material["material_code"] == "MAT001", "物料编码应该正确"
    
    def test_calculate_delivery_date(self):
        """测试计算交货日期"""
        delivery_date = calculate_delivery_date()
        assert delivery_date is not None, "交货日期应该存在"
        assert len(delivery_date) == 10, "日期格式应该正确 (YYYY-MM-DD)"
    
    def test_demonstrate_standard_procurement(self):
        """测试标准采购订单创建演示"""
        result = demonstrate_standard_procurement()
        assert result is not None, "演示应该返回结果"
        assert "po_number" in result, "结果应该包含订单号"
        assert "status" in result, "结果应该包含状态"
        assert result["status"] == "success", "状态应该为成功"


class TestDemoScenario2:
    """测试场景二：异常采购处理"""
    
    def test_find_quality_issues_by_supplier(self):
        """测试查找供应商的质量问题"""
        import json
        DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
        quality_issues = json.load(open(DEMO_DATA_DIR / "quality_issues.json", "r", encoding="utf-8"))
        
        issues = find_quality_issues_by_supplier(quality_issues, "SUP_001")
        assert len(issues) > 0, "应该找到质量问题记录"
    
    def test_find_related_orders(self):
        """测试查找相关订单"""
        import csv
        DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
        po_history = []
        with open(DEMO_DATA_DIR / "po_history.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            po_history = list(reader)
        
        orders = find_related_orders(po_history, "SUP_001", "completed")
        assert len(orders) > 0, "应该找到相关订单"
    
    def test_demonstrate_quality_issue_handling(self):
        """测试质量问题处理演示"""
        result = demonstrate_quality_issue_handling()
        assert result is not None, "演示应该返回结果"
        assert "payment_hold_orders" in result, "结果应该包含暂停付款订单"
        assert "investigation_task" in result, "结果应该包含调查任务"


class TestDemoDataIntegrity:
    """测试演示数据完整性"""
    
    def test_suppliers_data_integrity(self):
        """测试供应商数据完整性"""
        import json
        DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
        suppliers = json.load(open(DEMO_DATA_DIR / "suppliers.json", "r", encoding="utf-8"))
        
        required_fields = ["supplier_code", "name", "contact_person", "payment_terms", "credit_limit"]
        for supplier in suppliers:
            for field in required_fields:
                assert field in supplier, f"供应商数据应该包含字段: {field}"
    
    def test_materials_data_integrity(self):
        """测试物料数据完整性"""
        import json
        DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
        materials = json.load(open(DEMO_DATA_DIR / "materials.json", "r", encoding="utf-8"))
        
        required_fields = ["material_code", "name", "unit_price", "unit"]
        for material in materials:
            for field in required_fields:
                assert field in material, f"物料数据应该包含字段: {field}"
    
    def test_quality_issues_data_integrity(self):
        """测试质量问题数据完整性"""
        import json
        DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"
        quality_issues = json.load(open(DEMO_DATA_DIR / "quality_issues.json", "r", encoding="utf-8"))
        
        required_fields = ["issue_id", "supplier_code", "issue_type", "severity", "status"]
        for issue in quality_issues:
            for field in required_fields:
                assert field in issue, f"质量问题数据应该包含字段: {field}"

