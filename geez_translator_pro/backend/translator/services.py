import os
import io
from google.cloud import vision
from pathlib import Path
from dotenv import load_dotenv

# Setup paths relative to this file
# This finds the 'backend' folder
BASE_DIR = Path(__file__).resolve().parent.parent 
load_dotenv(dotenv_path=BASE_DIR / '.env')

def perform_top_tier_ocr(image_bytes):
    """
    Uses Google Cloud Vision to extract Ge'ez text from images/pastes.
    """
    # Securely located the credentials file
    cred_filename = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_filename:
        return "System Error: GOOGLE_APPLICATION_CREDENTIALS not set in .env"
        
    cred_path = BASE_DIR / cred_filename

    if not cred_path.exists():
        return f"System Error: JSON key not found at {cred_path}"

    # setted environment variable for this session
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cred_path)

    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        
        # Using DOCUMENT_TEXT_DETECTION for better manuscript handling
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            return f"Google Cloud Error: {response.error.message}"
            
        text = response.full_text_annotation.text
        return text.strip() if text else "No text detected in image."

    except Exception as e:
        return f"OCR System Error: {str(e)}"