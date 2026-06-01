"""성구 참조 dataclass."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reference:
    book_en: str
    book_ko: str
    chapter: int
    verse_start: int
    verse_end: int

    @property
    def header_en(self) -> str:
        if self.verse_start == self.verse_end:
            return f"{self.book_en} {self.chapter}:{self.verse_start}"
        return f"{self.book_en} {self.chapter}:{self.verse_start}-{self.verse_end}"

    @property
    def header_ko(self) -> str:
        if self.verse_start == self.verse_end:
            return f"{self.book_ko} {self.chapter}:{self.verse_start}"
        return f"{self.book_ko} {self.chapter}:{self.verse_start}-{self.verse_end}"

    def verse_numbers(self) -> list[int]:
        return list(range(self.verse_start, self.verse_end + 1))
