import requests
import json

BASE_URL = "http://localhost:8000"

def check_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Health Check Failed: {e}")

def test_chat():
    try:
        payload = {
            "message": "Hello Jarvis, can you hear me?",
            "model": "llama3-70b-8192" 
        }
        print("\nSending Chat Request...")
        # Note: Adjust endpoint if it's different in your current backend structure
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=10)
        print(f"Chat Status: {response.status_code}")
        print(response.text[:200]) # Print first 200 chars
    except Exception as e:
        print(f"Chat Request Failed: {e}")

if __name__ == "__main__":
    check_health()
    test_chat()
