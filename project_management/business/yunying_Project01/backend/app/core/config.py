import os
from dotenv import load_dotenv

load_dotenv()

from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Industry Report Automation"
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    REPORT_DIR: str = os.path.join(BASE_DIR, "reports")
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # Zhuochuang API (Mock)
    ZHUOCHUANG_API_URL: str = "https://api.zhuochuang.mock/v1"
    ZHUOCHUANG_API_KEY: str = "mock-key"
    
    # LLM (Qwen) - will be mocked or use actual if key provided
    LLM_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-turbo")
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
