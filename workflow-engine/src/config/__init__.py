"""
配置模块
包含各种配置模板和预设
"""
import sys
from pathlib import Path

# 导入settings（从上级目录的config.py）
config_file = Path(__file__).parent.parent / "config.py"
if config_file.exists():
    # 动态导入settings
    import importlib.util
    spec = importlib.util.spec_from_file_location("config_module", config_file)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    settings = config_module.settings
else:
    # 如果config.py不存在，创建一个默认的settings对象
    try:
        from pydantic_settings import BaseSettings
    except ImportError:
        # 如果pydantic_settings不可用，使用简单的类
        class BaseSettings:
            def __init__(self):
                self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
                self.LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
                self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    
    import os
    
    class Settings(BaseSettings):
        def __init__(self):
            if hasattr(BaseSettings, '__init__'):
                super().__init__()
            else:
                self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
                self.LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
                self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    
    settings = Settings()

__all__ = ["settings"]

