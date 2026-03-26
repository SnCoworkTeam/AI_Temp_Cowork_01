#!/usr/bin/env python3
"""执行迁移027"""
import sys
from pathlib import Path
import os

# 添加项目路径
project_root = Path("/opt/enterprise-ai-platform")
sys.path.insert(0, str(project_root))

# alembic.ini在/database目录
alembic_ini_path = "/database/alembic.ini"

from alembic.config import Config
from alembic import command

print("=" * 60)
print("执行数据库迁移 027")
print("=" * 60)
print(f"使用配置文件: {alembic_ini_path}")

try:
    cfg = Config(alembic_ini_path)
    print("开始执行迁移...")
    command.upgrade(cfg, "027")
    print("=" * 60)
    print("迁移027执行成功！")
    print("=" * 60)
except Exception as e:
    print(f"迁移失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

