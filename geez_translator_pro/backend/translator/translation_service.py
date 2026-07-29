import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path
from .models import TranslationCache

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def translate_flexible(text, source, target):
    if not text: return ""

    
    # Check if we have translated this before
    cached_hit = TranslationCache.objects.filter(
        source_text=text.strip(),
        source_lang=source,
        target_lang=target
    ).first()

    if cached_hit:
        print(f"Cache Hit: Returning saved translation for '{text[:10]}...'")
        return cached_hit.translated_text

    # If not in cache, call the AI
    print(f"Cache Miss: Calling Gemini API for '{text[:10]}...'")
    prompt = f"Direct Dictionary Translation. Source ({source}): {text}. Target: {target}. Rules: No sentences, no explanations, only the equivalent result."
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        translated_result = response.text.strip()

        # Save to cache for next time
        TranslationCache.objects.create(
            source_text=text.strip(),
            source_lang=source,
            target_lang=target,
            translated_text=translated_result
        )

        return translated_result
    except Exception as e:
        return f"AI Error: {str(e)}"