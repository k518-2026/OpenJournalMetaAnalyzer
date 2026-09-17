import pytest
from app.search.translator import is_japanese, translate_query, translate_to_english

def test_is_japanese():
    assert is_japanese("アルツハイマー病 新薬") is True
    assert is_japanese("COVID-19 ワクチン") is True
    assert is_japanese("Metformin and Type 2 Diabetes") is False
    assert is_japanese("12345 67890") is False
    assert is_japanese("がん 治療") is True
    assert is_japanese("かんじ") is True
    assert is_japanese("カタカナ") is True

def test_translate_english_passthrough():
    # If already English, it should pass through without modification
    original = "metformin longevity"
    translated, was_translated = translate_query(original)
    assert translated == original
    assert was_translated is False

def test_translate_japanese_live_or_fallback():
    # If Japanese, it should translate to English
    ja_query = "アルツハイマー病"
    translated, was_translated = translate_query(ja_query)
    assert was_translated is True
    assert translated != ja_query
    assert any(word in translated.lower() for word in ["alzheimer", "disease"])

def test_translate_alias():
    translated, was_translated = translate_to_english("糖尿病")
    assert was_translated is True
    assert "diabetes" in translated.lower()
