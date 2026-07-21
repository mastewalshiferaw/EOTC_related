import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

# Load env from backend root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source_lang="Ge'ez", target_lang="Amharic"):
    """
    High-stability translation using Gemini 1.5 Flash.
    """
    if not text:
        return ""

    try:
        # 1.5 Flash is highly stable for the free tier
        model_id = "gemini-1.5-flash"

        prompt = f"""
        You are a scholar of Ethiopic studies. 
        Translate this text from {source_lang} to {target_lang}.
        Maintain a formal, liturgical tone.

        Text: {text}
        """

        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        return response.text.strip() if response.text else "AI Error: Empty response."

    except Exception as e:
        if "429" in str(e):
            return "Error: Quota exceeded. Please wait 30 seconds."
        return f"Translation Error: {str(e)}"