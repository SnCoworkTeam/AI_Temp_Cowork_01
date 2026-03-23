#!/usr/bin/env python3
"""
测试SSH执行器导入
"""
import sys
import os
from pathlib import Path

# 添加可能的路径
possible_paths = [
    "/app/tools",
    "/opt/enterprise-ai-platform/tools",
    str(Path(__file__).resolve().parents[0] / "tools"),
]

print("Testing SSH executor import...")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

for path in possible_paths:
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.insert(0, path)
        print(f"✓ Added {path} to sys.path")
        ssh_file = os.path.join(path, "ssh_executor.py")
        if os.path.exists(ssh_file):
            print(f"  ✓ Found ssh_executor.py")
        else:
            print(f"  ✗ ssh_executor.py not found")
    else:
        print(f"✗ Path does not exist: {path}")

print("\nAttempting import...")
try:
    from tools.ssh_executor import SSHCommandExecutor, DeploymentExecutor, CommandResult
    print("✓ SUCCESS: SSH执行器导入成功")
    print(f"  SSHCommandExecutor: {SSHCommandExecutor}")
    print(f"  DeploymentExecutor: {DeploymentExecutor}")
    print(f"  CommandResult: {CommandResult}")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

