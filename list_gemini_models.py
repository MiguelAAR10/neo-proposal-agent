import os
import requests

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get("models", [])
        for m in models:
            print(f"{m.get('name')} - {m.get('displayName')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    list_models()
