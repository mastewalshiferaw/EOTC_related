import os
import io
from google.cloud import vision
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend folder
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def perform_top_tier_ocr(image_bytes):
    # GET THE JSON FILENAME FROM .ENV
    cred_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # BUILD THE ABSOLUTE PATH (Point to the backend folder)
    base_dir = Path(__file__).resolve().parent.parent
    cred_path = base_dir / cred_file

    # CHECK IF FILE EXISTS BEFORE RUNNING
    if not cred_path.exists():
        return f"System Error: Credentials file not found at {cred_path}"

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cred_path)

    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            return f"Google Error: {response.error.message}"
            
        return response.full_text_annotation.text.strip()
    except Exception as e:
        return f"OCR System Error: {str(e)}"