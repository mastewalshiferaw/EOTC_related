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
    
    # STRICT SYSTEM INSTRUCTIONS
    # We tell the AI it is a 'one-to-one' mapper.
    sys_instruction = (
        "You are a strict Ge'ez/Amharic/English direct dictionary. "
        "Rules: "
        "1. Provide ONLY the direct equivalent words or short phrases. "
        "2. Do NOT provide definitions, explanations, or sentences. "
        "3. Do NOT use conversational filler like 'This means' or 'The translation is'. "
        "4. If multiple meanings exist, separate them by a comma. "
        "Example Input: 'በስመ አብ' | Output: 'In the name of the Father'"
    )
    
    prompt = f"Translate {source} to {target}: {text}"
    
    try:
        from google.genai import types
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.0 # Force maximum accuracy and zero creativity
            )
        )
        return response.text.strip()
    except Exception as e:
        # Fallback logic remains same but with strict config
        return f"Error"