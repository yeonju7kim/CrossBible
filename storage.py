"""SQLite 기반 캐시 + 메모 저장.

저작권: 본문은 어느 것도 코드에 임베드하지 않고, 사용자 본인 머신의 캐시에만
원격에서 가져온 텍스트를 저장한다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from reference import Reference


SCHEMA = """
CREATE TABLE IF NOT EXISTS verses (
    translation TEXT NOT NULL,
    book_en TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (translation, book_en, chapter, verse)
);
CREATE TABLE IF NOT EXISTS verse_blob (
    kind TEXT NOT NULL,
    book_en TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (kind, book_en, chapter, verse)
);
CREATE TABLE IF NOT EXISTS notes (
    book_en TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    text TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (book_en, chapter, verse)
);
"""


class Storage:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---- verse text cache ----

    def get_verses(self, translation: str, ref: Reference) -> list[tuple[int, str]] | None:
        cur = self.conn.execute(
            "SELECT verse, text FROM verses WHERE translation=? AND book_en=? AND chapter=? "
            "AND verse BETWEEN ? AND ? ORDER BY verse",
            (translation, ref.book_en, ref.chapter, ref.verse_start, ref.verse_end),
        )
        rows = cur.fetchall()
        expected = ref.verse_end - ref.verse_start + 1
        if len(rows) != expected:
            return None
        return [(int(n), str(t)) for n, t in rows]

    def put_verses(self, translation: str, book_en: str, chapter: int, verses: list[tuple[int, str]]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO verses(translation, book_en, chapter, verse, text) VALUES (?,?,?,?,?)",
            [(translation, book_en, chapter, n, t) for n, t in verses],
        )
        self.conn.commit()

    # ---- per-verse blob (interlinear / commentary HTML or markdown) ----

    def get_blob(self, kind: str, book_en: str, chapter: int, verse: int) -> str | None:
        cur = self.conn.execute(
            "SELECT payload FROM verse_blob WHERE kind=? AND book_en=? AND chapter=? AND verse=?",
            (kind, book_en, chapter, verse),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def put_blob(self, kind: str, book_en: str, chapter: int, verse: int, payload: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO verse_blob(kind, book_en, chapter, verse, payload) VALUES (?,?,?,?,?)",
            (kind, book_en, chapter, verse, payload),
        )
        self.conn.commit()

    # ---- notes ----

    def get_note(self, book_en: str, chapter: int, verse: int) -> str:
        cur = self.conn.execute(
            "SELECT text FROM notes WHERE book_en=? AND chapter=? AND verse=?",
            (book_en, chapter, verse),
        )
        row = cur.fetchone()
        return row[0] if row else ""

    def put_note(self, book_en: str, chapter: int, verse: int, text: str) -> None:
        if not text.strip():
            self.conn.execute(
                "DELETE FROM notes WHERE book_en=? AND chapter=? AND verse=?",
                (book_en, chapter, verse),
            )
        else:
            self.conn.execute(
                "INSERT INTO notes(book_en, chapter, verse, text, updated_at) "
                "VALUES (?,?,?,?, datetime('now')) "
                "ON CONFLICT(book_en, chapter, verse) DO UPDATE SET "
                "text=excluded.text, updated_at=excluded.updated_at",
                (book_en, chapter, verse, text),
            )
        self.conn.commit()
