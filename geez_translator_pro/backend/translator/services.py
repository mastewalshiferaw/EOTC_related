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
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)

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
    Fast & Accurate Image Preprocessor (~0.05s):
    1. Red-Ink Equalization: Extracts min(G, B) channels to ensure red liturgical ink
       (ቀይ ቀለም / rubrics) is as dark and legible as black ink on parchment.
    2. Adaptive Scaling: Rescales image to ~1200px optimal line height with cubic interpolation.
    3. Bilateral Denoising: Preserves Fidel vowel diacritics and loops while smoothing paper grain.
    Note: Artificial white border padding (copyMakeBorder value=255) is intentionally excluded
    as high-contrast borders fool Tesseract's layout analyzer into treating manuscripts as non-text.
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

        # Scale to optimal height (~1200px) with cubic interpolation
        h, w = blended.shape
        if max(h, w) < 1200:
            scale = 1200.0 / max(h, w)
            blended = cv2.resize(blended, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Gentle bilateral filter to smooth paper fibers without smudging Fidel vowel dots
        processed = cv2.bilateralFilter(blended, d=5, sigmaColor=50, sigmaSpace=50)
        return processed
    else:
        # Latin / English preprocessing with CLAHE and Otsu
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if max(h, w) < 1400:
            scale = 1400.0 / max(h, w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh


def restore_fidel_ocr_text(raw_text, provider=None):
    """
    High-Speed Post-OCR Formatting & Reconstruction Layer:
    Corrects optical character misrecognitions (e.g. ዶ->ይ, ቪ->ዚ, 'ቡ->አቡ, broken punctuation)
    and formats raw OCR into clean, authentic canonical Fidel using high-speed LLM inference.
    """
    if not raw_text or len(raw_text.strip()) < 3:
        return raw_text

    preferred = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()

    prompt = (
        "You are an expert scholar in Classical Ge'ez (ግዕዝ) and Ethiopian Orthodox Tewahedo liturgical manuscripts. "
        "The following text was extracted by optical OCR and contains optical scan errors "
        "('ቡነ -> አቡነ, ዘበሰማያጎ -> ዘበሰማያት, ጸሎት ዘዘወጉር -> ጸሎት ዘዘወትር, አስመ ቪአክ -> እስመ ዚአከ, broken punctuation). "
        "Please format and restore it into clean, canonical, authentic Classical Ge'ez text. "
        "Rules:\n"
        "- Output ONLY the clean restored Fidel text.\n"
        "- Do NOT translate or explain.\n"
        "- Preserve prayer lines and authentic Fidel punctuation (፡, ።, ፤)."
    )

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
                max_tokens=600
            )
            content = resp.choices[0].message.content or ""
            if content.strip():
                print("OCR Formatter: Successfully formatted with Groq (Fast)")
                return content.strip()
        return None

    def _call_gemini():
        client = get_gemini_client()
        if client:
            model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            response = client.models.generate_content(
                model=model,
                contents=f"{prompt}\n\n[RAW OCR TEXT]:\n{raw_text}"
            )
            if response.text and len(response.text.strip()) > 5:
                print("OCR Formatter: Successfully formatted with Gemini")
                return response.text.strip()
        return None

    # For formatting, if Gemini is preferred, try Gemini; but failover instantly to Groq if 429/busy
    if preferred == "gemini":
        try:
            res = _call_gemini()
            if res:
                return res
        except Exception as e:
            print(f"Gemini formatting unavailable ({e}), instantly falling back to fast Groq...")
        try:
            res = _call_groq()
            if res:
                return res
        except Exception as e2:
            print(f"Groq formatting error: {e2}")
    else:
        try:
            res = _call_groq()
            if res:
                return res
        except Exception as e:
            print(f"Groq formatting error ({e}), attempting Gemini fallback...")
        try:
            res = _call_gemini()
            if res:
                return res
        except Exception as e2:
            print(f"Gemini formatting error: {e2}")

    # If both fail, return raw OCR text safely without crashing
    return raw_text


def perform_hybrid_ocr(image_bytes, lang="amh", provider=None, auto_clean=True):
    """
    Intelligent Hybrid OCR Pipeline:
    1. Preprocesses image with Red-Ink Equalization and 40px Quiet-Zone Padding (~0.05s).
    2. Runs Local Tesseract OCR with --psm 6 (~0.4s).
    3. Formats & restores extracted Fidel text using the fast LLM formatter (~2-3s).
    4. Falls back to Gemini Vision if local Tesseract detects 0 characters.
    """
    is_ethiopic = ("amh" in lang.lower() or "ge'ez" in lang.lower() or "geez" in lang.lower())
    tess_lang = "amh" if is_ethiopic else "eng"

    try:
        # Step 1: Preprocess image (~0.05s)
        processed_cv = preprocess_image_bytes(image_bytes, is_ethiopic=is_ethiopic)
        
        # Step 2: Local Tesseract OCR (~0.3s)
        local_text = ""
        if processed_cv is not None:
            # Try PSM 3 (automatic layout) first for multi-line/paragraph manuscripts
            tess_config = "--psm 3 --oem 1"
            local_text = pytesseract.image_to_string(processed_cv, lang=tess_lang, config=tess_config).strip()
            
            # If PSM 3 yielded few characters (e.g. tightly cropped box), try PSM 6 (single block)
            fidel_count = len(re.findall(r'[\u1200-\u137F]', local_text)) if is_ethiopic else 0
            if is_ethiopic and fidel_count < 15:
                alt_text = pytesseract.image_to_string(processed_cv, lang=tess_lang, config="--psm 6 --oem 1").strip()
                if len(re.findall(r'[\u1200-\u137F]', alt_text)) > fidel_count:
                    local_text = alt_text

        # Step 3: Check character detection & run integrated AI polish directly
        if is_ethiopic:
            fidel_count = len(re.findall(r'[\u1200-\u137F]', local_text))
            if fidel_count >= 2:
                print(f"OCR Pipeline: Extracted {fidel_count} Fidel characters. Running integrated AI polish...")
                if auto_clean:
                    formatted_text = restore_fidel_ocr_text(local_text, provider=provider)
                    return formatted_text
                return local_text
        else:
            latin_count = len(re.findall(r'[a-zA-Z]', local_text))
            if latin_count >= 8:
                print(f"OCR Mode: Local Tesseract (Extracted {latin_count} Latin characters)")
                return local_text

        # Step 4: Cloud Vision Fallback only if local OCR found 0 text
        print("OCR Mode: Cloud Fallback (Gemini Vision)")
        try:
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
        except Exception as vision_err:
            print(f"Cloud Vision fallback bypassed ({vision_err})")

        return local_text if local_text else "No text detected."

    except Exception as e:
        print(f"OCR Pipeline Exception: {e}")
        return f"OCR Pipeline Error: {str(e)}"
