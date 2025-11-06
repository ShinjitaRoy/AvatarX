import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_available_models():
    # Load API key from .env
    load_dotenv()
    
    # Configure Gemini with your API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env file")
        return
        
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        print("Available Models:")
        print("-" * 50)
        for m in genai.list_models():
            print(f"Model Name: {m.name}")
            print(f"Display Name: {m.display_name}")
            print(f"Description: {m.description}")
            print(f"Generation Methods: {m.supported_generation_methods}")
            print("-" * 50)
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()