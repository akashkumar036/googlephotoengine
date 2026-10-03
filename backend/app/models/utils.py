from __future__ import annotations
import json
import re
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel


def extract_json_from_response(raw_text: str) -> Dict[str, Any]:
    """
    Safely extract JSON object from LLM response text.
    Handles markdown code fences, leading/trailing commentary, and common formatting quirks.
    """
    if not raw_text or not raw_text.strip():
        return {}

    cleaned = raw_text.strip()

    # 1. Try direct json parse first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Check for markdown code fences ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, cleaned)
    if match:
        fence_content = match.group(1).strip()
        try:
            return json.loads(fence_content)
        except Exception:
            cleaned = fence_content

    # 3. Find outermost curly braces { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(json_candidate)
        except Exception:
            # 4. Attempt basic sanitization: remove trailing commas before closing braces
            sanitized = re.sub(r",\s*([\}\]])", r"\1", json_candidate)
            try:
                return json.loads(sanitized)
            except Exception:
                pass

    return {}


def parse_and_validate(raw_text: str, schema_cls: Type[BaseModel]) -> BaseModel:
    """Extract JSON from text and validate against a Pydantic schema."""
    data = extract_json_from_response(raw_text)
    return schema_cls.model_validate(data)
