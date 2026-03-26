"""
os-core测试配置
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 添加os-core目录到路径（Python不能直接导入带连字符的模块名）
OS_CORE_PATH = PROJECT_ROOT / "os-core"
if str(OS_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(OS_CORE_PATH))
