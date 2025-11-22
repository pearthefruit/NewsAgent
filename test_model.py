import google.generativeai as genai
import os
import sys

# Add parent directory to path to import Common modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Common.config import GEMINI_API_KEYS

api_key = GEMINI_API_KEYS.get("financial_analysis")
if not api_key:
    print("No API key found for financial_analysis")
    sys.exit(1)

genai.configure(api_key=api_key)

models_to_test = ['gemini-2.5-pro', 'gemini-2.0-flash']

print(f"Testing API Key: {api_key[:5]}...", flush=True)

for model_name in models_to_test:
    print(f"\nTesting {model_name}...", flush=True)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello")
        print(f"Success: {response.text}", flush=True)
    except Exception as e:
        print(f"Failed: {str(e)[:100]}...", flush=True)
