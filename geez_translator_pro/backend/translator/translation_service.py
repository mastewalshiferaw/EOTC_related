import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

# Absolute path loading to prevent "File Not Found"
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source, target):
    if not text: return ""
    
    # Rational Prompt
    prompt = f"Expert Translation. Source ({source}): {text}. Target: {target}. Tone: Scholarly/Liturgical."
    
    # Try models in order of stability
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-pro"]
    
    for model_id in models_to_try:
        try:
            response = client.models.generate_content(model=model_id, contents=prompt)
            if response.text:
                return response.text.strip()
        except Exception:
            continue # Try next model if this one 404s
            
    return "Error: All AI models failed. Check your API key at aistudio.google.com"