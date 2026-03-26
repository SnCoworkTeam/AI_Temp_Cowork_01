#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上还原数据到数据库
从同步包中恢复PostgreSQL、Chroma和文档数据
"""

import subprocess
import sys
import os
from pathlib import Path

def run_ssh_command(command):
    """执行SSH命令"""
    ssh_cmd = [
        "ssh", "-F", "remote.ssh", "enterprise-ai-server", command
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def restore_data_on_server():
    """在服务器上恢复数据"""
    print("=" * 80)
    print("在服务器上恢复数据到数据库")
    print("=" * 80)
    print()
    
    # 检查同步包是否存在
    sync_package = "/opt/enterprise-ai-platform/backups/metadata_knowledge_sync_20251204_141922.tar.gz"
    
    print(f"[1/4] 检查同步包...")
    success, stdout, stderr = run_ssh_command(f"test -f {sync_package} && echo 'exists' || echo 'not found'")
    if "not found" in stdout:
        print(f"  ❌ 同步包不存在: {sync_package}")
        return False
    print(f"  ✅ 同步包存在: {sync_package}")
    print()
    
    # 检查恢复脚本是否存在
    restore_script = "/opt/enterprise-ai-platform/scripts/restore_on_server.sh"
    print(f"[2/4] 检查恢复脚本...")
    success, stdout, stderr = run_ssh_command(f"test -f {restore_script} && echo 'exists' || echo 'not found'")
    if "not found" in stdout:
        print(f"  ⚠️ 恢复脚本不存在，将创建...")
        # 上传恢复脚本
        upload_cmd = [
            "scp", "-F", "remote.ssh",
            "scripts/restore_on_server.sh",
            f"enterprise-ai-server:{restore_script}"
        ]
        result = subprocess.run(upload_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ 上传恢复脚本失败: {result.stderr}")
            return False
        print(f"  ✅ 恢复脚本已上传")
    else:
        print(f"  ✅ 恢复脚本存在")
    print()
    
    # 设置执行权限
    print(f"[3/4] 设置脚本执行权限...")
    success, stdout, stderr = run_ssh_command(f"chmod +x {restore_script}")
    if not success:
        print(f"  ⚠️ 设置权限失败，但继续执行...")
    print(f"  ✅ 权限已设置")
    print()
    
    # 执行恢复脚本
    print(f"[4/4] 执行数据恢复...")
    print(f"  这可能需要几分钟时间...")
    print()
    
    restore_cmd = f"cd /opt/enterprise-ai-platform && bash {restore_script} {sync_package}"
    success, stdout, stderr = run_ssh_command(restore_cmd)
    
    if success:
        print(stdout)
        print()
        print("=" * 80)
        print("✅ 数据恢复完成！")
        print("=" * 80)
        return True
    else:
        print("❌ 数据恢复失败:")
        print(stderr)
        return False

if __name__ == "__main__":
    try:
        success = restore_data_on_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

