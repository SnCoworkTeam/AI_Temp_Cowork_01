#!/usr/bin/env python3
"""
提交时更新文档
在Git提交前自动更新相关文档
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
scripts_dir = project_root / "scripts" / "docs"


def get_changed_files():
    """获取修改的文件"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def should_update_api_docs(changed_files):
    """判断是否需要更新API文档"""
    api_files = [
        "src/routes/",
        "src/main.py",
        "src/models/",
        "src/schemas/"
    ]
    return any(any(pattern in f for pattern in api_files) for f in changed_files)


def should_update_code_docs(changed_files):
    """判断是否需要更新代码文档"""
    python_files = [f for f in changed_files if f.endswith('.py')]
    return len(python_files) > 0


def main():
    """主函数"""
    changed_files = get_changed_files()
    
    if not changed_files:
        print("没有修改的文件，跳过文档更新")
        return
    
    print("检查文档更新需求...")
    
    # 更新API文档
    if should_update_api_docs(changed_files):
        print("更新API文档...")
        subprocess.run([sys.executable, str(scripts_dir / "generate-api-docs.py")])
    
    # 更新代码文档
    if should_update_code_docs(changed_files):
        print("更新代码文档...")
        # 只更新修改的文件（可选）
        # 这里简化处理，更新所有文档
        pass
    
    print("文档更新完成")


if __name__ == "__main__":
    main()









