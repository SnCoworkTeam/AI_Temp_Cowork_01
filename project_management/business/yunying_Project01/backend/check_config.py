from app.core.config import settings
import os

print(f"Current Working Directory: {os.getcwd()}")
print(f"DASHSCOPE_API_KEY env var: {os.environ.get('DASHSCOPE_API_KEY')}")
print(f"Settings LLM_API_KEY: {settings.LLM_API_KEY}")
