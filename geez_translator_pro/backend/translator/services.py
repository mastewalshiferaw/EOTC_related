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
        img = Image.open(io.BytesIO(image_bytes))
        
        # Stricter OCR prompt
        prompt = "Extract all Ethiopic/English text from this image. Output ONLY the raw text found. No comments."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, img]
        )
        
        return response.text.strip() if response.text else ""
            
    except Exception as e:
        return f"OCR Error"