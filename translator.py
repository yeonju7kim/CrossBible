"""짧은 단어/구절 한↔영 번역 — Google Translate 공개 엔드포인트 사용.

키 없이 동작하지만 비공식 endpoint 이므로 대량 호출은 자제. UI 사전 다이얼로그
한 건씩의 호출 용도로만 사용한다.
"""
from __future__ import annotations

import json
import re
from typing import Optional

import requests


URL = "https://translate.googleapis.com/translate_a/single"
HEADERS = {"User-Agent": "Mozilla/5.0 (CrossBible)"}

_HANGUL_RE = re.compile(r"[가-힣]")


def detect_language(text: str) -> str:
    """한글 음절이 하나라도 있으면 'ko', 아니면 'en'."""
    return "ko" if _HANGUL_RE.search(text) else "en"


def translate(text: str, source: Optional[str] = None, target: Optional[str] = None) -> tuple[str, str, str]:
    """(source_lang, target_lang, translated_text)."""
    src = source or detect_language(text)
    tgt = target or ("en" if src == "ko" else "ko")
    params = {
        "client": "gtx",
        "sl": src,
        "tl": tgt,
        "dt": "t",
        "q": text,
    }
    r = requests.get(URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = json.loads(r.text)
    segments = data[0] if data and data[0] else []
    translated = "".join(seg[0] for seg in segments if seg and seg[0])
    return src, tgt, translated.strip()
