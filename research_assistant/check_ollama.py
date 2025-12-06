import requests
import json
import sys

def check_ollama():
    base_url = "http://localhost:11434"
    model = "nomic-embed-text"
    
    print(f"--- Checking Ollama at {base_url} ---")
    
    # 1. Check if Ollama is running
    try:
        requests.get(base_url)
        print("✅ Ollama is running")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Ollama. Is it running?")
        sys.exit(1)

    # 2. Check installed models
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            print(f"📋 Installed models: {', '.join(models)}")
            
            # Check for nomic-embed-text (exact or with :latest)
            if any(model in m for m in models):
                print(f"✅ Model '{model}' found!")
            else:
                print(f"❌ Model '{model}' NOT found.")
                print(f"👉 Please run: ollama pull {model}")
        else:
            print(f"❌ Failed to list models: {response.text}")
    except Exception as e:
        print(f"❌ Error checking models: {e}")

    # 3. Test Embeddings Endpoint (OpenAI Compatible)
    print("\n--- Testing Embedding Endpoint ---")
    embedding_url = f"{base_url}/v1/embeddings"
    payload = {
        "model": model,
        "input": "Test sentence"
    }
    
    try:
        resp = requests.post(embedding_url, json=payload)
        if resp.status_code == 200:
            print("✅ Embedding generation successful!")
        elif resp.status_code == 404:
             print("❌ Endpoint 404 Not Found.")
             print(f"   URL used: {embedding_url}")
             print("   This might mean the model is missing or the endpoint is wrong for this Ollama version.")
        else:
            print(f"❌ Embedding failed with status {resp.status_code}")
            print(f"   Response: {resp.text}")
    except Exception as e:
        print(f"❌ Error calling embeddings: {e}")

if __name__ == "__main__":
    check_ollama()
