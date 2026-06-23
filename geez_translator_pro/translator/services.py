import pytesseract
from PIL import Image
import os

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
   
    
