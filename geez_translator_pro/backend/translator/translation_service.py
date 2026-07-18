import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_dual(text):
    """
    Returns a dictionary with both Amharic and English translations.
    """
    if not text: return {"amharic": "", "english": ""}

    prompt = f"""
    You are an expert linguist in Ancient Ge'ez. 
    Translate the following Ge'ez text into TWO languages: Amharic and English.
    
    Maintain a sacred, liturgical tone for both.
    Return the response in this EXACT format:
    AMHARIC: [translation]
    ENGLISH: [translation]

    Ge'ez Text:
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw_text = response.text
        
        # Simple parsing logic
        amh = raw_text.split("AMHARIC:")[1].split("ENGLISH:")[0].strip()
        eng = raw_text.split("ENGLISH:")[1].strip()
        
        return {"amharic": amh, "english": eng}
    except Exception as e:
        return {"amharic": f"Error: {str(e)}", "english": "Error"}