import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source_lang, target_lang):
    if not text: return ""

    prompt = f"""
    Translate this text from {source_lang} to {target_lang}.
    If it is Ge'ez, use a formal liturgical tone.
    Source: {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"