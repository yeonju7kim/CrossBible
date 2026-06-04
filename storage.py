"""SQLite 기반 캐시 + 메모 저장.

저작권: 본문은 어느 것도 코드에 임베드하지 않고, 사용자 본인 머신의 캐시에만
원격에서 가져온 텍스트를 저장한다.
"""
from __future__ import annotations

import sqlite3
import threading
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
CREATE TABLE IF NOT EXISTS library (
    name TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class Storage:
    """Thread-safe wrapper over a single SQLite connection.

    PyQt UI thread writes notes; background QThread fetches and caches verses.
    sqlite3 connection itself is not thread-safe by default, so we open with
    ``check_same_thread=False`` and serialize access through a Lock.
    """

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    # ---- verse text cache ----

    def get_verses(self, translation: str, ref: Reference) -> list[tuple[int, str]] | None:
        with self._lock:
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
        with self._lock:
            self.conn.executemany(
                "INSERT OR REPLACE INTO verses(translation, book_en, chapter, verse, text) VALUES (?,?,?,?,?)",
                [(translation, book_en, chapter, n, t) for n, t in verses],
            )
            self.conn.commit()

    def get_chapter_verses(self, translation: str, book_en: str, chapter: int) -> list[tuple[int, str]]:
        """한 장에 대해 캐시된 모든 절을 절 번호 순으로 반환 (없으면 빈 리스트)."""
        with self._lock:
            cur = self.conn.execute(
                "SELECT verse, text FROM verses WHERE translation=? AND book_en=? AND chapter=? "
                "ORDER BY verse",
                (translation, book_en, chapter),
            )
            rows = cur.fetchall()
        return [(int(n), str(t)) for n, t in rows]

    def chapter_cached(self, translation: str, book_en: str, chapter: int) -> bool:
        with self._lock:
            cur = self.conn.execute(
                "SELECT 1 FROM verses WHERE translation=? AND book_en=? AND chapter=? LIMIT 1",
                (translation, book_en, chapter),
            )
            return cur.fetchone() is not None

    def search(
        self,
        query: str,
        translations: list[str] | None = None,
        limit: int = 500,
    ) -> list[dict]:
        """캐시된 본문에서 키워드(부분일치, 대소문자 무시) 검색."""
        q = query.strip()
        if not q:
            return []
        params: list = ["%" + q + "%"]
        sql = (
            "SELECT translation, book_en, chapter, verse, text "
            "FROM verses WHERE text LIKE ? COLLATE NOCASE"
        )
        if translations:
            placeholders = ",".join("?" for _ in translations)
            sql += f" AND translation IN ({placeholders})"
            params.extend(translations)
        sql += " ORDER BY book_en, chapter, verse, translation LIMIT ?"
        params.append(int(limit))
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
        return [
            {
                "translation": r[0],
                "book_en": r[1],
                "chapter": int(r[2]),
                "verse": int(r[3]),
                "text": r[4],
            }
            for r in rows
        ]

    def import_from(self, other_path: Path) -> dict:
        """다른 CrossBible DB 파일에서 verses + verse_blob 만 병합.

        - 메모(notes)는 의도적으로 가져오지 않음 — 사용자 개인 데이터라 합치면 충돌하기 쉬움.
        - 같은 키(translation/book/chapter/verse 또는 kind/book/chapter/verse)가 있으면 무시(IGNORE).
        - 반환: 추가된 행 수를 담은 dict.
        """
        with self._lock:
            before_verses = self.conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
            before_blobs = self.conn.execute("SELECT COUNT(*) FROM verse_blob").fetchone()[0]
            self.conn.execute("ATTACH DATABASE ? AS ext", (str(other_path),))
            try:
                # 다른 DB가 같은 스키마인지 확인
                rows = self.conn.execute(
                    "SELECT name FROM ext.sqlite_master WHERE type='table' AND name IN ('verses','verse_blob')"
                ).fetchall()
                tables = {r[0] for r in rows}
                if "verses" not in tables:
                    raise RuntimeError("다른 DB에 verses 테이블이 없습니다 — CrossBible DB 파일이 아닐 수 있어요.")
                self.conn.execute(
                    "INSERT OR IGNORE INTO verses "
                    "SELECT translation, book_en, chapter, verse, text FROM ext.verses"
                )
                if "verse_blob" in tables:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO verse_blob "
                        "SELECT kind, book_en, chapter, verse, payload FROM ext.verse_blob"
                    )
                self.conn.commit()
            finally:
                self.conn.execute("DETACH DATABASE ext")
            after_verses = self.conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
            after_blobs = self.conn.execute("SELECT COUNT(*) FROM verse_blob").fetchone()[0]
        return {
            "verses_added": after_verses - before_verses,
            "blobs_added": after_blobs - before_blobs,
        }

    def stats(self) -> dict:
        """캐시 통계 — 다이얼로그에서 보여줄 용도."""
        with self._lock:
            verses_by_t = dict(self.conn.execute(
                "SELECT translation, COUNT(*) FROM verses GROUP BY translation"
            ).fetchall())
            interlinear = self.conn.execute(
                "SELECT COUNT(*) FROM verse_blob WHERE kind='interlinear'"
            ).fetchone()[0]
            commentary = self.conn.execute(
                "SELECT COUNT(*) FROM verse_blob WHERE kind='commentary'"
            ).fetchone()[0]
            notes = self.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        try:
            size_bytes = self.path.stat().st_size
        except OSError:
            size_bytes = 0
        return {
            "verses_by_translation": verses_by_t,
            "interlinear": int(interlinear),
            "commentary": int(commentary),
            "notes": int(notes),
            "size_bytes": int(size_bytes),
            "path": str(self.path),
        }

    # ---- per-verse blob (interlinear / commentary HTML or markdown) ----

    def get_blob(self, kind: str, book_en: str, chapter: int, verse: int) -> str | None:
        with self._lock:
            cur = self.conn.execute(
                "SELECT payload FROM verse_blob WHERE kind=? AND book_en=? AND chapter=? AND verse=?",
                (kind, book_en, chapter, verse),
            )
            row = cur.fetchone()
        return row[0] if row else None

    def put_blob(self, kind: str, book_en: str, chapter: int, verse: int, payload: str) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO verse_blob(kind, book_en, chapter, verse, payload) VALUES (?,?,?,?,?)",
                (kind, book_en, chapter, verse, payload),
            )
            self.conn.commit()

    # ---- notes ----

    def get_note(self, book_en: str, chapter: int, verse: int) -> str:
        with self._lock:
            cur = self.conn.execute(
                "SELECT text FROM notes WHERE book_en=? AND chapter=? AND verse=?",
                (book_en, chapter, verse),
            )
            row = cur.fetchone()
        return row[0] if row else ""

    def put_note(self, book_en: str, chapter: int, verse: int, text: str) -> None:
        with self._lock:
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

    # ---- 라이브러리 (구절 모음 저장/불러오기) ----

    def save_collection(self, name: str, payload: str) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO library(name, payload, updated_at) VALUES (?,?, datetime('now')) "
                "ON CONFLICT(name) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (name, payload),
            )
            self.conn.commit()

    def list_collections(self) -> list[tuple[str, str]]:
        """저장된 모음 (name, updated_at) 목록 — 최근 수정 순."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT name, updated_at FROM library ORDER BY updated_at DESC, name"
            ).fetchall()
        return [(str(n), str(u)) for n, u in rows]

    def load_collection(self, name: str) -> str | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT payload FROM library WHERE name=?", (name,)
            ).fetchone()
        return row[0] if row else None

    def delete_collection(self, name: str) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM library WHERE name=?", (name,))
            self.conn.commit()
