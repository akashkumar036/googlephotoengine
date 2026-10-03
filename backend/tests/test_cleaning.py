from __future__ import annotations
import pytest
from app.pipeline.cleaning import clean_text, clean_batch, hash_author


def test_html_and_entity_removal():
    raw = "<p>Google Photos &amp; Apple Photos search is <b>completely broken</b>! &quot;Try again&quot;</p>"
    result = clean_text(raw)
    assert "<p>" not in result.cleaned_text
    assert "<b>" not in result.cleaned_text
    assert "&amp;" not in result.cleaned_text
    assert "Google Photos & Apple Photos search is completely broken! \"Try again\"" == result.cleaned_text


def test_whitespace_normalization():
    raw = "   Looking   for    vacation \t photos.\n\n\n\nWhere are they?   "
    result = clean_text(raw)
    assert "Looking for vacation photos.\n\nWhere are they?" == result.cleaned_text


def test_encoding_repair():
    raw = "I canâ€™t find my photosâ€¦"
    result = clean_text(raw)
    assert "’" in result.cleaned_text or "'" in result.cleaned_text
    assert "…" in result.cleaned_text or "..." in result.cleaned_text


def test_pii_detection_and_redaction():
    raw = "My email is user123@example.com and phone is 555-123-4567. Can you help me find photos?"
    result = clean_text(raw)
    assert result.pii_detected is True
    assert "[EMAIL_REDACTED]" in result.cleaned_text
    assert "[PHONE_REDACTED]" in result.cleaned_text
    assert "user123@example.com" not in result.cleaned_text
    assert "555-123-4567" not in result.cleaned_text


def test_author_hashing():
    raw_author = "real_person_name"
    h = hash_author(raw_author)
    assert len(h) == 64
    assert h != raw_author
    assert hash_author(raw_author) == h


def test_spam_detection():
    spam_text = "Click here for free download and discount on crypto casino recovery tool: https://spam.com https://spam.org"
    result = clean_text(spam_text)
    assert result.is_spam is True
    assert result.flags.get("is_automated") is True

    normal_text = "I took photos at my daughter's wedding and cannot find them using face search."
    normal_res = clean_text(normal_text)
    assert normal_res.is_spam is False


def test_low_information_filter():
    short_text = "Good app"
    result = clean_text(short_text)
    assert result.is_low_information is True
    assert result.token_count < 5

    long_text = "I am looking for pictures taken during our trip to Yellowstone in July 2023."
    long_res = clean_text(long_text)
    assert long_res.is_low_information is False
    assert long_res.token_count >= 5


def test_quoted_content_detection():
    text_with_quote = """> John said: The search feature never works
I totally disagree, for me it works great."""
    result = clean_text(text_with_quote)
    assert result.flags.get("has_quotes") is True
    assert result.flags.get("quotes_count", 0) >= 1
    # Check blockquote marker > was cleaned
    assert not result.cleaned_text.startswith(">")


def test_clean_batch_processes_100_records():
    """Verify clean_batch processes a batch of 100+ records without error."""
    texts = [
        f"Record {i}: Cannot retrieve photo taken in summer {2020 + (i % 5)} with friends."
        for i in range(105)
    ]
    results = clean_batch(texts)
    assert len(results) == 105
    assert all(r.cleaned_text != "" and r.token_count > 0 for r in results)
    assert all(r.pii_detected is False for r in results)
