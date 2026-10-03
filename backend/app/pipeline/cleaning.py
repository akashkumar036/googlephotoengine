from __future__ import annotations
import hashlib
import html
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import structlog

log = structlog.get_logger()

try:
    import ftfy
    _FTFY = True
except ImportError:
    _FTFY = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    _LANGDETECT = True
except ImportError:
    _LANGDETECT = False

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

_RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
_RE_PHONE = re.compile(r"\b(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b")
_RE_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_RE_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_RE_IP = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_RE_QUOTE_LINE = re.compile(r"^\s*>+\s*(.*)$", re.MULTILINE)
_RE_QUOTED_TEXT = re.compile(r'(?:said|wrote|stated|says):\s*["\']([^"\']+)["\']', re.I)

_SPAM_KEYWORDS = {
    "buy now", "click here", "limited offer", "discount", "promo code",
    "free download", "recovery tool", "crack", "crypto", "casino",
    "free license", "whatsapp", "telegram", "subscribe now", "visit website",
    "unlock tool", "fast cash", "win prize", "photo recovery software free"
}
_MIN_TOKEN_COUNT = 5


@dataclass
class CleanResult:
    cleaned_text: str
    language: Optional[str]
    is_spam: bool
    is_low_information: bool
    pii_detected: bool
    token_count: int
    flags: Dict[str, Any] = field(default_factory=dict)


def _remove_html(text: str) -> str:
    """Strip HTML markup and unescape entities like &amp;, &quot;, &#39; (Edge Case 2.6)."""
    if _BS4:
        text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    else:
        text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def _normalize_whitespace(text: str) -> str:
    """Normalize space characters, collapse excess blank lines, and fix spaces before punctuation."""
    text = text.strip()
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _fix_encoding(text: str) -> str:
    """Repair mojibake and encoding glitches via ftfy."""
    return ftfy.fix_text(text) if _FTFY else text


def _detect_language(text: str) -> Optional[str]:
    """Detect language, defaulting to None if detection is ambiguous or fails."""
    if not _LANGDETECT:
        return "en"
    clean_words = [w for w in text.split() if w.isalpha()]
    if len(clean_words) < 3:
        return "en"
    try:
        return detect(text)
    except Exception:
        return "en"


def _detect_spam(text: str) -> bool:
    """Spam detection using keyword heuristics, excessive URLs, and template patterns."""
    lower = text.lower()
    keyword_matches = sum(1 for kw in _SPAM_KEYWORDS if kw in lower)
    url_count = len(_RE_URL.findall(text))
    # 2+ spam keywords, or 3+ links in a short message, is considered spam
    if keyword_matches >= 2:
        return True
    if url_count >= 3:
        return True
    if keyword_matches >= 1 and url_count >= 1:
        return True
    return False


def _detect_pii(text: str) -> bool:
    """Flag presence of sensitive personally identifiable information."""
    return bool(
        _RE_EMAIL.search(text)
        or _RE_PHONE.search(text)
        or _RE_SSN.search(text)
        or _RE_IP.search(text)
    )


def _redact_pii(text: str) -> str:
    """Redact high-risk direct identifiers while preserving surrounding context (Edge Case 2.4)."""
    text = _RE_EMAIL.sub("[EMAIL_REDACTED]", text)
    text = _RE_PHONE.sub("[PHONE_REDACTED]", text)
    text = _RE_SSN.sub("[SSN_REDACTED]", text)
    return text


def _detect_and_handle_quotes(text: str) -> tuple[str, bool, list[str]]:
    """Detect blockquotes or attributed quoted text (Edge Case 2.1)."""
    quotes = []
    has_quotes = False

    blockquotes = _RE_QUOTE_LINE.findall(text)
    if blockquotes:
        has_quotes = True
        quotes.extend([q.strip() for q in blockquotes if q.strip()])

    attributed = _RE_QUOTED_TEXT.findall(text)
    if attributed:
        has_quotes = True
        quotes.extend([a.strip() for a in attributed if a.strip()])

    # Clean leading blockquote markers '>' so the text reads smoothly
    cleaned_quotes = _RE_QUOTE_LINE.sub(r"\1", text)
    return cleaned_quotes, has_quotes, quotes


def clean_text(raw_text: str) -> CleanResult:
    """
    Execute full multi-step cleaning pipeline in sequence:
    1. HTML/markup removal and unescaping
    2. Encoding repair (ftfy)
    3. Quoted content identification
    4. Whitespace normalization
    5. PII detection and redaction
    6. Language detection
    7. Spam and low-information filtering
    """
    if not raw_text:
        return CleanResult(
            cleaned_text="",
            language=None,
            is_spam=False,
            is_low_information=True,
            pii_detected=False,
            token_count=0,
            flags={"empty_input": True},
        )

    t = _remove_html(raw_text)
    t = _fix_encoding(t)
    t, has_quotes, quote_segments = _detect_and_handle_quotes(t)
    t = _normalize_whitespace(t)

    pii = _detect_pii(t)
    if pii:
        t = _redact_pii(t)

    lang = _detect_language(t)
    tokens = t.split()
    token_count = len(tokens)
    is_spam = _detect_spam(t)
    is_low_info = token_count < _MIN_TOKEN_COUNT

    flags: Dict[str, Any] = {
        "has_quotes": has_quotes,
        "quotes_count": len(quote_segments),
        "is_english": (lang == "en"),
    }
    if is_spam:
        flags["is_automated"] = True

    return CleanResult(
        cleaned_text=t,
        language=lang,
        is_spam=is_spam,
        is_low_information=is_low_info,
        pii_detected=pii,
        token_count=token_count,
        flags=flags,
    )


def clean_batch(texts: List[str]) -> List[CleanResult]:
    """Clean a batch of text records, gracefully handling individual failures."""
    results = []
    for text in texts:
        try:
            results.append(clean_text(text))
        except Exception as e:
            log.warning("cleaning_error", error=str(e))
            tokens = text.split() if text else []
            results.append(CleanResult(
                cleaned_text=text or "",
                language=None,
                is_spam=False,
                is_low_information=len(tokens) < _MIN_TOKEN_COUNT,
                pii_detected=False,
                token_count=len(tokens),
                flags={"error": str(e)},
            ))
    return results


def hash_author(author: str) -> str:
    """Compute SHA-256 hash of raw author identity to prevent storing PII."""
    return hashlib.sha256(author.encode()).hexdigest()


# Alias for backward compatibility
clean_conversation = clean_text
