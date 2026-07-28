import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

# Load env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source, target):
    if not text: return ""
    
    # We put the "Strict Dictionary" rules directly in the prompt
    # This avoids the 'types' configuration errors
    prompt = f"""
    TASK: Direct Dictionary Translation.
    RULES: 
    - Translate from {source} to {target}.
    - Provide ONLY the direct equivalent words.
    - NO sentences, NO explanations, NO 'The meaning is'.
    - Output ONLY the result.
    
    TEXT: {text}
    RESULT:
    """
    
    # We try your confirmed 2.0 model first, then fallback to the latest alias
    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
    
    for model_id in models:
        try:
            response = client.models.generate_content(
                model=model_id, 
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Model {model_id} failed: {e}")
            continue
            
    return "Error: Translation failed. Please try again in 10 seconds."