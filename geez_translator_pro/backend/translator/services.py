import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os
import re

def clean_geez_text(text):
    """Removes OCR noise but preserves Ge'ez script and punctuation."""
    # Keeps Ethiopic range (1200-137F) and Ethiopic punctuation
    cleaned = re.sub(r'[^\u1200-\u137F\s፡።፣፤፥፦፧፨]', '', text)
    return " ".join(cleaned.split())

def extract_text_from_any_file(file_path):
    """Detects file type and extracts Ge'ez text."""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.pdf':
            # Convert PDF to images (requires poppler installed on OS)
            pages = convert_from_path(file_path)
            full_text = ""
            for page in pages:
                text = pytesseract.image_to_string(page, lang='amh')
                full_text += text + "\n"
            return clean_geez_text(full_text)
        else:
            # Standard Image OCR
            text = pytesseract.image_to_string(Image.open(file_path), lang='amh')
            return clean_geez_text(text)
    except Exception as e:
        return f"OCR Error: {str(e)}"