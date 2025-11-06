import google.generativeai as genai
from dotenv import load_dotenv
import os

def check_available_models():
    # Load environment variables
    load_dotenv()
    
    # Configure API
    api_key = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        for m in genai.list_models():
            print(f"Model Name: {m.name}")
            print(f"Display Name: {m.display_name}")
            print(f"Description: {m.description}")
            print(f"Generation Methods: {', '.join(m.supported_generation_methods)}")
            print("-" * 50)
    except Exception as e:
        print(f"Error checking models: {str(e)}")

if __name__ == "__main__":
    check_available_models()