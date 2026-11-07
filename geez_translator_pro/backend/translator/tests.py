import time

from django.test import TestCase

from .ethiopian_numbers import (
    arabic_to_geez,
    extract_geez_number_mappings,
    normalize_ethiopian_numbers,
    parse_geez_number,
    replace_arabic_numbers_with_geez,
    replace_geez_numbers_with_arabic,
)
from .translation_service import (
    is_religious_context,
    prepare_translation_prompt,
    sanitize_translation_text,
    strip_translation_preamble,
)


class ParseGeezNumberTests(TestCase):
    def test_single_digits(self):
        for char, value in [
            ("\u1369", 1), ("\u136a", 2), ("\u136b", 3), ("\u136c", 4), ("\u136d", 5),
            ("\u136e", 6), ("\u136f", 7), ("\u1370", 8), ("\u1371", 9),
        ]:
            with self.subTest(char=char):
                self.assertEqual(parse_geez_number(char), value)

    def test_tens(self):
        for char, value in [
            ("\u1372", 10), ("\u1373", 20), ("\u1374", 30), ("\u1375", 40),
            ("\u1376", 50), ("\u1377", 60), ("\u1378", 70), ("\u1379", 80),
            ("\u137a", 90),
        ]:
            with self.subTest(char=char):
                self.assertEqual(parse_geez_number(char), value)

    def test_compound_numbers(self):
        self.assertEqual(parse_geez_number("\u1372\u136d"), 15)          # ፲፭
        self.assertEqual(parse_geez_number("\u137b"), 100)               # ፻
        self.assertEqual(parse_geez_number("\u137c"), 10000)             # ፼
        self.assertEqual(parse_geez_number("\u1369\u137b\u1369"), 101)   # ፩፻፩
        self.assertEqual(parse_geez_number("፲፱፻፺፯"), 1997)
        self.assertEqual(parse_geez_number("፳፻፵፬"), 2044)
        self.assertEqual(parse_geez_number("፪ሺ፲፯"), 2017)

    def test_empty_and_none_are_zero(self):
        self.assertEqual(parse_geez_number(""), 0)
        self.assertEqual(parse_geez_number(None), 0)

    def test_text_without_numerals_is_zero(self):
        self.assertEqual(parse_geez_number("\u1230\u120b\u121d"), 0)
        self.assertEqual(parse_geez_number("-"), 0)

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(parse_geez_number("  \u1372\u136d  "), 15)


class ArabicToGeezTests(TestCase):
    def test_known_values(self):
        self.assertEqual(arabic_to_geez(1), "\u1369")
        self.assertEqual(arabic_to_geez(10), "\u1372")
        self.assertEqual(arabic_to_geez(15), "\u1372\u136d")
        self.assertEqual(arabic_to_geez(100), "\u137b")
        self.assertEqual(arabic_to_geez(101), "\u137b\u1369")
        self.assertEqual(arabic_to_geez(1000), "\u1372\u137b")
        self.assertEqual(arabic_to_geez(10000), "\u137c")
        self.assertEqual(arabic_to_geez(10001), "\u137c\u1369")
        self.assertEqual(arabic_to_geez(20000), "\u136a\u137c")

    def test_zero_and_negative_are_left_as_digits(self):
        self.assertEqual(arabic_to_geez(0), "0")
        self.assertEqual(arabic_to_geez(-5), "-5")

    def test_round_trip_is_stable(self):
        for number in range(1, 2001):
            with self.subTest(number=number):
                self.assertEqual(
                    parse_geez_number(arabic_to_geez(number)), number
                )

    def test_round_trip_six_digit_values(self):
        for number in (12345, 99999, 100000, 999999):
            with self.subTest(number=number):
                self.assertEqual(
                    parse_geez_number(arabic_to_geez(number)), number
                )


class NumberReplacementTests(TestCase):
    def test_geez_to_arabic_in_a_sentence(self):
        self.assertEqual(
            replace_geez_numbers_with_arabic("\u121d\u12d5\u122b\u134d \u1369 \u1241\u1325\u122d \u136d"),
            "\u121d\u12d5\u122b\u134d 1 \u1241\u1325\u122d 5",
        )

    def test_geez_to_arabic_thousands_notation(self):
        self.assertEqual(
            replace_geez_numbers_with_arabic("፪ሺ፲፯ ዓ.ም"),
            "2017 ዓ.ም",
        )

    def test_arabic_to_geez_in_a_sentence(self):
        self.assertEqual(
            replace_arabic_numbers_with_geez("Chapter 1 verse 5"),
            "Chapter \u1369 verse \u136d",
        )

    def test_arabic_zero_and_large_numbers_are_untouched(self):
        self.assertEqual(replace_arabic_numbers_with_geez("0 items"), "0 items")
        self.assertEqual(replace_arabic_numbers_with_geez("1000000"), "1000000")

    def test_empty_inputs(self):
        self.assertEqual(replace_geez_numbers_with_arabic(""), "")
        self.assertEqual(replace_geez_numbers_with_arabic(None), "")
        self.assertEqual(replace_arabic_numbers_with_geez(""), "")
        self.assertEqual(replace_arabic_numbers_with_geez(None), "")

    def test_text_without_numbers_is_unchanged(self):
        text = "\u1230\u120b\u121d \u1208\u12aa\u1362"
        self.assertEqual(replace_geez_numbers_with_arabic(text), text)
        self.assertEqual(replace_arabic_numbers_with_geez(text), text)


class NormalizeNumbersTests(TestCase):
    def test_geez_numerals_are_converted_for_amharic_and_english(self):
        text = "\u121d\u12d5\u122b\u134d \u1369 \u1241\u1325\u122d \u1372\u136d"
        expected = "\u121d\u12d5\u122b\u134d 1 \u1241\u1325\u122d 15"
        for target in ("Amharic", "\u12a0\u121b\u122d\u129b", "English", "english"):
            with self.subTest(target=target):
                self.assertEqual(normalize_ethiopian_numbers(text, "Ge'ez", target), expected)

    def test_arabic_digits_are_converted_for_geez_target(self):
        self.assertEqual(
            normalize_ethiopian_numbers("Chapter 15 verse 3", "English", "Ge'ez"),
            "Chapter \u1372\u136d verse \u136b",
        )
        self.assertEqual(
            normalize_ethiopian_numbers("Chapter 15", "English", "\u130d\u12d5\u12dd"),
            "Chapter \u1372\u136d",
        )

    def test_unknown_target_is_passed_through(self):
        text = "\u121d\u12d5\u122b\u134d \u1369"
        self.assertEqual(normalize_ethiopian_numbers(text, "Ge'ez", "Klingon"), text)

    def test_empty_input(self):
        self.assertEqual(normalize_ethiopian_numbers("", "Ge'ez", "Amharic"), "")
        self.assertEqual(normalize_ethiopian_numbers(None, "Ge'ez", "Amharic"), "")

    def test_missing_target_is_passed_through(self):
        text = "\u1369\u136a"
        self.assertEqual(normalize_ethiopian_numbers(text, "Ge'ez", ""), text)
        self.assertEqual(normalize_ethiopian_numbers(text, "Ge'ez", None), text)


class ExtractNumberMappingsTests(TestCase):
    def test_unique_pairs_are_returned_in_order(self):
        text = "\u1369 \u1369 \u1372\u136d \u136b"
        self.assertEqual(
            extract_geez_number_mappings(text), "\u1369=1, \u1372\u136d=15, \u136b=3"
        )

    def test_no_numerals_returns_empty_string(self):
        self.assertEqual(extract_geez_number_mappings("\u1230\u120b\u121d"), "")
        self.assertEqual(extract_geez_number_mappings(""), "")
        self.assertEqual(extract_geez_number_mappings(None), "")


class SanitizeTranslationTests(TestCase):
    def test_preamble_is_stripped(self):
        cases = [
            ("\u12a5\u1290\u1206 \u1275\u122d\u1309\u1219: \u1230\u120b\u121d \u1208\u12aa",
             "\u1230\u120b\u121d \u1208\u12aa"),
            ("Here is the translation: Peace be with you", "Peace be with you"),
            ("Translation - hello there friend", "hello there friend"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(sanitize_translation_text(raw), expected)

    def test_strip_preamble_helper(self):
        self.assertEqual(strip_translation_preamble("Translation: hi"), "hi")
        self.assertEqual(strip_translation_preamble(""), "")
        self.assertEqual(strip_translation_preamble(None), "")

    def test_long_repeating_unit_is_collapsed(self):
        self.assertEqual(sanitize_translation_text("foobar foobar foobar"), "foobar")
        self.assertEqual(
            sanitize_translation_text("Peace be with you. " * 3), "Peace be with you."
        )

    def test_single_repetition_is_preserved(self):
        self.assertEqual(sanitize_translation_text("foobarb foobarb"), "foobarb foobarb")

    def test_short_liturgical_repetition_is_preserved(self):
        """Short repeated words are legitimate in hymns and must survive."""
        text = "\u1230\u120b\u121d \u1230\u120b\u121d \u1230\u120b\u121d"
        self.assertEqual(sanitize_translation_text(text), text)

    def test_plain_text_is_unchanged(self):
        text = "The quick brown fox jumps over the lazy dog."
        self.assertEqual(sanitize_translation_text(text), text)

    def test_empty_and_none(self):
        self.assertEqual(sanitize_translation_text(""), "")
        self.assertEqual(sanitize_translation_text(None), "")

    def test_whitespace_is_trimmed(self):
        self.assertEqual(sanitize_translation_text("   \u1230\u120b\u121d   "), "\u1230\u120b\u121d")

    def test_long_input_is_fast(self):
        """Guard against catastrophic backtracking in the repeat pattern."""
        text = "The quick brown fox jumps over the lazy dog. " * 200
        started = time.perf_counter()
        sanitize_translation_text(text)
        self.assertLess(time.perf_counter() - started, 2.0)


class ReligiousContextTests(TestCase):
    def test_detects_geez_and_english_religious_terms(self):
        for text in (
            "\u12a5\u130d\u12da\u12a0\u1265\u1214\u122d \u1230\u120b\u121d",
            "\u121b\u122d\u12eb\u121d \u12dd\u1295\u130d\u120d",
            "Holy Mary, pray for us",
            "Lord have mercy",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_religious_context(text))

    def test_secular_text_is_not_religious(self):
        self.assertFalse(is_religious_context("Please pay the invoice by Friday."))
        self.assertFalse(is_religious_context(""))
        self.assertFalse(is_religious_context(None))

    def test_prompt_notes_religious_context_and_numerals(self):
        prompt, user_content = prepare_translation_prompt(
            "\u12a5\u130d\u12da\u12a0\u1265\u1214\u122d \u1369", "Ge'ez", "Amharic"
        )
        self.assertIn("Ethiopian Orthodox", prompt)
        self.assertIn("Religious", user_content)
        self.assertIn("\u1369=1", user_content)

    def test_prompt_notes_secular_context(self):
        prompt, user_content = prepare_translation_prompt(
            "The meeting is at noon.", "English", "Amharic"
        )
        self.assertIn("Secular", user_content)
        self.assertNotIn("Ge'ez numeral values", user_content)
import json
from unittest.mock import patch

from django.test import TestCase

from . import translation_service
from .translation_service import (
    postprocess_translation_stream,
    translate_flexible,
    translate_stream_flexible,
)


def _collect(chunks, source="Ge'ez", target="Amharic"):
    return "".join(postprocess_translation_stream(iter(chunks), source, target))


class StreamPostprocessTests(TestCase):
    def test_geez_numerals_are_converted_mid_stream(self):
        """Regression: the SSE path used to skip numeral normalization entirely."""
        chunks = ["\u121d\u12d5\u122b", "\u134d ", "\u1372", "\u136d \u1241\u1325\u122d", " \u136b"]
        self.assertEqual(
            _collect(chunks), "\u121d\u12d5\u122b\u134d 15 \u1241\u1325\u122d 3"
        )

    def test_numeral_split_across_chunks_is_not_mangled(self):
        """፲ + ፭ must become 15, not 105."""
        self.assertEqual(_collect(["\u1372", "\u136d"]), "15")
        self.assertNotIn("105", _collect(["\u1372", "\u136d"]))

    def test_arabic_number_split_across_chunks_for_geez_target(self):
        self.assertEqual(
            _collect(["Chapter ", "15", " verse ", "3"], "English", "Ge'ez"),
            "Chapter \u1372\u136d verse \u136b",
        )

    def test_preamble_split_across_chunks_is_stripped(self):
        chunks = ["Here is the ", "translation: ", "Peace be ", "with you"]
        self.assertEqual(_collect(chunks, "Ge'ez", "English"), "Peace be with you")

    def test_amharic_preamble_with_trailing_separator_chunk(self):
        chunks = ["\u12a5\u1290\u1206 \u1275\u122d\u1309\u1219", ": ", "\u1230\u120b\u121d \u1208\u12aa"]
        self.assertEqual(_collect(chunks), "\u1230\u120b\u121d \u1208\u12aa")

    def test_preamble_only_stream_yields_nothing(self):
        self.assertEqual(_collect(["Translation:", " "], "Ge'ez", "English"), "")

    def test_plain_text_streams_through_unchanged(self):
        self.assertEqual(_collect(["\u1230\u120b\u121d ", "\u1208\u12aa"]), "\u1230\u120b\u121d \u1208\u12aa")

    def test_streaming_is_incremental(self):
        """Chunks must still be delivered piece by piece, not buffered whole."""
        pieces = list(
            postprocess_translation_stream(
                iter(["Peace ", "be ", "with you"]), "Ge'ez", "English"
            )
        )
        self.assertGreater(len(pieces), 1)
        self.assertEqual("".join(pieces), "Peace be with you")

    def test_empty_chunks_are_skipped(self):
        self.assertEqual(_collect(["", "\u1230\u120b\u121d", ""]), "\u1230\u120b\u121d")

    def test_empty_stream(self):
        self.assertEqual(_collect([]), "")

    def test_unknown_target_passes_through(self):
        self.assertEqual(_collect(["\u121d\u12d5\u122b\u134d \u1369"], "Ge'ez", "Klingon"),
                         "\u121d\u12d5\u122b\u134d \u1369")


def _chunks(*items):
    for item in items:
        yield item


class StreamFallbackTests(TestCase):
    def test_primary_provider_streams_when_healthy(self):
        with patch.object(translation_service, "translate_stream_with_gemini",
                          side_effect=lambda *a, **k: _chunks("Hello ", "world")), \
             patch.object(translation_service, "translate_stream_with_groq",
                          side_effect=AssertionError("groq should not be called")):
            self.assertEqual("".join(translate_stream_flexible("x", "Ge'ez", "English")),
                             "Hello world")

    def test_falls_back_before_any_output(self):
        def boom(*args, **kwargs):
            raise RuntimeError("quota exceeded")
            yield  # pragma: no cover

        with patch.object(translation_service, "translate_stream_with_gemini", side_effect=boom), \
             patch.object(translation_service, "translate_stream_with_groq",
                          side_effect=lambda *a, **k: _chunks("Fallback ", "text")):
            self.assertEqual("".join(translate_stream_flexible("x", "Ge'ez", "English")),
                             "Fallback text")

    def test_groq_preference_is_honoured(self):
        with patch.object(translation_service, "translate_stream_with_groq",
                          side_effect=lambda *a, **k: _chunks("groq")), \
             patch.object(translation_service, "translate_stream_with_gemini",
                          side_effect=AssertionError("gemini should not be called")):
            self.assertEqual(
                "".join(translate_stream_flexible("x", "Ge'ez", "English", provider="groq")),
                "groq",
            )

    def test_mid_stream_failure_does_not_replay_the_whole_translation(self):
        """Regression: falling back after partial output duplicated the text."""
        def partial_then_boom(*args, **kwargs):
            yield "The Lord "
            raise RuntimeError("connection dropped")

        with patch.object(translation_service, "translate_stream_with_gemini",
                          side_effect=partial_then_boom), \
             patch.object(translation_service, "translate_stream_with_groq",
                          side_effect=lambda *a, **k: _chunks("The Lord is my shepherd")):
            output = "".join(translate_stream_flexible("x", "Ge'ez", "English"))

        self.assertEqual(output.count("shepherd"), 0)
        self.assertEqual(output.count("The Lord"), 1)
        self.assertIn("Translation Error", output)

    def test_both_providers_failing_reports_both_errors(self):
        def boom(*args, **kwargs):
            raise RuntimeError("first down")
            yield  # pragma: no cover

        def boom2(*args, **kwargs):
            raise RuntimeError("second down")
            yield  # pragma: no cover

        with patch.object(translation_service, "translate_stream_with_gemini", side_effect=boom), \
             patch.object(translation_service, "translate_stream_with_groq", side_effect=boom2):
            output = "".join(translate_stream_flexible("x", "Ge'ez", "English"))

        self.assertIn("first down", output)
        self.assertIn("second down", output)

    def test_empty_input_yields_nothing(self):
        self.assertEqual(list(translate_stream_flexible("", "Ge'ez", "English")), [])
        self.assertEqual(list(translate_stream_flexible("   ", "Ge'ez", "English")), [])


class BatchTranslationTests(TestCase):
    def test_empty_input_returns_empty_string(self):
        self.assertEqual(translate_flexible("", "Ge'ez", "Amharic"), "")
        self.assertEqual(translate_flexible("   ", "Ge'ez", "Amharic"), "")

    def test_batch_applies_sanitize_and_number_normalization(self):
        with patch.object(translation_service, "get_gemini_client") as client, \
             patch.object(translation_service, "prepare_translation_prompt",
                          return_value=("sys", "user")):
            client.return_value.models.generate_content.return_value.text = (
                "Here is the translation: \u121d\u12d5\u122b\u134d \u1369"
            )
            self.assertEqual(
                translate_flexible("x", "Ge'ez", "Amharic"), "\u121d\u12d5\u122b\u134d 1"
            )

    def test_batch_falls_back_to_groq_when_gemini_fails(self):
        with patch.object(translation_service, "translate_with_gemini",
                          side_effect=RuntimeError("no key")), \
             patch.object(translation_service, "translate_with_groq",
                          return_value="\u1230\u120b\u121d"):
            self.assertEqual(translate_flexible("x", "Ge'ez", "Amharic"), "\u1230\u120b\u121d")

    def test_batch_reports_both_errors(self):
        with patch.object(translation_service, "translate_with_gemini",
                          side_effect=RuntimeError("gemini down")), \
             patch.object(translation_service, "translate_with_groq",
                          side_effect=RuntimeError("groq down")):
            result = translate_flexible("x", "Ge'ez", "Amharic")
        self.assertIn("gemini down", result)
        self.assertIn("groq down", result)

    def test_non_string_provider_does_not_crash(self):
        with patch.object(translation_service, "translate_with_gemini",
                          return_value="ok"):
            self.assertEqual(translate_flexible("x", "Ge'ez", "Amharic", provider={"a": 1}), "ok")
import io
import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .services import clean_pure_geez_ocr, restore_fidel_ocr_text, preprocess_image_bytes
from .views import _as_bool

from . import views as views_module


class OcrCleanupTests(TestCase):
    def test_homoglyph_rules(self):
        cases = [
            ("\u12a0\u130d\u12da\u12a0\u1265\u1214\u122d", "\u12a5\u130d\u12da\u12a0\u1265\u1214\u122d"),  # አ/እ
            ("\u12f5\u1308\u130d\u120d", "\u12f5\u1295\u130d\u120d"),                                    # ገ/ን
            ("\u1260\u1285\u1232\u1293\u12aa", "\u1260\u1285\u120a\u1293\u12aa"),                        # ሲ/ሊ
            ("\u121d\u1235\u1234\u12aa", "\u121d\u1235\u120c\u12aa"),                                   # ሴ/ሌ
            ("\u12a0\u121d\u12a0\u1295\u1235\u1275", "\u12a5\u121d\u12a0\u1295\u1235\u1275"),            # አም/እም
            ("\u12c8\u1338\u120d\u12e9", "\u12c8\u1338\u120d\u12ea"),                                    # ዩ/ዪ
            ("\u12a0\u1290\u1272", "\u12a0\u1295\u1272"),                                               # ነ/ን
            ("ኀጣውኢነ", "ኃጣውኢነ"),                                                                          # ኀ/ኃ
            ("\u12a0 \u121d\u120d\u12a0\u1270", "\u12a6 \u121d\u120d\u12a5\u1270"),                       # ኦ ምልእተ
            ("ከርስቶስ", "ክርስቶስ"),                                                                          # ከ/ክ
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(clean_pure_geez_ocr(raw), expected)

    def test_cleanup_is_deterministic_and_idempotent(self):
        text = "\u12a0\u130d\u12da\u12a0\u1265\u1214\u122d \u12f5\u1308\u130d\u120d"
        first = clean_pure_geez_ocr(text)
        self.assertEqual(first, clean_pure_geez_ocr(text))
        self.assertEqual(clean_pure_geez_ocr(first), first)

    def test_empty_inputs(self):
        self.assertEqual(clean_pure_geez_ocr(""), "")
        self.assertEqual(clean_pure_geez_ocr(None), "")
        self.assertEqual(restore_fidel_ocr_text(""), "")
        self.assertEqual(restore_fidel_ocr_text(None), "")

    def test_restore_is_a_pure_rewrite_of_clean(self):
        text = "\u12f5\u1308\u130d\u120d \u1230\u120b\u121d"
        self.assertEqual(restore_fidel_ocr_text(text), clean_pure_geez_ocr(text))

    def test_punctuation_noise_is_removed(self):
        self.assertNotIn(".", clean_pure_geez_ocr("\u1230\u120b\u121d . \u1208\u12aa ."))

    def test_preprocess_dark_background_detection_and_red_text_preservation(self):
        import cv2
        import numpy as np
        # Create a dark background image with white and red text
        dark_img = np.zeros((100, 200, 3), dtype=np.uint8)
        # White text area (high intensity across all channels)
        dark_img[20:40, 20:80] = [200, 200, 200]
        # Red text area (high red, low blue/green)
        dark_img[60:80, 20:80] = [30, 30, 220]

        is_success, buf = cv2.imencode(".png", dark_img)
        self.assertTrue(is_success)
        processed = preprocess_image_bytes(buf.tobytes(), is_ethiopic=True)
        self.assertIsNotNone(processed)
        # Tesseract expects dark text on light background:
        # Background should be inverted to light (> 200)
        self.assertGreater(processed[5, 5], 200)
        # Both white and red text areas should be inverted to dark (< 100)
        # Check that red text is NOT washed out/lost in background:
        self.assertLess(np.min(processed), 100)


class AsBoolTests(TestCase):
    def test_json_booleans(self):
        self.assertIs(_as_bool(True), True)
        self.assertIs(_as_bool(False), False)

    def test_string_forms(self):
        for value in ("true", "True", "1", "yes", "on"):
            with self.subTest(value=value):
                self.assertIs(_as_bool(value), True)
        for value in ("false", "0", "no", "off", ""):
            with self.subTest(value=value):
                self.assertIs(_as_bool(value), False)

    def test_missing_value_uses_default(self):
        self.assertIs(_as_bool(None), False)
        self.assertIs(_as_bool(None, default=True), True)


class HealthCheckTests(TestCase):
    def test_health_is_public_and_healthy(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["checks"]["database"], "connected")
        self.assertIn("tesseract_ocr", body["checks"])
        self.assertIn("timestamp", body)

    def test_health_aliases_work(self):
        for url in ("/health/", "/healthz", "/healthz/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class OcrEndpointTests(TestCase):
    def _upload(self, **extra):
        image = io.BytesIO()
        image.write(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        image.seek(0)
        data = {"file": SimpleUploadedFile("p.png", image.read(), content_type="image/png")}
        data.update(extra)
        return self.client.post("/api/ocr-only/", data)

    def test_missing_file_is_rejected(self):
        response = self.client.post("/api/ocr-only/", {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["text"], "No file received")

    @patch.object(views_module, "perform_hybrid_ocr", return_value="\u1230\u120b\u121d")
    def test_upload_returns_ocr_text_and_provider(self, mock_ocr):
        response = self._upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "\u1230\u120b\u121d")
        self.assertEqual(response.json()["provider"], "gemini")
        self.assertTrue(mock_ocr.called)

    @patch.object(views_module, "perform_hybrid_ocr", return_value="ok")
    def test_auto_clean_string_flag_is_parsed(self, mock_ocr):
        self._upload(auto_clean="false")
        self.assertIs(mock_ocr.call_args.kwargs["auto_clean"], False)

    @patch.object(views_module, "perform_hybrid_ocr", return_value="ok")
    def test_auto_clean_defaults_to_true(self, mock_ocr):
        self._upload()
        self.assertIs(mock_ocr.call_args.kwargs["auto_clean"], True)

    def test_provider_override_is_echoed(self):
        with patch.object(views_module, "perform_hybrid_ocr", return_value="ok"):
            response = self._upload(provider="groq")
        self.assertEqual(response.json()["provider"], "groq")


class CleanEndpointTests(TestCase):
    def test_empty_text_is_rejected(self):
        for payload in ({}, {"text": ""}, {"text": "   "}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/clean-ocr/", payload)
                self.assertEqual(response.status_code, 400)

    def test_non_string_text_is_rejected(self):
        response = self.client.post(
            "/api/clean-ocr/",
            data=json.dumps({"text": {"a": 1}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_text_is_cleaned(self):
        response = self.client.post("/api/clean-ocr/", {"text": "\u12f5\u1308\u130d\u120d"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "\u12f5\u1295\u130d\u120d")


class TranslateEndpointTests(TestCase):
    def test_empty_text_is_rejected(self):
        for payload in ({}, {"text": ""}, {"text": "   "}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/translate-flexible/", payload)
                self.assertEqual(response.status_code, 400)

    @patch.object(views_module, "translate_flexible", return_value="\u1230\u120b\u121d")
    def test_translation_is_returned(self, mock_translate):
        response = self.client.post(
            "/api/translate-flexible/",
            {"text": "\u1369", "source": "Ge'ez", "target": "Amharic"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translation"], "\u1230\u120b\u121d")


def _parse_sse(payload):
    """Split an SSE body into its JSON events plus the [DONE] sentinel."""
    events = []
    for block in payload.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        assert block.startswith("data: "), block
        body = block[len("data: "):]
        events.append("[DONE]" if body == "[DONE]" else json.loads(body))
    return events


class StreamEndpointTests(TestCase):
    def test_empty_text_is_rejected(self):
        for payload in ({}, {"text": ""}, {"text": "   "}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/translate-flexible-stream/", payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"], "Empty text provided")

    @patch.object(views_module, "translate_stream_flexible")
    def test_sse_framing_and_done_marker(self, mock_stream):
        mock_stream.return_value = iter(["\u1230\u120b\u121d", " \u1208\u12aa"])
        response = self.client.post(
            "/api/translate-flexible-stream/", {"text": "\u1369"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertEqual(response["X-Accel-Buffering"], "no")

        events = _parse_sse(b"".join(response.streaming_content).decode("utf-8"))
        self.assertEqual(events[0], {"chunk": "\u1230\u120b\u121d"})
        self.assertEqual(events[1], {"chunk": " \u1208\u12aa"})
        self.assertEqual(events[-1], "[DONE]")

    @patch.object(views_module, "translate_stream_flexible")
    def test_provider_exception_becomes_sse_error_event(self, mock_stream):
        def boom(*args, **kwargs):
            raise RuntimeError("provider exploded")
            yield  # pragma: no cover

        mock_stream.side_effect = boom
        response = self.client.post("/api/translate-flexible-stream/", {"text": "\u1369"})
        events = _parse_sse(b"".join(response.streaming_content).decode("utf-8"))
        self.assertEqual(events[0]["error"], "provider exploded")
        self.assertEqual(events[-1], "[DONE]")

    def test_numbers_are_normalized_end_to_end_through_the_endpoint(self):
        """The UI only uses SSE, so numerals must be converted here too."""
        with patch.object(
            views_module, "translate_stream_flexible",
        ) as mock_stream:
            from .translation_service import postprocess_translation_stream

            mock_stream.return_value = postprocess_translation_stream(
                iter(["\u121d\u12d5\u122b\u134d ", "\u1372", "\u136d"]),
                "Ge'ez",
                "Amharic",
            )
            response = self.client.post(
                "/api/translate-flexible-stream/",
                {"text": "x", "source": "Ge'ez", "target": "Amharic"},
            )
            payload = b"".join(response.streaming_content).decode("utf-8")

        events = _parse_sse(payload)
        self.assertEqual(events[-1], "[DONE]")
        self.assertEqual(
            "".join(e["chunk"] for e in events if "chunk" in e),
            "\u121d\u12d5\u122b\u134d 15",
        )
