"""
架构守护脚本测试
"""
import unittest
from pathlib import Path
from architecture_guard import ArchitectureGuard, ViolationLevel


class TestArchitectureGuard(unittest.TestCase):
    """架构守护测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.guard = ArchitectureGuard()
        self.project_root = Path(__file__).parent.parent
    
    def test_validate_project_structure(self):
        """测试项目结构验证"""
        result = self.guard.validate_project_structure()
        self.assertIn("success", result)
        self.assertIn("violations", result)
        self.assertIn("details", result)
    
    def test_validate_imports(self):
        """测试导入验证"""
        # 测试一个存在的文件
        test_file = self.project_root / "mcp-gateway" / "src" / "main.py"
        if test_file.exists():
            violations = self.guard.validate_imports(str(test_file))
            self.assertIsInstance(violations, list)
    
    def test_generate_health_report(self):
        """测试健康报告生成"""
        report = self.guard.generate_health_report()
        self.assertIn("timestamp", report)
        self.assertIn("project_structure", report)
        self.assertIn("services", report)
        self.assertIn("overall_health", report)
    
    def test_violation_levels(self):
        """测试违规级别"""
        self.assertEqual(ViolationLevel.ERROR.value, "error")
        self.assertEqual(ViolationLevel.WARNING.value, "warning")
        self.assertEqual(ViolationLevel.INFO.value, "info")


if __name__ == "__main__":
    unittest.main()









