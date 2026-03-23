from app.services.llm_service import llm_service
from app.core.config import settings
import sys

print("Testing LLM Service with current configuration...")
print(f"URL: {settings.LLM_API_URL}")
print(f"Model: {settings.LLM_MODEL}")

# Test prompt
prompt = "请生成一段简短的市场分析测试文本，确认你可以正常工作。字数在50字以内。"

print(f"\nSending prompt: {prompt}")
print("-" * 50)

try:
    response = llm_service.generate_analysis(prompt)
    print("Response received:")
    print(response)
except Exception as e:
    print(f"Error occurred: {e}")
