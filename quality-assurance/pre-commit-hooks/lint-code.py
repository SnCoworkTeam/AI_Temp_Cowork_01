#!/usr/bin/env python3
"""
代码规范检查
在Git提交前检查代码风格和规范
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


def run_linter(files, tool="all"):
    """运行代码检查工具"""
    python_files = [f for f in files if f.endswith('.py')]
    
    if not python_files:
        print("ℹ️  没有Python文件需要检查")
        return True
    
    print(f"🔍 检查 {len(python_files)} 个Python文件...")
    
    all_passed = True
    
    # 1. Flake8检查
    if tool in ["all", "flake8"]:
        print("  运行 Flake8...")
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "flake8",
                    "--max-line-length=120",
                    "--extend-ignore=E203,W503",
                    "--exclude=.git,__pycache__,venv,env,.venv",
                ] + python_files,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ❌ Flake8发现问题:")
                print(result.stdout)
                all_passed = False
            else:
                print("  ✅ Flake8检查通过")
        except FileNotFoundError:
            print("  ⚠️  Flake8未安装，跳过")
    
    # 2. Black格式化检查
    if tool in ["all", "black"]:
        print("  运行 Black格式化检查...")
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "black",
                    "--check",
                    "--line-length=120",
                ] + python_files,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ❌ Black格式化检查失败:")
                print(result.stdout)
                print("  💡 运行 'black .' 自动格式化")
                all_passed = False
            else:
                print("  ✅ Black格式化检查通过")
        except FileNotFoundError:
            print("  ⚠️  Black未安装，跳过")
    
    # 3. isort导入排序检查
    if tool in ["all", "isort"]:
        print("  运行 isort导入排序检查...")
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "isort",
                    "--check-only",
                    "--profile=black",
                ] + python_files,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ❌ isort导入排序检查失败:")
                print(result.stdout)
                print("  💡 运行 'isort .' 自动排序")
                all_passed = False
            else:
                print("  ✅ isort导入排序检查通过")
        except FileNotFoundError:
            print("  ⚠️  isort未安装，跳过")
    
    # 4. Pylint检查（可选，较慢）
    if tool == "all" and os.getenv("RUN_PYLINT", "false").lower() == "true":
        print("  运行 Pylint...")
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "pylint",
                    "--max-line-length=120",
                    "--disable=C0111",  # 禁用缺少文档字符串警告
                ] + python_files[:5],  # 只检查前5个文件
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("  ⚠️  Pylint发现问题（非阻塞）:")
                print(result.stdout[:500])  # 只显示前500字符
            else:
                print("  ✅ Pylint检查通过")
        except FileNotFoundError:
            print("  ⚠️  Pylint未安装，跳过")
    
    return all_passed


def main():
    """主函数"""
    try:
        staged_files = get_staged_files()
        
        if not staged_files:
            print("ℹ️  没有暂存的文件需要检查")
            return True
        
        tool = sys.argv[1] if len(sys.argv) > 1 else "all"
        success = run_linter(staged_files, tool)
        
        if not success:
            print("\n❌ 代码规范检查失败")
            print("💡 提示:")
            print("   - 运行 'black .' 格式化代码")
            print("   - 运行 'isort .' 排序导入")
            print("   - 修复 Flake8 报告的问题")
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: 代码检查时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()









