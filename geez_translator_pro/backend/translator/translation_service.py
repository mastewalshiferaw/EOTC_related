import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
from .models import TranslationCache

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)

_gemini_client = None
_groq_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key and api_key != "your_gemini_api_key_here":
            _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if api_key:
            _groq_client = Groq(api_key=api_key)
    return _groq_client


def build_system_prompt(source, target):
    return (
        f"You are an expert scholar and translator specializing in Classical Ge'ez (ግዕዝ), "
        f"Amharic (አማርኛ), and English. "
        f"Translate the following text accurately from {source} into natural, high-quality {target}. "
        "Rules:\n"
        "- Clean up minor OCR noise, misread punctuation, or broken characters.\n"
        "- Translate full sentences, prayers, or paragraphs faithfully.\n"
        "- Output ONLY the final translation without explanations, introductory remarks, or quotes."
    )


def translate_with_gemini(text, source, target):
    client = get_gemini_client()
    if not client:
        raise ValueError("Gemini API key is missing or invalid.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    prompt = build_system_prompt(source, target)
    response = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.3,
        ),
    )
    return response.text.strip() if response.text else ""


def translate_with_groq(text, source, target):
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key is missing.")
    model = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3.8-27b")
    prompt = build_system_prompt(source, target)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=1000,
    )
    msg = response.choices[0].message
    content = msg.content or ""
    return content.strip()


def translate_flexible(text, source, target, provider=None):
    """
    Unified dual-provider translation:
    - Supports 'gemini' and 'groq'
    - Respects dynamic provider parameter or .env default (LLM_PROVIDER)
    - Automatically falls back to the other provider if one encounters rate-limits or errors
    """
    if not text or not text.strip():
        return ""

    cleaned_text = text.strip()
    preferred_provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    # 1. Check database cache
    cached_hit = TranslationCache.objects.filter(
        source_text=cleaned_text,
        source_lang=source,
        target_lang=target
    ).first()

    if cached_hit:
        print("Cache Hit: Returning saved translation from database cache.")
        return cached_hit.translated_text

    # 2. Call AI Provider with auto-fallback
    translated_result = ""

    if preferred_provider == "groq":
        try:
            print(f"Calling Groq ({os.getenv('GROQ_TEXT_MODEL', 'qwen/qwen3.8-27b')})...")
            translated_result = translate_with_groq(cleaned_text, source, target)
        except Exception as e:
            print(f"Groq error ({e}), attempting Gemini fallback...")
            try:
                translated_result = translate_with_gemini(cleaned_text, source, target)
            except Exception as e2:
                return f"Translation Error: {str(e)} | Fallback: {str(e2)}"
    else:
        try:
            print(f"Calling Gemini ({os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')})...")
            translated_result = translate_with_gemini(cleaned_text, source, target)
        except Exception as e:
            print(f"Gemini error ({e}), attempting Groq fallback...")
            try:
                translated_result = translate_with_groq(cleaned_text, source, target)
            except Exception as e2:
                return f"Translation Error: {str(e)} | Fallback: {str(e2)}"

    # 3. Save to Cache
    if translated_result and not translated_result.startswith("Translation Error:"):
        try:
            TranslationCache.objects.create(
                source_text=cleaned_text,
                source_lang=source,
                target_lang=target,
                translated_text=translated_result
            )
        except Exception as cache_err:
            print(f"Cache Save Warning: {cache_err}")

    return translated_result
