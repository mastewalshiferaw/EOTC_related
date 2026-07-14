import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os
import re

def extract_geez_from_image(image_path):
    """
    it will read our image and it will returns the extracted Ethiopic text
    (not a copy from AI...I am just trying to understand the code)
    """
    try:
        custom_config = r'--oem 3 --psm 3' 
        text = pytesseract.image_to_string(Image.open(image_path), lang='amh', config=custom_config)
        return text.strip()
    except Exception as e:
        return f"Error during OCR: {str(e)}"
   



def extract_text_from_any_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        # Convert PDF pages to images
        pages = convert_from_path(file_path)
        full_text = ""
        for page in pages:
            # Run OCR on each page
            text = pytesseract.image_to_string(page, lang='amh')
            full_text += text + "\n\n"
        return full_text
    else:
        # It's an image
        return extract_geez_from_image(file_path)
    


def clean_geez_text(text):
    # Remove weird OCR artifacts but keep Ge'ez characters and punctuation
    cleaned = re.sub(r'[^\u1200-\u137F\s፡።፣፤፥፦፧፨]', '', text)
    return cleaned.strip()