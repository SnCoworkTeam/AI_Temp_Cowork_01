#!/usr/bin/env python3
"""
快速测试运行
在Git提交前运行快速测试套件
"""

import sys
import os
import subprocess
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent.parent


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


def find_test_files(modified_files):
    """根据修改的文件找到对应的测试文件"""
    test_files = []
    
    for file_path in modified_files:
        if file_path.endswith('.py'):
            # 查找对应的测试文件
            # 例如: src/main.py -> tests/test_main.py
            # 或者: src/routes/auth.py -> tests/test_auth.py
            
            # 移除扩展名
            base_name = file_path.replace('.py', '')
            
            # 查找可能的测试文件
            possible_tests = [
                f"tests/test_{Path(base_name).name}.py",
                f"tests/{base_name.replace('src/', 'test_')}.py",
                f"{base_name.replace('src/', 'tests/test_')}.py",
            ]
            
            for test_file in possible_tests:
                full_test_path = project_root / test_file
                if full_test_path.exists():
                    test_files.append(str(full_test_path))
                    break
    
    return test_files


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行快速测试...")
    
    # 获取修改的文件
    staged_files = get_staged_files()
    
    if not staged_files:
        print("ℹ️  没有修改的文件，跳过测试")
        return True
    
    # 查找相关的测试文件
    test_files = find_test_files(staged_files)
    
    if not test_files:
        print("ℹ️  未找到对应的测试文件，跳过测试")
        return True
    
    print(f"  找到 {len(test_files)} 个测试文件")
    
    # 运行pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "-x",  # 遇到第一个失败就停止
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误追踪
    ] + test_files
    
    print(f"  执行: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("✅ 快速测试通过")
        return True
    else:
        print("❌ 快速测试失败")
        return False


def main():
    """主函数"""
    try:
        # 检查是否安装了pytest
        try:
            import pytest
        except ImportError:
            print("⚠️  pytest未安装，跳过测试")
            return True
        
        success = run_unit_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: 运行测试时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









