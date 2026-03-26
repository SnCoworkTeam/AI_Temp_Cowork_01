#!/usr/bin/env python3
"""运行迁移027"""
import sys
from pathlib import Path

project_root = Path("/opt/enterprise-ai-platform")
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
import os

os.chdir("/opt/enterprise-ai-platform/database")
cfg = Config("alembic.ini")
command.upgrade(cfg, "027")
print("Migration 027 completed")

