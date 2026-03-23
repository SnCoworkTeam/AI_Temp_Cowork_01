#!/bin/bash
# 远程执行数据初始化脚本

cd /opt/enterprise-ai-platform

# 在metadata-service容器中执行
docker compose exec -T metadata-service python << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, '/opt/enterprise-ai-platform')

# 设置环境变量
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/enterprise_ai_platform')

# 执行初始化脚本
exec(open('/opt/enterprise-ai-platform/scripts/init_enterprise_architecture_data.py').read())
PYTHON_SCRIPT

