#!/usr/bin/env python3
"""
生成所有文档
运行所有文档生成脚本
"""
import sys
import subprocess
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent.parent
scripts_dir = project_root / "scripts" / "docs"


def run_script(script_name: str):
    """运行文档生成脚本"""
    script_path = scripts_dir / script_name
    if script_path.exists():
        print(f"\n{'='*60}")
        print(f"运行: {script_name}")
        print(f"{'='*60}")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=project_root,
                check=False
            )
            if result.returncode == 0:
                print(f"✅ {script_name} 完成")
            else:
                print(f"⚠️  {script_name} 完成（有警告）")
        except Exception as e:
            print(f"❌ {script_name} 失败: {e}")
    else:
        print(f"⚠️  脚本不存在: {script_name}")


def main():
    """主函数"""
    print("="*60)
    print("开始生成所有文档")
    print("="*60)
    
    # 运行所有文档生成脚本
    scripts = [
        "generate-api-docs.py",
        "generate-code-docs.py",
        "generate-dependency-graph.py"
    ]
    
    for script in scripts:
        run_script(script)
    
    print("\n" + "="*60)
    print("所有文档生成完成")
    print("="*60)
    print("\n文档位置:")
    print("  - API文档: docs/api-docs/")
    print("  - 代码文档: docs/auto-generated/code-docs/")
    print("  - 依赖图: docs/auto-generated/dependency-graphs/")


if __name__ == "__main__":
    main()









