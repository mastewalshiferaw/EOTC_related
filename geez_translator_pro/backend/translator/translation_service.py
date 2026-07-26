import os
from google import genai
from google.genai import types # Import types for configuration
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source, target):
    if not text: return ""
    
    # 1. Define a strict system instruction to force short, direct outputs
    sys_instruction = (
        "You are a direct translation dictionary tool. "
        "Provide ONLY the direct meaning, literal translation, or equivalent term. "
        "Do NOT write long sentences, introductions, or explanations. "
        "Keep it concise: just 'this to this'."
    )
    
    prompt = f"Translate this {source} text to {target}: {text}"
    
    try:
        # 2. Pass the system instruction in the config
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.1 # Low temperature makes it deterministic and strict
            )
        )
        return response.text.strip()
    except Exception as e:
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction,
                    temperature=0.1
                )
            )
            return response.text.strip()
        except:
            return f"Error: {str(e)}"