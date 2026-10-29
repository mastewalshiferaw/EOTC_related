import os
import io
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract
from google import genai
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Detect Tesseract executable on Windows if not already on PATH
DEFAULT_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]
for p in DEFAULT_TESSERACT_PATHS:
    if os.path.isfile(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break

_gemini_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key and api_key != "your_gemini_api_key_here":
            _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def preprocess_image_bytes(image_bytes, is_ethiopic=True):
    """
    Language-adaptive image preprocessing using OpenCV:
    - Ethiopic (Ge'ez/Amharic): Bicubic scaling + bilateral filter to preserve Fidel vowel marks.
    - Latin (English): Bicubic scaling + CLAHE + Otsu binarization.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    if is_ethiopic:
        # Scale to ~1200px to ensure stroke thickness without fragmentation
        if max(h, w) < 1200:
            scale = 1200.0 / max(h, w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        # Gentle bilateral filter removes noise/paper texture while keeping Fidel dots/accents
        processed = cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)
        return processed
    else:
        # English / Latin: sharp contrast binarization
        if max(h, w) < 1600:
            scale = 1600.0 / max(h, w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh


def perform_hybrid_ocr(image_bytes, lang="amh"):
    """
    Enhanced Hybrid OCR Pipeline:
    1. Preprocesses image adaptively (Ethiopic vs English).
    2. Runs local Tesseract OCR with dedicated language model.
    3. Validates actual character quality (not just character count).
    4. Falls back to Gemini Vision (gemini-3.8-flash) if local OCR fails or produces noise.
    """
    is_ethiopic = ("amh" in lang.lower() or "ge'ez" in lang.lower() or "geez" in lang.lower())
    tess_lang = "amh" if is_ethiopic else "eng"

    try:
        # Step 1: Preprocess image
        processed_cv = preprocess_image_bytes(image_bytes, is_ethiopic=is_ethiopic)
        
        # Step 2: Local Tesseract OCR
        if processed_cv is not None:
            local_text = pytesseract.image_to_string(processed_cv, lang=tess_lang).strip()
        else:
            pil_img = Image.open(io.BytesIO(image_bytes))
            local_text = pytesseract.image_to_string(pil_img, lang=tess_lang).strip()

        # Step 3: Check quality
        if is_ethiopic:
            # Count actual Ethiopic Fidel characters (\u1200 - \u137F)
            fidel_count = len(re.findall(r'[\u1200-\u137F]', local_text))
            if fidel_count >= 5:
                print(f"OCR Mode: Local Tesseract (Extracted {fidel_count} Fidel characters)")
                return local_text
        else:
            latin_count = len(re.findall(r'[a-zA-Z]', local_text))
            if latin_count >= 8:
                print(f"OCR Mode: Local Tesseract (Extracted {latin_count} Latin characters)")
                return local_text

        # Step 4: Intelligent Cloud Fallback to Gemini Vision
        print("OCR Mode: Cloud Fallback (Gemini Vision)")
        client = get_gemini_client()
        if client:
            pil_img = Image.open(io.BytesIO(image_bytes))
            target_script = "Ge'ez or Amharic" if is_ethiopic else "English"
            prompt = (
                f"Transcribe all text from this image exactly as written in {target_script}. "
                "Output ONLY the transcribed raw text, without comments or formatting."
            )
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
                contents=[prompt, pil_img]
            )
            if response.text and response.text.strip():
                return response.text.strip()

        # If cloud fallback unavailable or empty, return what Tesseract found
        return local_text if local_text else "No text detected."

    except Exception as e:
        print(f"OCR Pipeline Exception: {e}")
        return f"OCR Pipeline Error: {str(e)}"
