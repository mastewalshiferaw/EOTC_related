"""
Deterministic Ethiopian / Ge'ez Numeral Converter & Normalizer.
Provides bidirectional conversion between Classical Ge'ez numerals (፩ - ፼) and Arabic digits.
"""
import re

GEEZ_DIGITS = {
    '፩': 1, '፪': 2, '፫': 3, '፬': 4, '፭': 5,
    '፮': 6, '፯': 7, '፰': 8, '፱': 9
}

GEEZ_TENS = {
    '፲': 10, '፳': 20, '፴': 30, '፵': 40, '፶': 50,
    '፷': 60, '፸': 70, '፹': 80, '፺': 90
}

GEEZ_HUNDRED = '፻'       # 100
GEEZ_TEN_THOUSAND = '፼'  # 10,000

GEEZ_CHAR_SET = set(list(GEEZ_DIGITS.keys()) + list(GEEZ_TENS.keys()) + [GEEZ_HUNDRED, GEEZ_TEN_THOUSAND])


def parse_geez_number(text: str) -> int:
    """
    Converts a Ge'ez numeral string (e.g. ፩, ፭, ፲፭, ፻, ፲፱፻፺፯, ፪ሺ፲፯) into an integer.
    """
    if not text:
        return 0

    clean = text.strip()

    # Handle modern 'ሺ' (thousand) notation e.g. ፪ሺ፲፯
    if 'ሺ' in clean:
        parts = clean.split('ሺ', 1)
        thousands = parse_geez_number(parts[0]) if parts[0] else 1
        remainder = parse_geez_number(parts[1]) if len(parts) > 1 and parts[1] else 0
        return thousands * 1000 + remainder

    # Handle ፼ (10,000)
    if GEEZ_TEN_THOUSAND in clean:
        parts = clean.split(GEEZ_TEN_THOUSAND, 1)
        multiplier = parse_geez_number(parts[0]) if parts[0] else 1
        remainder = parse_geez_number(parts[1]) if len(parts) > 1 and parts[1] else 0
        return multiplier * 10000 + remainder

    # Handle ፻ (100)
    if GEEZ_HUNDRED in clean:
        parts = clean.split(GEEZ_HUNDRED, 1)
        multiplier = parse_geez_number(parts[0]) if parts[0] else 1
        remainder = parse_geez_number(parts[1]) if len(parts) > 1 and parts[1] else 0
        return multiplier * 100 + remainder

    total = 0
    for ch in clean:
        if ch in GEEZ_DIGITS:
            total += GEEZ_DIGITS[ch]
        elif ch in GEEZ_TENS:
            total += GEEZ_TENS[ch]
    return total


def arabic_to_geez(num: int) -> str:
    """
    Converts an integer (1 - 999,999) to a Classical Ge'ez numeral string.
    """
    if num <= 0:
        return str(num)

    if num >= 10000:
        ten_thousands = num // 10000
        remainder = num % 10000
        tt_str = (arabic_to_geez(ten_thousands) if ten_thousands > 1 else "") + GEEZ_TEN_THOUSAND
        rem_str = arabic_to_geez(remainder) if remainder > 0 else ""
        return tt_str + rem_str

    if num >= 100:
        hundreds = num // 100
        remainder = num % 100
        h_str = (arabic_to_geez(hundreds) if hundreds > 1 else "") + GEEZ_HUNDRED
        rem_str = arabic_to_geez(remainder) if remainder > 0 else ""
        return h_str + rem_str

    result = []
    tens = (num // 10) * 10
    ones = num % 10

    for ch, val in GEEZ_TENS.items():
        if val == tens:
            result.append(ch)
            break

    for ch, val in GEEZ_DIGITS.items():
        if val == ones:
            result.append(ch)
            break

    return "".join(result)


def replace_geez_numbers_with_arabic(text: str) -> str:
    """
    Finds Ge'ez numbers in a text string and converts them to Arabic digits.
    Example: 'ምዕራፍ ፩ ቁጥር ፭' -> 'ምዕራፍ 1 ቁጥር 5'
             '፲፭' -> '15'
             '፪ሺ፲፯ ዓ.ም' -> '2017 ዓ.ም'
    """
    if not text:
        return ""

    # Pattern matches Ge'ez numerals with optional modern ሺ
    pattern = r'[፩-፼]+(?:ሺ[፩-፼]*)?'

    def _replacer(match):
        g_str = match.group(0)
        val = parse_geez_number(g_str)
        return str(val) if val > 0 else g_str

    return re.sub(pattern, _replacer, text)


def replace_arabic_numbers_with_geez(text: str) -> str:
    """
    Finds Arabic digits in a text string and converts them to Ge'ez numerals.
    Example: 'ምዕራፍ 1 ቁጥር 5' -> 'ምዕራፍ ፩ ቁጥር ፭'
             '15' -> '፲፭'
    """
    if not text:
        return ""

    def _replacer(match):
        try:
            num = int(match.group(0))
            if 1 <= num <= 999999:
                return arabic_to_geez(num)
        except ValueError:
            pass
        return match.group(0)

    return re.sub(r'\b\d+\b', _replacer, text)


def extract_geez_number_mappings(text: str) -> str:
    """
    Finds unique Ge'ez numerals in text and returns a compact mapping string
    e.g. '፩=1, ፭=5, ፲=10' to assist LLM prompt conditioning.
    """
    if not text:
        return ""
    matches = re.findall(r'[፩-፼]+(?:ሺ[፩-፼]*)?', text)
    if not matches:
        return ""
    seen = {}
    for m in matches:
        if m not in seen:
            val = parse_geez_number(m)
            if val > 0:
                seen[m] = val
    if not seen:
        return ""
    return ", ".join(f"{k}={v}" for k, v in seen.items())


def normalize_ethiopian_numbers(text: str, source: str, target: str) -> str:
    """
    Applies deterministic number post-processing based on source and target language:
    - If target is English or Amharic: converts residual Ge'ez numerals to standard numbers.
    - If target is Ge'ez: converts Arabic numbers to Ge'ez numerals.
    """
    if not text:
        return ""

    tgt_lower = (target or "").lower()
    if "ge'ez" in tgt_lower or "geez" in tgt_lower or "ግዕዝ" in tgt_lower:
        return replace_arabic_numbers_with_geez(text)
    elif "amharic" in tgt_lower or "አማርኛ" in tgt_lower or "english" in tgt_lower:
        return replace_geez_numbers_with_arabic(text)
    return text
