#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查服务器内存占用
"""
import subprocess
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_ssh_command(cmd):
    """执行SSH命令"""
    full_cmd = f'ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
    return result.stdout

print("="*80)
print("服务器内存占用分析")
print("="*80)

# 1. 总内存使用
print("\n1. 系统总内存:")
print(run_ssh_command("free -h"))

# 2. Docker容器内存占用（前10个）
print("\n2. Docker容器内存占用 (Top 10):")
docker_stats = run_ssh_command("sudo docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'")
lines = docker_stats.split('\n')
print(lines[0])  # Header
# 解析并排序
data_lines = []
for line in lines[1:]:
    if line.strip():
        parts = line.split('\t')
        if len(parts) >= 3:
            try:
                mem_perc = float(parts[2].replace('%', ''))
                data_lines.append((line, mem_perc))
            except:
                pass

# 按内存百分比排序
data_lines.sort(key=lambda x: x[1], reverse=True)
for line, _ in data_lines[:10]:
    print(line)

# 3. 占用内存最多的进程（非Docker）
print("\n3. 占用内存最多的进程 (Top 10):")
print(run_ssh_command("ps aux --sort=-%mem | head -11 | tail -10"))

# 4. Qdrant特别检查（向量数据库）
print("\n4. Qdrant向量数据库检查:")
qdrant_info = run_ssh_command("sudo docker stats enterprise-ai-qdrant --no-stream")
print(qdrant_info)
