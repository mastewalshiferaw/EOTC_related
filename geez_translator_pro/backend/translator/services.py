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
    Enhanced Image Preprocessing Pipeline:
    1. Red-Ink Equalization: Extracts min(G, B) channels to ensure red liturgical ink
       (ቀይ ቀለም / rubrics) is as dark and legible as black ink on parchment.
    2. Quiet-Zone Auto-Padding: Adds a clean 40px white border so Tesseract never clips
       character stems or fails baseline estimation on tightly cropped images.
    3. High-DPI Rescaling & Bilateral Denoising: Preserves Fidel vowel diacritics and loops.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    if is_ethiopic:
        # Red-ink liturgical equalization:
        red_equalized = np.minimum(img[:, :, 0], img[:, :, 1])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blended = cv2.addWeighted(red_equalized, 0.65, gray, 0.35, 0)

        # 40px white quiet-zone padding to stabilize Tesseract line/word segmentation on cropped boxes
        padded = cv2.copyMakeBorder(blended, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)

        # Rescale to optimal height (~1400px)
        h, w = padded.shape
        if max(h, w) < 1400:
            scale = 1400.0 / max(h, w)
            padded = cv2.resize(padded, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Gentle bilateral filter to smooth paper fibers without smudging Fidel vowel dots
        processed = cv2.bilateralFilter(padded, d=5, sigmaColor=50, sigmaSpace=50)
        return processed
    else:
        # Latin / English preprocessing with CLAHE and Otsu
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        padded = cv2.copyMakeBorder(gray, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
        h, w = padded.shape
        if max(h, w) < 1600:
            scale = 1600.0 / max(h, w)
            padded = cv2.resize(padded, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(padded)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh


def restore_fidel_ocr_text(raw_text, provider=None):
    """
    Intelligent Post-OCR Reconstruction Layer:
    Corrects optical character misrecognitions (e.g. ዶ->ይ, ቪ->ዚ, 'ቡ->አቡ, broken punctuation)
    using dual-provider LLM intelligence (Gemini / Groq), preserving authentic canonical Fidel.
    """
    if not raw_text or len(raw_text.strip()) < 10:
        return raw_text

    preferred = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    prompt = (
        "You are an expert scholar in Classical Ge'ez (ግዕዝ) and Ethiopian Orthodox Tewahedo liturgy. "
        "The text below was produced by an OCR engine from a liturgical text (e.g. ጸሎት ዘዘወትር / መጽሐፈ ጸሎት) "
        "and contains optical scanning errors (for example: 'ቡነ -> አቡነ, ዘበሰማያጎ -> ዘበሰማያት, ዘዘወጉር -> ዘዘወትር, "
        "አስመ ቪአክ -> እስመ ዚአከ, corrupted letters and punctuation). "
        "Please reconstruct and output the corrected, canonical Classical Ge'ez liturgical text. "
        "Rules:\n"
        "- Output ONLY the corrected Fidel text.\n"
        "- Do NOT provide English translation or commentary.\n"
        "- Do NOT add quotation marks or intro/outro text."
    )

    def _call_gemini():
        client = get_gemini_client()
        if client:
            model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            response = client.models.generate_content(
                model=model,
                contents=f"{prompt}\n\n[RAW OCR TEXT]:\n{raw_text}"
            )
            if response.text and len(response.text.strip()) > 5:
                print("Post-OCR Cleanup: Restored via Gemini")
                return response.text.strip()
        return None

    def _call_groq():
        from .translation_service import get_groq_client
        groq_client = get_groq_client()
        if groq_client:
            groq_model = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3.8-27b")
            resp = groq_client.chat.completions.create(
                model=groq_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": raw_text}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            content = resp.choices[0].message.content or ""
            if content.strip():
                print("Post-OCR Cleanup: Restored via Groq")
                return content.strip()
        return None

    if preferred == "groq":
        try:
            res = _call_groq()
            if res:
                return res
        except Exception as e:
            print(f"Groq restoration error ({e}), attempting Gemini fallback...")
        try:
            res = _call_gemini()
            if res:
                return res
        except Exception as e2:
            print(f"Gemini restoration error: {e2}")
    else:
        try:
            res = _call_gemini()
            if res:
                return res
        except Exception as e:
            print(f"Gemini restoration error ({e}), attempting Groq fallback...")
        try:
            res = _call_groq()
            if res:
                return res
        except Exception as e2:
            print(f"Groq restoration error: {e2}")

    # Fallback to raw OCR text if LLM restoration fails
    return raw_text


def perform_hybrid_ocr(image_bytes, lang="amh", provider=None):
    """
    Production-Grade Hybrid OCR Pipeline:
    1. Preprocesses image with Red-Ink Equalization and 40px Quiet-Zone Padding.
    2. Runs Tesseract with optimized Page Segmentation Mode (--psm 6 for cropped blocks).
    3. Multi-PSM fallback (--psm 4) if character density is low.
    4. Applies Post-OCR Contextual Restoration (Gemini/Groq) to fix optical Fidel typos.
    5. Falls back to Gemini Vision if local Tesseract detects no text.
    """
    is_ethiopic = ("amh" in lang.lower() or "ge'ez" in lang.lower() or "geez" in lang.lower())
    tess_lang = "amh" if is_ethiopic else "eng"

    try:
        # Step 1: Preprocess image
        processed_cv = preprocess_image_bytes(image_bytes, is_ethiopic=is_ethiopic)
        
        # Step 2: Local Tesseract OCR with --psm 6 (Uniform text block)
        local_text = ""
        if processed_cv is not None:
            tess_config = "--psm 6 --oem 1"
            local_text = pytesseract.image_to_string(processed_cv, lang=tess_lang, config=tess_config).strip()
            
            # If PSM 6 yielded few characters, try PSM 4
            fidel_count = len(re.findall(r'[\u1200-\u137F]', local_text)) if is_ethiopic else 0
            if is_ethiopic and fidel_count < 8:
                alt_text = pytesseract.image_to_string(processed_cv, lang=tess_lang, config="--psm 4 --oem 1").strip()
                if len(re.findall(r'[\u1200-\u137F]', alt_text)) > fidel_count:
                    local_text = alt_text

        # Step 3: Validate character detection
        if is_ethiopic:
            fidel_count = len(re.findall(r'[\u1200-\u137F]', local_text))
            if fidel_count >= 5:
                print(f"OCR Mode: Local Tesseract (Extracted {fidel_count} Fidel characters)")
                # Step 4: Apply Post-OCR Contextual Restoration
                restored_text = restore_fidel_ocr_text(local_text, provider=provider)
                return restored_text
        else:
            latin_count = len(re.findall(r'[a-zA-Z]', local_text))
            if latin_count >= 8:
                print(f"OCR Mode: Local Tesseract (Extracted {latin_count} Latin characters)")
                return local_text

        # Step 5: Cloud Vision Fallback (Gemini Vision)
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

        # If cloud fallback unavailable, return whatever Tesseract found
        return local_text if local_text else "No text detected."

    except Exception as e:
        print(f"OCR Pipeline Exception: {e}")
        return f"OCR Pipeline Error: {str(e)}"
