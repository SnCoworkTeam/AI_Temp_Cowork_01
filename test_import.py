#!/usr/bin/env python3
import sys
import os

# 添加 shared_libs 到 Python 路径
for path in ['/shared_libs', '/app/../shared_libs']:
    if os.path.exists(path):
        real_path = os.path.realpath(path)
        if real_path not in sys.path:
            sys.path.insert(0, real_path)
        if path not in sys.path:
            sys.path.insert(0, path)

print("Python path:", sys.path[:5])
print("Testing import...")

try:
    import shared_libs
    print("✓ shared_libs imported successfully")
    print("Location:", shared_libs.__file__)
    
    from shared_libs.schemas import workflow_schemas
    print("✓ shared_libs.schemas.workflow_schemas imported successfully")
except ImportError as e:
    print("✗ Import failed:", e)
    import traceback
    traceback.print_exc()

