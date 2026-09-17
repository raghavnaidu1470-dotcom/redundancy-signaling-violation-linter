"""Unit tests for OCR text cleaning and garbage filtering."""

import unittest

from src.ocr.cleaner import clean_ocr_text, is_valid_slide_text


class OcrCleanerTest(unittest.TestCase):
    def test_handles_empty_or_none(self):
        self.assertEqual(clean_ocr_text(""), "")
        self.assertEqual(clean_ocr_text("   "), "")

    def test_strips_noise_symbols(self):
        raw = "i se mary “Wee < Tv we Are 4 teavers SQ oder Sey ORT wh cuccessar, meet, de my w& Bovey Seorchy We sAME C cay HEE Vin SUhee SRK Y"
        cleaned = clean_ocr_text(raw)
        # Verify noise symbols like < are removed
        self.assertNotIn("<", cleaned)
        self.assertNotIn("~", cleaned)
        self.assertNotIn("|", cleaned)

    def test_filters_standalone_noise_characters(self):
        raw = "~ | _ \\ ^ * < > = + #\nValid Title\n- single - w&"
        cleaned = clean_ocr_text(raw)
        self.assertIn("Valid Title", cleaned)

    def test_is_valid_slide_text(self):
        self.assertTrue(is_valid_slide_text("Binary Trees Part 1"))
        self.assertFalse(is_valid_slide_text("< > = ~"))
        self.assertFalse(is_valid_slide_text("x"))


if __name__ == "__main__":
    unittest.main()
