#!/usr/bin/env python3
"""
检查ADR要求
检查是否有架构变更但没有创建或更新ADR
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
adr_dir = project_root / "docs" / "architecture-docs" / "decision-records"


def get_changed_files():
    """获取变更的文件"""
    # 检查是否是PR环境
    pr_number = None
    try:
        pr_number = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            capture_output=True,
            text=True
        ).stdout.strip()
    except:
        pass
    
    if pr_number:
        # PR环境，获取PR变更
        result = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--name-only"],
            capture_output=True,
            text=True
        )
    else:
        # 本地环境，获取暂存文件
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True
        )
    
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def check_architecture_changes(changed_files):
    """检查是否有架构相关变更"""
    architecture_keywords = [
        "architecture", "arch", "design", "framework",
        "service", "database", "auth", "api", "sso",
        "microservice", "workflow", "tool", "gateway"
    ]
    
    architecture_files = [
        f for f in changed_files
        if any(keyword in f.lower() for keyword in architecture_keywords)
        and f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.yml', '.yaml'))
        and 'test' not in f.lower()
    ]
    
    return architecture_files


def check_adr_updates():
    """检查是否有ADR更新"""
    changed_files = get_changed_files()
    
    adr_changes = [
        f for f in changed_files
        if 'decision-records' in f and f.endswith('.md')
    ]
    
    architecture_changes = check_architecture_changes(changed_files)
    
    if architecture_changes and not adr_changes:
        print("⚠️  检测到架构相关变更，但未创建或更新ADR:")
        for f in architecture_changes[:10]:
            print(f"  - {f}")
        print("\n建议:")
        print("  1. 创建新的ADR记录架构决策")
        print("  2. 或更新现有ADR记录变更")
        print(f"\n参考模板: {adr_dir}/adr-template.md")
        return False
    
    return True


if __name__ == "__main__":
    success = check_adr_updates()
    sys.exit(0 if success else 1)









