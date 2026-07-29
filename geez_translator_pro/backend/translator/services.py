import os
import io
import pytesseract
from google import genai
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def perform_hybrid_ocr(image_bytes):
    """
    PORTFOLIO FEATURE: Hybrid OCR Pipeline
    1. Tesseract (Local/Free) for clear text.
    2. Gemini Vision (Cloud/Paid) for complex manuscripts.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Step 1: Try Local Tesseract
        # Note: Requires Tesseract installed on OS with 'amh' data
        local_text = pytesseract.image_to_string(img, lang='amh').strip()
        
        # If Tesseract did a good job (found more than 10 characters), return it
        if len(local_text) > 10:
            print("OCR Mode: Local (Tesseract)")
            return local_text

        # Step 2: Fallback to Gemini Vision if local fails
        print("OCR Mode: Cloud Fallback (Gemini)")
        prompt = "Extract Ge'ez text from this image. Output ONLY the raw text."
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt, img]
        )
        return response.text.strip() if response.text else "No text found."

    except Exception as e:
        return f"OCR Pipeline Error: {str(e)}"