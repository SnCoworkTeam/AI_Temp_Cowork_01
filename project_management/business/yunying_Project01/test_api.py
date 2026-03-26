import requests
import json

def test_generate():
    url = "http://localhost:8000/api/reports/generate"
    data = {
        "title": "Test Report",
        "period_start": "2023-01-01",
        "period_end": "2023-01-07",
        "products": []
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_generate()
