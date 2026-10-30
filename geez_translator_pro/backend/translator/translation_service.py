import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
from .ethiopian_numbers import (
    normalize_ethiopian_numbers,
    extract_geez_number_mappings,
    replace_geez_numbers_with_arabic,
    replace_arabic_numbers_with_geez,
)

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


def sanitize_translation_text(text):
    """
    Cleans up common LLM artifacts:
    1. Removes degenerate repeating loops (consecutive duplicate phrases/sentences).
    2. Strips conversational preambles (e.g., 'እነሆ ትርጉሙ:', 'Here is the translation:').
    """
    if not text:
        return ""
    # Remove consecutive repeating phrases/sentences (at least 6 chars repeated 2+ times)
    pattern = r'(.{6,}?)\s*(?:\1\s*){2,}'
    cleaned = re.sub(pattern, r'\1 ', text)
    # Strip conversational preambles
    cleaned = re.sub(r'^(?:እነሆ\s*ትርጉሙ|ትርጉም|Translation|Here is the translation)\s*[:፡\-]*\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def build_system_prompt(source, target):
    return (
        f"You are a revered linguist and master translator of Ethiopian languages, specializing in Classical Ge'ez (ግዕዝ), "
        f"Amharic (አማርኛ), and English.\n"
        f"Your task is to translate the provided text from {source} into natural, elegant, culturally authentic {target}.\n"
        "Strict Guidelines:\n"
        f"1. Output ONLY the direct {target} translation. Never include preambles, introductory filler, or notes.\n"
        "2. For liturgical or sacred prayers, use standard, reverent phrasing faithful to Ethiopian Orthodox Tewahedo Church (EOTC) tradition "
        "(e.g. 'አቡነ ዘበሰማያት' -> 'አባታችን ሆይ በሰማያት የምትኖር...', 'በሰላመ ቅዱስ ገብርኤል' -> 'እመቤታችን ቅድስት ድንግል ማርያም ሆይ በመልአኩ በቅዱስ ገብርኤል ሰላምታ...').\n"
        "3. Translate full thoughts coherently into natural, flowing sentences. Avoid robotic literal glossing.\n"
        "4. Do NOT repeat words, phrases, or conversational sentences.\n"
        "5. Preserve original prayer stanza line breaks and authentic Fidel punctuation.\n"
        "6. ETHIOPIAN / GE'EZ NUMERAL TRANSLATION RULES:\n"
        "   - Classical Ge'ez numerals use: ፩=1, ፪=2, ፫=3, ፬=4, ፭=5, ፮=6, ፯=7, ፰=8, ፱=9, ፲=10, ፳=20, ፴=30, ፵=40, ፶=50, ፷=60, ፸=70, ፹=80, ፺=90, ፻=100, ፼=10,000.\n"
        "   - When translating from Ge'ez to Amharic or English, you MUST translate all Ge'ez numerals into standard Arabic digits or standard written words (e.g. 'ምዕራፍ ፩' -> 'ምዕራፍ 1' or 'Chapter 1', 'ቁጥር ፭' -> 'ቁጥር 5' or 'Verse 5', '፲፭' -> '15', '፪ሺ፲፯' -> '2017'). NEVER leave raw, untranslated Ge'ez numerals in Amharic or English output.\n"
        "   - When translating from English or Amharic to Ge'ez, translate all numbers into authentic Classical Ge'ez numerals (e.g. '1' -> '፩', '5' -> '፭', '10' -> '፲', '15' -> '፲፭', '100' -> '፻')."
    )


def prepare_translation_prompt(text, source, target):
    prompt = build_system_prompt(source, target)
    extra_notes = []
    if re.search(r'[፩-፼]', text):
        mappings = extract_geez_number_mappings(text)
        if mappings:
            extra_notes.append(f"Ge'ez numeral values: {mappings}")

    notes_str = f" [Note: {'; '.join(extra_notes)}]" if extra_notes else ""
    user_content = f"Text to translate from {source} to {target}{notes_str}:\n\"\"\"\n{text}\n\"\"\"\n\nDirect {target} translation:"
    return prompt, user_content


def translate_with_gemini(text, source, target):
    client = get_gemini_client()
    if not client:
        raise ValueError("Gemini API key is missing or invalid.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    prompt, user_content = prepare_translation_prompt(text, source, target)
    response = client.models.generate_content(
        model=model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.2,
        ),
    )
    res = response.text.strip() if response.text else ""
    cleaned = sanitize_translation_text(res)
    return normalize_ethiopian_numbers(cleaned, source, target)


def translate_with_groq(text, source, target):
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key is missing.")
    model = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3.8-27b")
    prompt, user_content = prepare_translation_prompt(text, source, target)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=1000,
    )
    msg = response.choices[0].message
    content = msg.content or ""
    cleaned = sanitize_translation_text(content)
    return normalize_ethiopian_numbers(cleaned, source, target)


def translate_flexible(text, source, target, provider=None):
    """
    Unified dual-provider translation:
    - Supports 'gemini' and 'groq'
    - Real-time live inference on every request (no stale cache)
    - Automatically falls back to the other provider if one encounters rate-limits or errors
    """
    if not text or not text.strip():
        return ""

    cleaned_text = text.strip()
    preferred_provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    # Call AI Provider with auto-fallback
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

    return translated_result


def translate_stream_with_gemini(text, source, target):
    client = get_gemini_client()
    if not client:
        raise ValueError("Gemini API key is missing or invalid.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    prompt, user_content = prepare_translation_prompt(text, source, target)
    response_stream = client.models.generate_content_stream(
        model=model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.2,
        ),
    )
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text


def translate_stream_with_groq(text, source, target):
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key is missing.")
    model = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3.8-27b")
    prompt, user_content = prepare_translation_prompt(text, source, target)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=1000,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
        if delta:
            yield delta


def translate_stream_flexible(text, source, target, provider=None):
    """
    Streaming generator for live translation:
    - Yields text tokens/chunks in real time
    - Supports Gemini and Groq with automatic fallback
    """
    if not text or not text.strip():
        return

    cleaned_text = text.strip()
    preferred_provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    if preferred_provider == "groq":
        try:
            for chunk in translate_stream_with_groq(cleaned_text, source, target):
                yield chunk
        except Exception as e:
            print(f"Groq stream error ({e}), attempting Gemini fallback...")
            try:
                for chunk in translate_stream_with_gemini(cleaned_text, source, target):
                    yield chunk
            except Exception as e2:
                yield f"\n[Translation Error: {str(e)} | Fallback: {str(e2)}]"
    else:
        try:
            for chunk in translate_stream_with_gemini(cleaned_text, source, target):
                yield chunk
        except Exception as e:
            print(f"Gemini stream error ({e}), attempting Groq fallback...")
            try:
                for chunk in translate_stream_with_groq(cleaned_text, source, target):
                    yield chunk
            except Exception as e2:
                yield f"\n[Translation Error: {str(e)} | Fallback: {str(e2)}]"

