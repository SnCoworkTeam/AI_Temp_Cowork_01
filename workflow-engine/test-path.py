#!/usr/bin/env python
"""测试shared_libs路径配置"""
import sys
import os

print("=== shared_libs路径检查 ===")
print(f"\nPYTHONPATH环境变量: {os.environ.get('PYTHONPATH', '未设置')}")
print(f"\nPython sys.path中的shared_libs相关路径:")
for p in sys.path:
    if 'shared_libs' in p or 'enterprise' in p:
        print(f"  ✓ {p}")

print(f"\nshared_libs真实路径: E:\\enterprise-ai-platform\\shared_libs")
print(f"路径存在: {os.path.exists(r'E:\enterprise-ai-platform\shared_libs')}")

print(f"\n测试导入:")
try:
    from shared_libs.common.logger import setup_logger
    print("  ✅ shared_libs.common.logger")
    
    from shared_libs.schemas.workflow_schemas import WorkflowStatus
    print("  ✅ shared_libs.schemas.workflow_schemas")
    
    from shared_libs.common.http_client import HTTPClient
    print("  ✅ shared_libs.common.http_client")
    
    from shared_libs.common.agent_error_handling import *
    print("  ✅ shared_libs.common.agent_error_handling")
    
    print("\n✅ 所有导入成功！路径配置正确！")
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

