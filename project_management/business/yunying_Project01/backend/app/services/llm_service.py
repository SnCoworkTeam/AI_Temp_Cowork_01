import requests
import json
from app.core.config import settings
from typing import Dict, Any
import urllib3

# Suppress InsecureRequestWarning since we are disabling SSL verify
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_url = settings.LLM_API_URL
        self.model = settings.LLM_MODEL
        
    def generate_analysis(self, prompt: str) -> str:
        if not self.api_key or self.api_key == "your_api_key_here":
            return "Mock Analysis: LLM API Key not configured. Please set DASHSCOPE_API_KEY in .env file."
            
        try:
            # Assuming OpenAI-compatible format or standard completion format
            # Based on the URL /chat/completions, it's likely OpenAI-compatible
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # OpenAI compatible payload
            payload = {
                "model": self.model, # Use configured model
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            print(f"Calling LLM at {self.api_url}")
            print(f"Using Model: {self.model}")
            
            # Disable SSL verification if needed (for internal corporate networks)
            # and add retry logic
            
            session = requests.Session()
            # session.verify = False # Uncomment if SSL certificate errors persist
            
            response = session.post(
                self.api_url, 
                headers=headers, 
                json=payload,
                timeout=60,
                verify=False, # Often needed for corporate internal APIs
                proxies={"http": None, "https": None} # Disable proxies to avoid local proxy errors
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for explicit error in 200 OK response (common in some gateways)
                if isinstance(result, dict) and result.get("code") == 422:
                    return f"Error from LLM Provider: {result.get('msg', 'Unknown Error')} (Model: {self.model})"

                # Try standard OpenAI format
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    return message.get("content", "")
                # Fallback for other formats
                return str(result)
            else:
                return f"Error: Status code: {response.status_code}, Response: {response.text}"
                
        except Exception as e:
            return f"Exception during LLM call: {str(e)}"

llm_service = LLMService()
