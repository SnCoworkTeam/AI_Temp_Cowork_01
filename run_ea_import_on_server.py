"""
在服务器上运行企业架构数据导入
修改数据库连接为Docker网络中的postgres
"""
import sys
import os

# 修改数据库配置
os.environ['DB_HOST'] = 'postgres'
os.environ['DB_PORT'] = '5432'
os.environ['DB_USER'] = 'ai_user'
os.environ['DB_PASSWORD'] = 'ai_password'
os.environ['DB_NAME'] = 'ai_platform'

# 导入并运行主脚本
if __name__ == '__main__':
    # 读取并执行主脚本
    script_path = '/opt/enterprise-ai-platform/analyze_e2_report_and_generate_ea_data.py'
    with open(script_path, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code)

