import requests
import json

data = {
    "name": "auth-service",
    "host": "auth-service",
    "port": 8003,
    "service_type": "HTTP",
    "health_check_url": "/health",
    "metadata": {"version": "1.0.0"},
    "tags": ["auth", "authentication"]
}

response = requests.post("http://localhost:8000/api/register", json=data)
print(response.text)
