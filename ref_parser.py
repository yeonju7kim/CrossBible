"""자유 텍스트 성구 참조 파서.

예) "Acts 12:12, 12:25, 13:5, 13:13, 15:37-40, Col 4:10, Philem 1:24"
    "사도행전 12:12, 12:25, 골 4:10"
    "John 3"            (장 전체)
    "요한복음 3:14-21"

규칙
----
- 쉼표(,) 로 토큰 분리. 각 토큰은 다음 중 하나:
    BOOK C:V            한 절
    BOOK C:V-V2         한 장 안의 절 범위
    BOOK C              장 전체
    C:V / C:V-V2 / C    앞 토큰의 책을 그대로 이어 씀 (book carry-over)
- 책 이름은 영문 정식/약어, 한글 정식/약어, 그리고 접두사(prefix) 매칭까지 허용.
  ("Col"→Colossians, "Philem"→Philemon, "행"→Acts)
- 대시는 - – — 모두 허용.
"""
from __future__ import annotations

import re

from bible_books import BOOKS, book_chapters
from reference import Reference


# 토큰: 맨 끝의 "장:절[-절2]" 또는 "장" 을 기준으로 앞부분을 책 이름으로 본다.
# 장:절 구분자는 콜론(:) 과 점(.) 모두 허용 ("Ecc 1:3" == "Ecc 1.3").
_RANGE_RE = re.compile(r"^(?P<book>.*?)\s*(?P<chap>\d+)\s*[.:]\s*(?P<v1>\d+)(?:\s*-\s*(?P<v2>\d+))?$")
_CHAPTER_RE = re.compile(r"^(?P<book>.*?)\s*(?P<chap>\d+)$")


def _normalize(text: str) -> str:
    # 다양한 대시/물결표를 ASCII 하이픈으로 통일 (범위 구분자)
    #   –(en) —(em) −(minus) ~ ～(전각) 〜(물결)
    for ch in ("–", "—", "−", "~", "～", "〜"):
        text = text.replace(ch, "-")
    return text


def resolve_book(name: str) -> tuple[str, str] | None:
    """책 이름(영/한, 약어, 접두사) → (영문 정식명, 한글 정식명). 못 찾으면 None."""
    raw = name.strip().rstrip(". ")  # 약어 뒤 마침표 허용 ("Ecc." → "Ecc")
    if not raw:
        return None
    low = raw.lower()

    # 1) 정확히 일치 (영문 정식/약어 또는 한글 정식/약어)
    for en, ko, en_aliases, ko_aliases, _ in BOOKS:
        if low == en.lower() or raw == ko:
            return (en, ko)
        if any(low == a.lower() for a in en_aliases):
            return (en, ko)
        if any(raw == a for a in ko_aliases):
            return (en, ko)

    # 2) 접두사 매칭 — 영문은 정식명/약어가 입력으로 시작하는 경우,
    #    한글은 정식명/약어가 입력으로 시작하는 경우.
    for en, ko, en_aliases, ko_aliases, _ in BOOKS:
        if en.lower().startswith(low):
            return (en, ko)
        if any(a.lower().startswith(low) for a in en_aliases):
            return (en, ko)
        if ko.startswith(raw):
            return (en, ko)
        if any(a.startswith(raw) for a in ko_aliases):
            return (en, ko)

    return None


def _make_reference(book_en: str, book_ko: str, chap: int,
                    v1: int | None, v2: int | None) -> Reference | None:
    if chap < 1:
        return None
    try:
        max_chap = book_chapters(book_en)
    except KeyError:
        return None
    if chap > max_chap:
        return None
    if v1 is None:  # 장 전체
        return Reference(book_en, book_ko, chap, 1, 1, whole_chapter=True)
    vs = v1
    ve = v2 if v2 is not None else v1
    if ve < vs:
        vs, ve = ve, vs
    if vs < 1:
        return None
    return Reference(book_en, book_ko, chap, vs, ve)


def parse_references(text: str) -> tuple[list[Reference], list[str]]:
    """자유 텍스트를 Reference 리스트로 파싱.

    반환: (references, errors). errors 는 해석하지 못한 토큰 원문 목록.
    """
    refs: list[Reference] = []
    errors: list[str] = []
    current_book: tuple[str, str] | None = None

    for token in _normalize(text).split(","):
        tok = token.strip()
        if not tok:
            continue

        m = _RANGE_RE.match(tok)
        whole = False
        if m is None:
            m = _CHAPTER_RE.match(tok)
            whole = True
        if m is None:
            errors.append(tok)
            continue

        book_part = m.group("book").strip()
        if book_part:
            resolved = resolve_book(book_part)
            if resolved is None:
                errors.append(tok)
                continue
            current_book = resolved
        if current_book is None:
            # 책 없이 시작하는 토큰 (예: 맨 앞이 "12:25")
            errors.append(tok)
            continue

        chap = int(m.group("chap"))
        if whole:
            ref = _make_reference(current_book[0], current_book[1], chap, None, None)
        else:
            v2 = m.group("v2")
            ref = _make_reference(
                current_book[0], current_book[1], chap,
                int(m.group("v1")), int(v2) if v2 else None,
            )
        if ref is None:
            errors.append(tok)
        else:
            refs.append(ref)

    return refs, errors
