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


PREAMBLE_RE = re.compile(
    r'^(?:እነሆ\s*ትርጉሙ|ትርጉም|Translation|Here is the translation)\s*[:፡\-]*\s*',
    re.IGNORECASE,
)


def strip_translation_preamble(text):
    """Drop a leading "Here is the translation:" style line."""
    if not text:
        return ""
    return PREAMBLE_RE.sub('', text, count=1)


def sanitize_translation_text(text):
    """
    Cleans up common LLM artifacts:
    1. Removes degenerate repeating loops (consecutive duplicate phrases/sentences).
    2. Strips conversational preambles (e.g., 'እነሆ ትርጉሙ:', 'Here is the translation:').

    Note: loop collapsing needs a unit of at least 6 characters repeated three
    times in total, so short-token stutter ("ሰላም ሰላም ሰላም") is deliberately kept —
    liturgical texts repeat short phrases legitimately.
    """
    if not text:
        return ""
    # Remove consecutive repeating phrases/sentences (at least 6 chars repeated 2+ times)
    pattern = r'(.{6,}?)\s*(?:\1\s*){2,}'
    cleaned = re.sub(pattern, r'\1 ', text)
    return strip_translation_preamble(cleaned).strip()


RELIGIOUS_PATTERNS = [
    r'እግዚአብሔር', r'አምላክ', r'ክርስቶስ', r'ማርያም', r'ድንግል', r'ገብርኤል', r'ሚካኤል',
    r'መላእክት', r'ሰላም\s*ለኪ', r'አቡነ\s*ዘበሰማያት', r'ስብሐት', r'ይትባረክ', r'ቅዱስ',
    r'ሃይማኖት', r'ቤተክርስቲያን', r'ካህን', r'ዲያቆን', r'መስቀል', r'ሥላሴ', r'መንፈስ\s*ቅዱስ',
    r'ጸሎት', r'ቅዳሴ', r'ማኅሌት', r'ውዳሴ', r'ምልእተ\s*ጸጋ', r'ጸባዖት', r'ሰአሊ',
    r'ይስረይ', r'ኃጣው', r'ኃጢአት', r'ንስሐ', r'በረከት', r'ከርሥ', r'ፍቁር\s*ወልድ',
    r'ወንጌል', r'ሐዋርያ', r'ነቢይ', r'ፃድቅ', r'ሰማዕት', r'ተፈሥሒ',
    r'ወረብ', r'ድጓ', r'ዚቅ', r'መዋድስ', r'ቅኔ', r'መልክዕ', r'ሰቆቃወ', r'ሐረገ\s*ወይን', r'ጽጌ',
    r'\bgod\b', r'\blord\b', r'\bchrist\b', r'\bjesus\b', r'\bmary\b', r'\bvirgin\b',
    r'\bsaint\b', r'\bangel\b', r'\bgabriel\b', r'\bmichael\b', r'\bprayer\b',
    r'\bhymn\b', r'\bliturgy\b', r'\bgospel\b', r'\bapostle\b', r'\btrinity\b',
    r'\bchurch\b', r'\bsacred\b', r'\bholy\b', r'\bblessed\b', r'\bgrace\b',
    r'\bintercede\b', r'\bsaviour\b', r'\bsavior\b', r'\bsabaoth\b', r'\bamen\b',
    r'\bmahlet\b', r'\bwereb\b', r'\bdeggwa\b', r'\bziq\b', r'\bmalk[a\']?\b'
]


def is_religious_context(text: str) -> bool:
    if not text:
        return False
    return any(re.search(pat, text, re.IGNORECASE) for pat in RELIGIOUS_PATTERNS)


def build_system_prompt(source, target):
    return (
        f"You are a revered linguist, master philologist, and scholar of Ethiopian Semitic languages, "
        f"specializing in Classical Ge'ez (ግዕዝ), Amharic (አማርኛ), and English, with deep mastery of "
        f"Ethiopian Orthodox Tewahedo Church (EOTC) hymnody, patristics, and liturgical poetry.\n\n"
        f"Your task is to translate the provided text from {source} into natural, elegant, culturally authentic, and context-appropriate {target}.\n\n"
        "Strict Translation Guidelines:\n\n"
        "1. OUTPUT FORMAT:\n"
        f"   - Output ONLY the direct {target} translation.\n"
        "   - Never include preambles, introductory filler, explanations, commentaries, or notes.\n\n"
        "2. LITURGICAL & HYMNODIC TEXTS (Mahlet, Wereb, Deggwa, Prayers):\n"
        "   - AUTOMATIC SACRED DETECTION: Any Ge'ez text drawn from or resembling EOTC liturgical traditions—including "
        "Mahlet (ማኅሌት), Mahlete Tsige (ማኅሌተ ጽጌ), Wereb (ወረብ), Deggwa / Tsome Deggwa (ድጓ / ጾመ ድጓ), Ziq (ዚቅ), "
        "Mawaddis (መዋድስ), Qine (ቅኔ), Malk'a (መልክዕ), Saqoqawa Dengel (ሰቆቃወ ድንግል), or Widase Maryam (ውዳሴ ማርያም)—MUST be treated as Sacred Liturgical Poetry.\n"
        "   - THEOLOGICAL TYPOLOGY (ANDEMTA): Do NOT translate liturgical poetry literally as secular or botanical nature texts. Recognize canonical EOTC typology:\n"
        "     * In Marian hymns (e.g., Mahlete Tsige), images of flowers (ጽጌ), plants, vines (ሐረገ ወይን), fleece (ጸምር), dew (ጠል), dawn, and gardens refer typologically to the Holy Theotokos (St. Mary) and our Lord Jesus Christ.\n"
        "     * Translate with standard EOTC liturgical terminology and reverence (e.g., 'ጸባዖት' -> 'የሠራዊት ጌታ / Lord of Hosts', 'ምልእተ ጸጋ' -> 'ጸጋን የተመላሽ / Full of Grace', 'ሰአሊ ለነ' -> 'አማልጂን / ለምኚልን', 'ይስረይ ለነ ኃጣውኢነ' -> 'ኃጢአታችንን ያስተሰርይልን ዘንድ').\n"
        "   - WEREB & SHORT HYMN CHANTS:\n"
        "     * When translating short fragments or individual chant lines (ወረብ / ዚቅ), understand their liturgical context and render them into coherent, sacred, and poetic sentences rather than broken, word-by-word fragments.\n\n"
        "3. SECULAR & CONTEMPORARY TEXTS:\n"
        "   - Only apply secular registers to clearly profane, conversational, administrative, legal, or modern everyday texts that lack ecclesiastical vocabulary.\n"
        "   - For purely secular texts, do NOT inject pious blessings or religious phrasing where none exists.\n\n"
        "4. TARGET LANGUAGE STYLISTIC PURITY:\n"
        "   - When Target is Amharic (አማርኛ): Use traditional church Amharic phrasing for liturgical works (በኢትዮጵያ ኦርቶዶክስ ተዋሕዶ ቤተክርስቲያን የትርጓሜና የማኅሌት ሥርዓት መሠረት); use natural modern Amharic for secular works.\n"
        "   - When Target is Classical Ge'ez (ግዕዝ): Output pure Classical Ge'ez grammar, vocabulary, and Fidel. Never mix Amharic loanwords or modern syntax into Ge'ez.\n"
        "   - When Target is English: Use elevated, reverent ecclesiastical English (reminiscent of liturgical hymnals) for church texts, and clear, idiomatic English for secular texts.\n\n"
        "5. NUMERAL TRANSLATION RULES:\n"
        "   - Classical Ge'ez numerals: ፩=1, ፪=2, ፫=3, ፬=4, ፭=5, ፮=6, ፯=7, ፰=8, ፱=9, ፲=10, ፳=20, ፴=30, ፵=40, ፶=50, ፷=60, ፸=70, ፹=80, ፺=90, ፻=100, ፼=10,000.\n"
        "   - Ge'ez -> Amharic / English: Translate ALL Ge'ez numerals into standard Arabic digits (e.g., 'ምዕራፍ ፩' -> 'ምዕራፍ 1' or 'Chapter 1', '፲፭' -> '15'). NEVER leave raw Ge'ez numerals in Amharic or English output.\n"
        "   - English / Amharic -> Ge'ez: Translate ALL Arabic numbers into authentic Ge'ez numerals (e.g., '1' -> '፩', '12' -> '፲፪', '100' -> '፻').\n\n"
        "6. STRUCTURE:\n"
        "   - Preserve original hymnal verse meter, poetic line breaks, and punctuation (፡ ፣ ፤ ፥ ።)."
    )


def prepare_translation_prompt(text, source, target):
    prompt = build_system_prompt(source, target)
    extra_notes = []

    # Detect religious vs secular context
    if is_religious_context(text):
        extra_notes.append("Context: Religious / Liturgical — translate with authentic ecclesiastical reverence in the sense of Ethiopian Orthodox Tewahedo Church tradition")
    else:
        extra_notes.append("Context: General / Secular prose — translate naturally without unneeded religious terms")

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
        max_tokens=4096,
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
    preferred_provider = str(provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

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
            print(f"Calling Gemini ({os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')})...")
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
        max_tokens=4096,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
        if delta:
            yield delta


# Characters that can belong to a number in either direction. A numeral may be
# split across two LLM chunks ("፲" then "፭"), so a trailing run of them is held
# back until it is complete; converting the halves separately would give "105"
# instead of "15".
_NUMERAL_TAIL_CHARS = set("፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼ሺ0123456789")


_PREAMBLE_PHRASES = ("እነሆ ትርጉሙ", "ትርጉም", "translation", "here is the translation")
# Any character that can appear in a preamble line plus its separators.
_PREAMBLE_CHARS = set(" ".join(_PREAMBLE_PHRASES).lower()) | set(" :፡-\t\n")
_PREAMBLE_MAX_HOLD = 40


def _is_partial_preamble(text):
    """True while text could still grow into a preamble that must be stripped.

    The preamble can be split over several chunks ("Here is the " +
    "translation: "), so the head is held back for a moment. Judging by
    character set rather than by prefix keeps the leftover ": " separator from
    being emitted when it lands in the chunk after the words.
    """
    head = text.lstrip()
    if not head:
        return True
    return set(head.lower()) <= _PREAMBLE_CHARS


def _split_off_numeral_tail(text):
    """Split text into (safe_to_convert, trailing_numeral_run)."""
    cut = len(text)
    while cut > 0 and text[cut - 1] in _NUMERAL_TAIL_CHARS:
        cut -= 1
    return text[:cut], text[cut:]


def postprocess_translation_stream(chunks, source, target):
    """Apply the batch path's post-processing to a chunk stream.

    The batch endpoint sanitizes and normalizes the finished text; without this
    the SSE endpoint (the only one the UI uses) leaked raw Ge'ez numerals into
    Amharic/English output. Loop collapsing stays batch-only: it needs the whole
    response, and buffering it would defeat streaming.
    """
    pending = ""
    head = ""
    started = False

    for chunk in chunks:
        if not chunk:
            continue

        if not started:
            head += chunk
            if _is_partial_preamble(head) and len(head) < _PREAMBLE_MAX_HOLD:
                continue
            chunk = strip_translation_preamble(head)
            head = ""
            started = True
            if not chunk:
                continue

        pending += chunk
        ready, pending = _split_off_numeral_tail(pending)
        if ready:
            yield normalize_ethiopian_numbers(ready, source, target)

    if not started:
        # Whole response was shorter than the preamble decision window.
        pending += strip_translation_preamble(head)

    if pending:
        yield normalize_ethiopian_numbers(pending, source, target)


def translate_stream_flexible(text, source, target, provider=None):
    """
    Streaming generator for live translation:
    - Yields text tokens/chunks in real time
    - Supports Gemini and Groq with automatic fallback
    """
    if not text or not text.strip():
        return

    cleaned_text = text.strip()
    preferred_provider = str(provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    if preferred_provider == "groq":
        primary, secondary, primary_name = (
            translate_stream_with_groq, translate_stream_with_gemini, "Groq"
        )
    else:
        primary, secondary, primary_name = (
            translate_stream_with_gemini, translate_stream_with_groq, "Gemini"
        )

    emitted = False
    try:
        for chunk in postprocess_translation_stream(
            primary(cleaned_text, source, target), source, target
        ):
            emitted = True
            yield chunk
    except Exception as e:
        if emitted:
            # Text already reached the browser; replaying the full translation
            # from the other provider would duplicate it, so just report.
            print(f"{primary_name} stream failed mid-response ({e}).")
            yield f"\n[Translation Error: {str(e)}]"
            return
        print(f"{primary_name} stream error ({e}), attempting fallback...")
        try:
            for chunk in postprocess_translation_stream(
                secondary(cleaned_text, source, target), source, target
            ):
                yield chunk
        except Exception as e2:
            yield f"\n[Translation Error: {str(e)} | Fallback: {str(e2)}]"

