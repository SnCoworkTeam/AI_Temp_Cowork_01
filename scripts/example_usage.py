#!/usr/bin/env python3
"""
架构守护脚本使用示例
"""
from architecture_guard import ArchitectureGuard


def main():
    """示例用法"""
    # 创建架构守护实例
    guard = ArchitectureGuard()
    
    print("=" * 60)
    print("架构守护脚本使用示例")
    print("=" * 60)
    
    # 1. 验证项目结构
    print("\n1. 验证项目结构...")
    structure_result = guard.validate_project_structure()
    print(f"   结果: {'通过' if structure_result['success'] else '失败'}")
    print(f"   违规数量: {len(structure_result['violations'])}")
    
    # 2. 验证导入
    print("\n2. 验证导入...")
    test_file = "mcp-gateway/src/main.py"
    import_violations = guard.validate_imports(test_file)
    print(f"   文件: {test_file}")
    print(f"   违规数量: {len(import_violations)}")
    for violation in import_violations[:3]:  # 只显示前3个
        print(f"   - [{violation.level.value}] {violation.message}")
    
    # 3. 生成健康报告
    print("\n3. 生成健康报告...")
    report = guard.generate_health_report()
    print(f"   总体健康度: {report['overall_health']}")
    print(f"   时间戳: {report['timestamp']}")
    
    # 4. 导出报告
    print("\n4. 导出报告...")
    guard.export_report(report, "example_architecture_report.json")
    print("   报告已保存到: example_architecture_report.json")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()









