#!/usr/bin/env python3
"""
预提交钩子脚本
在git commit之前自动运行架构检查
"""
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# 添加scripts目录到路径
scripts_dir = Path(__file__).parent
project_root = scripts_dir.parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(project_root))

try:
    # 尝试从scripts包导入
    from scripts.architecture_guard import ArchitectureGuard, ViolationLevel
except ImportError:
    try:
        # 尝试直接导入（如果scripts在路径中）
        from architecture_guard import ArchitectureGuard, ViolationLevel
    except ImportError:
        print("错误: 无法导入架构守护模块")
        print(f"Python路径: {sys.path}")
        print(f"当前目录: {Path.cwd()}")
        sys.exit(1)


class PreCommitHook:
    """预提交钩子类"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.guard = ArchitectureGuard(project_root=str(self.project_root))
        self.errors = []
        self.warnings = []
    
    def get_staged_files(self) -> List[str]:
        """
        获取暂存的文件列表
        
        Returns:
            暂存文件路径列表
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []
    
    def check_staged_files(self) -> Tuple[bool, List[str]]:
        """
        检查暂存的文件
        
        Returns:
            (是否通过, 错误消息列表)
        """
        staged_files = self.get_staged_files()
        
        if not staged_files:
            print("没有暂存的文件")
            return True, []
        
        print(f"检查 {len(staged_files)} 个暂存文件...")
        
        errors = []
        warnings = []
        
        # 检查Python文件的导入
        python_files = [f for f in staged_files if f.endswith('.py')]
        for file_path in python_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                violations = self.guard.validate_imports(str(full_path))
                for violation in violations:
                    if violation.level == ViolationLevel.ERROR:
                        errors.append(
                            f"{file_path}:{violation.line_number or '?'} - {violation.message}"
                        )
                    elif violation.level == ViolationLevel.WARNING:
                        warnings.append(
                            f"{file_path}:{violation.line_number or '?'} - {violation.message}"
                        )
        
        # 检查项目结构（仅在关键文件变更时）
        critical_files = [
            "docker-compose.yml",
            ".project_constitution.md",
            "requirements.txt",
            "package.json"
        ]
        
        if any(any(cf in f for cf in critical_files) for f in staged_files):
            structure_result = self.guard.validate_project_structure()
            for violation in structure_result["violations"]:
                if violation.level == ViolationLevel.ERROR:
                    errors.append(f"结构: {violation.message}")
        
        # 显示警告
        if warnings:
            print("\n警告:")
            for warning in warnings[:10]:  # 限制显示数量
                print(f"  ⚠ {warning}")
            if len(warnings) > 10:
                print(f"  ... 还有 {len(warnings) - 10} 个警告")
        
        # 显示错误
        if errors:
            print("\n错误:")
            for error in errors:
                print(f"  ✗ {error}")
            print("\n提交被阻止，请修复上述错误后重试")
            return False, errors
        
        return True, []
    
    def check_basic_rules(self) -> Tuple[bool, List[str]]:
        """
        检查基本规则
        
        Returns:
            (是否通过, 错误消息列表)
        """
        errors = []
        
        # 检查是否有TODO注释（可选规则）
        staged_files = self.get_staged_files()
        for file_path in staged_files:
            if not file_path.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                continue
            
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 检查TODO注释（可以配置为警告而非错误）
                    if 'TODO' in content or 'FIXME' in content:
                        # 这只是一个示例，实际可以配置为警告
                        pass
            except Exception:
                pass
        
        return True, errors
    
    def run(self) -> int:
        """
        运行预提交检查
        
        Returns:
            退出代码 (0=成功, 1=失败)
        """
        print("=" * 60)
        print("架构守护 - 预提交检查")
        print("=" * 60)
        
        # 检查基本规则
        basic_ok, basic_errors = self.check_basic_rules()
        if not basic_ok:
            self.errors.extend(basic_errors)
        
        # 检查暂存文件
        files_ok, file_errors = self.check_staged_files()
        if not files_ok:
            self.errors.extend(file_errors)
        
        # 快速结构检查
        structure_result = self.guard.validate_project_structure()
        critical_errors = [
            v for v in structure_result["violations"]
            if v.level == ViolationLevel.ERROR
        ]
        
        if critical_errors:
            print("\n关键结构错误:")
            for violation in critical_errors[:5]:
                print(f"  ✗ {violation.message}")
                if violation.file_path:
                    print(f"    文件: {violation.file_path}")
            self.errors.extend([v.message for v in critical_errors])
        
        # 总结
        print("\n" + "=" * 60)
        if self.errors:
            print(f"❌ 检查失败: {len(self.errors)} 个错误")
            print("\n提示:")
            print("  - 运行 'python scripts/architecture_guard.py --report' 查看详细报告")
            print("  - 运行 'python scripts/architecture_guard.py --auto-fix' 尝试自动修复")
            return 1
        else:
            print("✅ 检查通过")
            return 0


def install_hook():
    """安装git钩子"""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("错误: 不是git仓库")
        return False
    
    hook_file = hooks_dir / "pre-commit"
    script_path = Path(__file__).absolute()
    
    hook_content = f"""#!/bin/sh
# 架构守护预提交钩子
python3 "{script_path}" "$@"
"""
    
    try:
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        
        # 设置执行权限
        import os
        os.chmod(hook_file, 0o755)
        
        print(f"✅ 预提交钩子已安装: {hook_file}")
        return True
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="预提交钩子")
    parser.add_argument(
        "--install",
        action="store_true",
        help="安装git预提交钩子"
    )
    parser.add_argument(
        "--skip-hook",
        action="store_true",
        help="跳过钩子检查（用于测试）"
    )
    
    args = parser.parse_args()
    
    if args.install:
        success = install_hook()
        sys.exit(0 if success else 1)
    
    if args.skip_hook:
        print("跳过预提交检查")
        sys.exit(0)
    
    hook = PreCommitHook()
    exit_code = hook.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

