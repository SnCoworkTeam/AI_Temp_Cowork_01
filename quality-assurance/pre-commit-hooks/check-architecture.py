#!/usr/bin/env python3
"""
架构符合性检查
在Git提交前检查代码是否符合项目架构规范
"""

import sys
import os
from pathlib import Path
import subprocess
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.architecture_guard import ArchitectureGuard
except ImportError:
    print("ERROR: 无法导入ArchitectureGuard模块")
    sys.exit(1)


def get_staged_files():
    """获取暂存的文件列表"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]


def check_architecture():
    """检查架构符合性"""
    print("🔍 检查架构符合性...")
    
    guard = ArchitectureGuard(project_root)
    
    # 获取暂存的文件
    staged_files = get_staged_files()
    
    if not staged_files:
        print("ℹ️  没有暂存的文件需要检查")
        return True
    
    # 过滤Python文件
    python_files = [f for f in staged_files if f.endswith('.py')]
    
    if not python_files:
        print("ℹ️  没有Python文件需要检查")
        return True
    
    issues = []
    
    # 检查项目结构
    print("  检查项目结构...")
    structure_valid, structure_issues = guard.validate_project_structure()
    if not structure_valid:
        issues.extend(structure_issues)
    
    # 检查导入依赖
    print("  检查导入依赖...")
    for file_path in python_files:
        full_path = project_root / file_path
        if full_path.exists():
            import_valid, import_issues = guard.validate_imports(str(full_path))
            if not import_valid:
                issues.extend(import_issues)
    
    # 检查API规范
    print("  检查API规范...")
    api_valid, api_issues = guard.validate_api_specifications()
    if not api_valid:
        issues.extend(api_issues)
    
    if issues:
        print("\n❌ 架构符合性检查失败:")
        for issue in issues[:10]:  # 只显示前10个问题
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... 还有 {len(issues) - 10} 个问题")
        return False
    
    print("✅ 架构符合性检查通过")
    return True


def main():
    """主函数"""
    try:
        success = check_architecture()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: 架构检查时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









