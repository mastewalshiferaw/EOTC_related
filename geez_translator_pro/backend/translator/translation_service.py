import os
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")


if api_key:
    genai.configure(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")

def translate_text(text, target_lang="amh_Ethi"):
    """
    Translates Ge'ez text using Google Gemini 1.5 Flash.
    """
    if not text or len(text.strip()) == 0:
        return ""

    # Mapping frontend codes to human-readable names
    lang_map = {
        "amh_Ethi": "Amharic",
        "eng_Latn": "English"
    }
    target = lang_map.get(target_lang, "Amharic")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert linguist specializing in Ancient Ge'ez (Ethiopic). 
        Translate the following Ge'ez text into clear, accurate {target}. 
        
        If the text is liturgical (EOTC), biblical, or prayer-based, 
        maintain the traditional sacred tone and poetic flow. 
        If there are multiple possible interpretations, provide the most accepted one.

        Ge'ez Text:
        {text}
        
        Translation:
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
        else:
            return "AI Error: Received an empty response."
            
    except Exception as e:
        return f"Gemini API Error: {str(e)}"