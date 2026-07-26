import os
import io
from google import genai
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image

# Absolute path loading
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def perform_top_tier_ocr(image_bytes):
    try:
        # Load the image
        img = Image.open(io.BytesIO(image_bytes))
        
        prompt = "Extract all Ge'ez (Ethiopic) text from this image. Output ONLY the text found."

        # USE THE EXACT MODEL FROM YOUR LIST
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, img]
        )
        
        if response.text:
            return response.text.strip()
        else:
            return "No text detected."
            
    except Exception as e:
        # If 2.0 fails, try the absolute 'latest' alias
        try:
            response = client.models.generate_content(model="gemini-flash-latest", contents=[prompt, img])
            return response.text.strip()
        except:
            return f"Gemini Vision Error: {str(e)}"