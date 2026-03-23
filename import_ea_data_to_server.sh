#!/bin/bash
# 在服务器上导入企业架构数据

cd /opt/enterprise-ai-platform

# 修改数据库配置为服务器配置
export DB_HOST=postgres
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform

# 运行分析脚本
echo "开始分析E2报告并生成企业架构数据..."
python3 analyze_e2_report_and_generate_ea_data.py

echo ""
echo "数据导入完成！"

