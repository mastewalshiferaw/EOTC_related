import os
import io
import re
from google.cloud import vision
from PIL import Image, ImageOps, ImageEnhance

from dotenv import load_dotenv
load_dotenv()

# This line is the fix:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Make sure you have your Google Cloud JSON key path here
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-file.json"

def clean_geez_text(text):
    cleaned = re.sub(r'[^\u1200-\u137F\s፡።፣፤፥፦፧፨]', '', text)
    return " ".join(cleaned.split())

def perform_top_tier_ocr(image_bytes):
    """
    Uses Google Cloud Vision for high-accuracy Ethiopic OCR.
    """
    try:
        # Preprocessing: Convert to Grayscale and increase contrast
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.grayscale(img)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Save back to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        processed_bytes = img_byte_arr.getvalue()

        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=processed_bytes)
        
        # Use DOCUMENT_TEXT_DETECTION for manuscripts
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            return f"OCR Error: {response.error.message}"
            
        return clean_geez_text(response.full_text_annotation.text)
    except Exception as e:
        return f"System Error: {str(e)}"