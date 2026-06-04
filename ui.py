"""PyQt6 메인 윈도우 — 메뉴바, i18n, 테마, 오프라인 다운로드."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QSettings, Qt, QThread, pyqtSignal
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QDesktopServices,
    QIcon,
    QKeySequence,
    QPalette,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from bible_books import book_names_ko, lookup_by_ko
from fetchers import BIBLEHUB_BOOK_SLUGS, CrossBibleFetcher
from ref_parser import parse_references
from reference import Reference
from storage import Storage


# ---------- i18n ----------

LANGUAGES = ["ko", "en"]
LANGUAGE_LABELS = {"ko": "한국어", "en": "English"}

STRINGS: dict[str, dict[str, str]] = {
    "ko": {
        "app.title": "CrossBible — 다중 번역 성경 학습",
        "app.title_with_ref": "CrossBible — {ref}",
        "status.ready": "준비됨",
        "status.done": "완료",
        "status.looking_up": "{ref_ko} ({ref_en}) 조회 중…",
        "status.min_one_translation": "번역본을 최소 하나는 켜두세요.",
        "selector.book": "책",
        "selector.chapter": "장",
        "selector.verse": "절",
        "selector.range_sep": "~",
        "selector.lookup": "조회 (Ctrl+Enter)",
        "selector.whole": "전체",
        "selector.whole_tooltip": "장 전체를 조회합니다 (절 범위 무시).",
        "selector.add": "＋ 추가",
        "selector.add_tooltip": "맨 왼쪽 패널에 이 구절을 쌓습니다.",
        "selector.new_panel": "＋ 새 패널",
        "selector.new_panel_tooltip": "빈 패널을 추가합니다. ◀ ▶ 로 구절을 옮겨올 수 있어요.",
        "selector.refresh": "↻ 새로고침",
        "selector.refresh_tooltip": "현재 화면의 구절을 캐시 무시하고 다시 가져옵니다 (오래되거나 누락된 본문 갱신).",
        "selector.side_on": "원어/주석/메모 패널",
        "selector.side_off": "원어/주석/메모 패널 (꺼짐)",
        "selector.side_tooltip": "F9: 오른쪽 패널 켜기/끄기",
        "multi.placeholder": "여러 구절: Acts 12:12, 12:25, 13:5, 15:37-40, Col 4:10 …",
        "multi.lookup": "조회",
        "multi.add": "＋ 추가",
        "multi.tooltip": "쉼표로 구분. 책 생략 시 앞 구절의 책을 이어 씁니다. 예) Acts 12:12, 12:25, 13:5",
        "parse.none_title": "구절 없음",
        "parse.none_body": "조회할 구절을 입력하세요.",
        "parse.problem_title": "구절 입력 확인",
        "parse.problem_unparsed": "해석하지 못한 구절: {tokens}",
        "passage.remove_tooltip": "이 구절 제거",
        "passage.split_tooltip": "이 구절을 위/아래 둘로 나누기",
        "block.move_left": "왼쪽 패널로 옮기기",
        "block.move_right": "오른쪽 패널로 옮기기",
        "block.move_up": "위로 (패널 안 순서)",
        "block.move_down": "아래로 (패널 안 순서)",
        "panel.empty": "(빈 패널)\n◀ ▶ 로 구절을 옮겨오세요",
        "panel.remove_tooltip": "이 패널 삭제 (구절 포함)",
        "passage.max_title": "패널 한도",
        "passage.max_body": "패널은 최대 {n}개까지예요.",
        "passage.max_reached": "패널은 최대 {n}개 — 처음 {n}개만 표시합니다.",
        "split.title": "패널 나누기",
        "split.label": "{lo}~{hi} 중, 어느 절 뒤에서 나눌까요?",
        "split.need_text": "본문을 받은 뒤에 나눌 수 있어요. 잠시 후 다시 시도해 주세요.",
        "split.too_small": "한 절짜리는 나눌 수 없어요.",
        "menu.library": "라이브러리",
        "library.save": "현재 구절 저장…",
        "library.open": "불러오기 / 관리…",
        "library.save_title": "라이브러리에 저장",
        "library.save_label": "이 구절 모음의 이름:",
        "library.save_empty": "화면에 저장할 구절이 없습니다.",
        "library.saved": "'{name}' 저장됨 ({count}개 구절).",
        "library.dialog_title": "라이브러리",
        "library.intro": "저장한 구절 모음을 불러오거나 관리합니다. 더블클릭하면 불러옵니다.",
        "library.empty": "저장된 모음이 없습니다. 먼저 라이브러리 → 현재 구절 저장… 을 사용하세요.",
        "library.col_name": "이름",
        "library.col_count": "구절 수",
        "library.col_updated": "수정",
        "library.load_replace": "불러오기 (교체)",
        "library.load_add": "현재에 추가",
        "library.delete": "삭제",
        "library.close": "닫기",
        "library.delete_confirm_title": "모음 삭제",
        "library.delete_confirm_body": "'{name}' 모음을 삭제할까요? (본문 캐시는 지워지지 않습니다)",
        "filter.show_translations": "표시할 번역:",
        "filter.interleave": "번갈아보기",
        "filter.interleave_tooltip": "절 단위로 여러 번역을 묶어서 표시합니다.",
        "verse.interlinear_section": "원어 (BibleHub Interlinear)",
        "verse.commentary_section": "주석 (BibleHub Commentaries)",
        "verse.note_section": "메모",
        "verse.note_placeholder": "이 절에 대한 메모를 입력하세요. (자동 저장)",
        "verse.loading": "불러오는 중…",
        "verse.no_commentary": "주석 없음",
        "verse.fetch_failed": "가져오기 실패",
        "verse.commentary_failed": "주석 가져오기 실패",
        "interlinear.col_strong": "Strong",
        "interlinear.col_original": "원어",
        "interlinear.col_translit": "음역",
        "interlinear.col_english": "영어",
        "interlinear.error": "오류",
        "biblehub.label": "BibleHub:",
        "biblehub.compare": "본문 비교",
        "biblehub.interlinear": "원어",
        "biblehub.commentary": "주석",
        "biblehub.lexicon": "렉시콘",
        "menu.settings": "설정",
        "menu.new_window": "새 창 (Ctrl+N)",
        "menu.tools": "도구",
        "menu.theme": "테마",
        "menu.language": "언어",
        "menu.download_all": "전체 다운로드…",
        "menu.search": "검색…",
        "search.title": "본문 검색 (캐시 안)",
        "search.placeholder": "키워드 (한/영, 부분 일치)",
        "search.intro": "이미 다운로드한 본문에서만 검색됩니다. 도구 → 성경 다운로드… 에서 미리 받아두세요.",
        "search.go": "검색",
        "search.translations_label": "번역본",
        "search.col_ref": "참조",
        "search.col_translation": "번역",
        "search.col_preview": "미리보기",
        "search.results_count": "{n}건",
        "search.no_results": "결과 없음",
        "search.too_many": "{n}건 (처음 {limit}건만 표시)",
        "search.empty_cache": "캐시가 비어 있습니다. 도구 → 성경 다운로드… 로 본문을 먼저 받으세요.",
        "search.jump_hint": "더블클릭하면 왼쪽 패널에 추가됩니다.",
        "menu.help": "도움말",
        "menu.feedback": "건의사항 · 이슈 보내기…",
        "menu.about": "버전 정보…",
        "about.title": "CrossBible 정보",
        "about.body": (
            "CrossBible {version}\n\n"
            "여러 한국어/영어 번역본을 한 화면에 보여주는 개인 성경 학습용 데스크탑 앱.\n\n"
            "https://github.com/yeonju7kim/CrossBible"
        ),
        "about.unknown_version": "(버전 정보 없음)",
        "menu.cache_info": "캐시 정보…",
        "menu.export_db": "캐시 백업 (.db 내보내기)…",
        "menu.import_db": "캐시 불러오기 (.db 병합)…",
        "db.export.title": "캐시 백업 저장 위치",
        "db.export.filter": "SQLite DB (*.db);;모든 파일 (*)",
        "db.export.success_title": "백업 완료",
        "db.export.success_body": "캐시 파일을 다음 위치에 저장했습니다:\n{path}",
        "db.export.error_title": "백업 실패",
        "db.export.error_body": "백업 중 오류가 발생했습니다: {message}",
        "db.import.title": "불러올 캐시 .db 선택",
        "db.import.filter": "SQLite DB (*.db);;모든 파일 (*)",
        "db.import.confirm_title": "캐시 병합",
        "db.import.confirm_body": (
            "선택한 DB의 본문/원어/주석 캐시를 현재 캐시에 병합합니다.\n"
            "메모(notes)는 가져오지 않고 본인 PC의 것을 유지합니다.\n"
            "이미 있는 행은 건너뛰니, 안전하게 합칠 수 있어요.\n\n"
            "계속할까요?"
        ),
        "db.import.success_title": "병합 완료",
        "db.import.success_body": "본문 {verses}건, 원어/주석 {blobs}건이 새로 추가되었습니다.",
        "db.import.error_title": "병합 실패",
        "db.import.error_body": "병합 중 오류가 발생했습니다: {message}",
        "cache.title": "캐시 정보",
        "cache.intro": (
            "캐시 파일에는 다음이 저장됩니다:\n"
            "  • 성경 구절 (조회한 절 + 전체 다운로드한 본문)\n"
            "  • 이미 본 절의 원어 (BibleHub Interlinear)\n"
            "  • 이미 본 절의 주석 (BibleHub Commentary)\n"
            "  • 절별 메모\n\n"
            "원어와 주석은 한 번이라도 본 절만 캐시됩니다."
        ),
        "cache.path_label": "위치",
        "cache.size_label": "파일 크기",
        "cache.contents_label": "현재 저장된 항목",
        "cache.verses_line": "본문: {summary} (총 {total}절)",
        "cache.verses_none": "본문: 없음",
        "cache.interlinear_line": "원어: {n}개 절",
        "cache.commentary_line": "주석: {n}개 절",
        "cache.notes_line": "메모: {n}개",
        "cache.open_folder": "폴더 열기",
        "cache.close": "닫기",
        "menu.dictionary": "영어사전…",
        "dictionary.title": "영어사전 (한↔영)",
        "dictionary.prompt": "단어 또는 짧은 구절을 입력하세요. 한글이면 영어로, 영어면 한글로 번역됩니다.",
        "dictionary.search": "검색",
        "dictionary.empty": "검색어를 입력하세요.",
        "dictionary.error": "번역 실패: {message}",
        "language.restart_title": "재시작 필요",
        "language.restart_body": "언어를 바꾸려면 앱을 다시 시작하세요.",
        "download.title": "성경 다운로드",
        "download.prompt_title": "다운로드할 항목 선택",
        "download.intro": (
            "선택한 번역본과 책의 모든 장을 받아 캐시합니다.\n"
            "이미 받은 장은 자동으로 건너뜁니다. 도중에 취소해도 그때까지 받은 분은 유지되니, "
            "다시 열어서 이어받기가 가능합니다."
        ),
        "download.translations_label": "번역본",
        "download.books_label": "책 (필요한 것만 체크)",
        "download.select_all_books": "전체",
        "download.select_ot": "구약",
        "download.select_nt": "신약",
        "download.clear_books": "모두 해제",
        "download.summary": "선택: {books_count}권 × 번역 {trans_count}개 = {total}회 호출 / 약 {minutes}분",
        "download.start": "시작",
        "download.no_selection": "번역본과 책을 하나 이상 선택해주세요.",
        "download.preparing": "준비 중…",
        "download.cancel": "취소",
        "download.canceled_title": "취소됨",
        "download.canceled_body": "다운로드가 취소되었습니다. {done}/{total} 까지 캐시됨.",
        "download.done_title": "다운로드 완료",
        "download.done_body": "{done}/{total} 페이지 캐시됨. 실패: {failures}",
        "download.in_progress": "이미 다운로드가 진행 중입니다.",
    },
    "en": {
        "app.title": "CrossBible — Multi-translation Bible Study",
        "app.title_with_ref": "CrossBible — {ref}",
        "status.ready": "Ready",
        "status.done": "Done",
        "status.looking_up": "Looking up {ref_ko} ({ref_en})…",
        "status.min_one_translation": "Keep at least one translation enabled.",
        "selector.book": "Book",
        "selector.chapter": "Chap",
        "selector.verse": "Verse",
        "selector.range_sep": "~",
        "selector.lookup": "Look up (Ctrl+Enter)",
        "selector.whole": "Whole",
        "selector.whole_tooltip": "Look up the whole chapter (ignores the verse range).",
        "selector.add": "＋ Add",
        "selector.add_tooltip": "Stack this passage onto the leftmost panel.",
        "selector.new_panel": "＋ New panel",
        "selector.new_panel_tooltip": "Add an empty panel. Move blocks into it with ◀ ▶.",
        "selector.refresh": "↻ Refresh",
        "selector.refresh_tooltip": "Re-fetch the current passages ignoring the cache (refresh stale or missing text).",
        "selector.side_on": "Original / Commentary / Notes",
        "selector.side_off": "Original / Commentary / Notes (off)",
        "selector.side_tooltip": "F9: toggle the right panel",
        "multi.placeholder": "Multiple refs: Acts 12:12, 12:25, 13:5, 15:37-40, Col 4:10 …",
        "multi.lookup": "Look up",
        "multi.add": "＋ Add",
        "multi.tooltip": "Comma-separated. Omit the book to carry over the previous one. e.g. Acts 12:12, 12:25, 13:5",
        "parse.none_title": "No reference",
        "parse.none_body": "Enter a reference to look up.",
        "parse.problem_title": "Check your references",
        "parse.problem_unparsed": "Could not parse: {tokens}",
        "passage.remove_tooltip": "Remove this passage",
        "passage.split_tooltip": "Split this passage into top/bottom",
        "block.move_left": "Move to the left panel",
        "block.move_right": "Move to the right panel",
        "block.move_up": "Move up (within panel)",
        "block.move_down": "Move down (within panel)",
        "panel.empty": "(empty panel)\nMove blocks here with ◀ ▶",
        "panel.remove_tooltip": "Delete this panel (with its passages)",
        "passage.max_title": "Panel limit",
        "passage.max_body": "At most {n} panels.",
        "passage.max_reached": "Max {n} panels — showing the first {n}.",
        "split.title": "Split panel",
        "split.label": "Split after which verse? (range {lo}-{hi})",
        "split.need_text": "You can split once the text has loaded. Try again shortly.",
        "split.too_small": "A single verse can't be split.",
        "menu.library": "Library",
        "library.save": "Save current passages…",
        "library.open": "Open / manage…",
        "library.save_title": "Save to library",
        "library.save_label": "Name for this passage set:",
        "library.save_empty": "No passages on screen to save.",
        "library.saved": "Saved '{name}' ({count} passages).",
        "library.dialog_title": "Library",
        "library.intro": "Load or manage your saved passage sets. Double-click to load.",
        "library.empty": "No saved sets yet. Use Library → Save current passages… first.",
        "library.col_name": "Name",
        "library.col_count": "Passages",
        "library.col_updated": "Updated",
        "library.load_replace": "Load (replace)",
        "library.load_add": "Add to current",
        "library.delete": "Delete",
        "library.close": "Close",
        "library.delete_confirm_title": "Delete set",
        "library.delete_confirm_body": "Delete the set '{name}'? (verse cache is not removed)",
        "filter.show_translations": "Show translations:",
        "filter.interleave": "Interleave",
        "filter.interleave_tooltip": "Group translations per verse.",
        "verse.interlinear_section": "Original (BibleHub Interlinear)",
        "verse.commentary_section": "Commentary (BibleHub Commentaries)",
        "verse.note_section": "Notes",
        "verse.note_placeholder": "Write your note for this verse. (auto-saved)",
        "verse.loading": "Loading…",
        "verse.no_commentary": "No commentary",
        "verse.fetch_failed": "Fetch failed",
        "verse.commentary_failed": "Commentary fetch failed",
        "interlinear.col_strong": "Strong",
        "interlinear.col_original": "Original",
        "interlinear.col_translit": "Translit",
        "interlinear.col_english": "English",
        "interlinear.error": "Error",
        "biblehub.label": "BibleHub:",
        "biblehub.compare": "compare",
        "biblehub.interlinear": "interlinear",
        "biblehub.commentary": "commentary",
        "biblehub.lexicon": "lexicon",
        "menu.settings": "Settings",
        "menu.new_window": "New window (Ctrl+N)",
        "menu.tools": "Tools",
        "menu.theme": "Theme",
        "menu.language": "Language",
        "menu.download_all": "Download all chapters…",
        "menu.search": "Search…",
        "search.title": "Search Bible text (cached)",
        "search.placeholder": "Keyword (Korean or English, substring)",
        "search.intro": "Only verses you've already downloaded are searched. Use Tools → Download Bible first.",
        "search.go": "Search",
        "search.translations_label": "Translations",
        "search.col_ref": "Reference",
        "search.col_translation": "Translation",
        "search.col_preview": "Preview",
        "search.results_count": "{n} result(s)",
        "search.no_results": "No results",
        "search.too_many": "{n} matches (showing first {limit})",
        "search.empty_cache": "Cache is empty. Run Tools → Download Bible first.",
        "search.jump_hint": "Double-click a row to add it to the left panel.",
        "menu.help": "Help",
        "menu.feedback": "Send feedback / open an issue…",
        "menu.about": "About…",
        "about.title": "About CrossBible",
        "about.body": (
            "CrossBible {version}\n\n"
            "A personal desktop app that puts multiple Korean / English Bible translations side by side.\n\n"
            "https://github.com/yeonju7kim/CrossBible"
        ),
        "about.unknown_version": "(version unknown)",
        "menu.cache_info": "Cache info…",
        "menu.export_db": "Back up cache (.db export)…",
        "menu.import_db": "Import cache (.db merge)…",
        "db.export.title": "Save cache backup as…",
        "db.export.filter": "SQLite DB (*.db);;All files (*)",
        "db.export.success_title": "Backup saved",
        "db.export.success_body": "Cache file saved to:\n{path}",
        "db.export.error_title": "Backup failed",
        "db.export.error_body": "Could not save the backup: {message}",
        "db.import.title": "Select a CrossBible .db to import",
        "db.import.filter": "SQLite DB (*.db);;All files (*)",
        "db.import.confirm_title": "Merge cache",
        "db.import.confirm_body": (
            "Merges verses / interlinear / commentary from the chosen DB into your current cache.\n"
            "Notes are intentionally kept from your local DB (not imported).\n"
            "Existing rows are skipped, so the merge is safe to repeat.\n\n"
            "Proceed?"
        ),
        "db.import.success_title": "Merge complete",
        "db.import.success_body": "Added {verses} verses and {blobs} interlinear/commentary entries.",
        "db.import.error_title": "Merge failed",
        "db.import.error_body": "Could not merge: {message}",
        "cache.title": "Cache info",
        "cache.intro": (
            "The cache file stores:\n"
            "  • Bible verses (verses you looked up + any whole-book download)\n"
            "  • Interlinear data for verses you've already viewed (BibleHub)\n"
            "  • Commentary for verses you've already viewed (BibleHub)\n"
            "  • Per-verse notes\n\n"
            "Interlinear and commentary are cached only for verses you have viewed."
        ),
        "cache.path_label": "Location",
        "cache.size_label": "File size",
        "cache.contents_label": "Currently stored",
        "cache.verses_line": "Verses: {summary} (total {total})",
        "cache.verses_none": "Verses: none",
        "cache.interlinear_line": "Interlinear: {n} verses",
        "cache.commentary_line": "Commentary: {n} verses",
        "cache.notes_line": "Notes: {n}",
        "cache.open_folder": "Open folder",
        "cache.close": "Close",
        "menu.dictionary": "Dictionary…",
        "dictionary.title": "Dictionary (Korean ↔ English)",
        "dictionary.prompt": "Type a word or short phrase. Korean is translated to English and vice versa.",
        "dictionary.search": "Search",
        "dictionary.empty": "Enter a word to look up.",
        "dictionary.error": "Translation failed: {message}",
        "language.restart_title": "Restart required",
        "language.restart_body": "Restart the app to apply the language change.",
        "download.title": "Download Bible",
        "download.prompt_title": "Choose what to download",
        "download.intro": (
            "Cache every chapter of the selected translations × books.\n"
            "Already-cached chapters are skipped, so canceling and reopening this dialog resumes where you left off."
        ),
        "download.translations_label": "Translations",
        "download.books_label": "Books (check the ones you want)",
        "download.select_all_books": "All",
        "download.select_ot": "OT",
        "download.select_nt": "NT",
        "download.clear_books": "Clear",
        "download.summary": "Selected: {books_count} books × {trans_count} translations = {total} requests / ~{minutes} min",
        "download.start": "Start",
        "download.no_selection": "Select at least one translation and one book.",
        "download.preparing": "Preparing…",
        "download.cancel": "Cancel",
        "download.canceled_title": "Canceled",
        "download.canceled_body": "Download canceled. Cached up to {done}/{total}.",
        "download.done_title": "Download complete",
        "download.done_body": "{done}/{total} pages cached. Failures: {failures}",
        "download.in_progress": "A download is already in progress.",
    },
}

_CURRENT_LANG = "ko"


def set_language(lang: str) -> None:
    global _CURRENT_LANG
    if lang in STRINGS:
        _CURRENT_LANG = lang


def tr(key: str, **kwargs) -> str:
    table = STRINGS.get(_CURRENT_LANG, STRINGS["ko"])
    value = table.get(key) or STRINGS["ko"].get(key) or key
    if kwargs:
        try:
            return value.format(**kwargs)
        except Exception:
            return value
    return value


# ---------- 패널 모델 ----------

@dataclass
class Panel:
    """세로 구절 묶음. blocks 는 위→아래 구절 순서, interleave 는 패널별 번갈아보기."""
    blocks: list[Reference] = field(default_factory=list)
    interleave: bool = False


# ---------- 라이브러리 직렬화 ----------

def _ref_to_dict(r: Reference) -> dict:
    return {
        "book_en": r.book_en,
        "book_ko": r.book_ko,
        "chapter": r.chapter,
        "vs": r.verse_start,
        "ve": r.verse_end,
        "whole": r.whole_chapter,
    }


def _ref_from_dict(d: dict) -> Reference:
    return Reference(
        d["book_en"], d["book_ko"], int(d["chapter"]),
        int(d["vs"]), int(d["ve"]), bool(d.get("whole", False)),
    )


def serialize_panels(panels: list[Panel]) -> str:
    return json.dumps(
        [{"interleave": p.interleave, "blocks": [_ref_to_dict(r) for r in p.blocks]}
         for p in panels],
        ensure_ascii=False,
    )


def deserialize_panels(payload: str) -> list[Panel]:
    """패널 구조 복원. 구버전(평면 구절 리스트) 저장본은 각 구절을 패널 하나로."""
    try:
        data = json.loads(payload)
    except Exception:
        return []
    out: list[Panel] = []
    for item in data:
        if isinstance(item, dict) and "blocks" in item:  # 신버전: 패널
            blocks = []
            for d in item["blocks"]:
                try:
                    blocks.append(_ref_from_dict(d))
                except Exception:
                    continue
            out.append(Panel(blocks, bool(item.get("interleave", False))))
        else:  # 구버전: 구절 하나 → 패널 하나
            try:
                out.append(Panel([_ref_from_dict(item)]))
            except Exception:
                continue
    return out


# ---------- BibleHub 링크 ----------

def _biblehub_links_html(book_en: str, chapter: int, verse: int) -> str:
    slug = BIBLEHUB_BOOK_SLUGS.get(book_en)
    if not slug:
        return ""
    base = "https://biblehub.com"
    cv = f"{chapter}-{verse}"
    parts = [
        f'<a href="{base}/{slug}/{cv}.htm">{tr("biblehub.compare")}</a>',
        f'<a href="{base}/interlinear/{slug}/{cv}.htm">{tr("biblehub.interlinear")}</a>',
        f'<a href="{base}/commentaries/{slug}/{cv}.htm">{tr("biblehub.commentary")}</a>',
        f'<a href="{base}/lexicon/{slug}/{cv}.htm">{tr("biblehub.lexicon")}</a>',
    ]
    return (
        f"<span style='font-size:10pt; color:#888'>{tr('biblehub.label')} "
        + " · ".join(parts)
        + "</span>"
    )


# ---------- 테마 ----------

THEMES = ["System", "Fusion Light", "Fusion Dark", "Solarized Light"]


def apply_theme(app: QApplication, theme: str) -> None:
    if theme == "System":
        app.setStyle("")
        app.setPalette(app.style().standardPalette())
        return

    app.setStyle("Fusion")

    if theme == "Fusion Light":
        app.setPalette(app.style().standardPalette())
        return

    p = QPalette()

    if theme == "Fusion Dark":
        bg = QColor(53, 53, 53)
        base = QColor(35, 35, 35)
        text = QColor(220, 220, 220)
        highlight = QColor(42, 130, 218)
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, text)
        p.setColor(QPalette.ColorRole.Base, base)
        p.setColor(QPalette.ColorRole.AlternateBase, bg)
        p.setColor(QPalette.ColorRole.Text, text)
        p.setColor(QPalette.ColorRole.Button, bg)
        p.setColor(QPalette.ColorRole.ButtonText, text)
        p.setColor(QPalette.ColorRole.ToolTipBase, bg)
        p.setColor(QPalette.ColorRole.ToolTipText, text)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor(150, 150, 150))
        p.setColor(QPalette.ColorRole.Highlight, highlight)
        p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Link, QColor(100, 170, 240))
    elif theme == "Solarized Light":
        bg = QColor(253, 246, 227)
        base = QColor(238, 232, 213)
        text = QColor(88, 110, 117)
        highlight = QColor(38, 139, 210)
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, text)
        p.setColor(QPalette.ColorRole.Base, base)
        p.setColor(QPalette.ColorRole.AlternateBase, bg)
        p.setColor(QPalette.ColorRole.Text, text)
        p.setColor(QPalette.ColorRole.Button, base)
        p.setColor(QPalette.ColorRole.ButtonText, text)
        p.setColor(QPalette.ColorRole.ToolTipBase, base)
        p.setColor(QPalette.ColorRole.ToolTipText, text)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor(147, 161, 161))
        p.setColor(QPalette.ColorRole.Highlight, highlight)
        p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Link, QColor(38, 139, 210))
    else:
        p = app.style().standardPalette()

    app.setPalette(p)


# ---------- 백그라운드 작업 ----------

class DownloadWorker(QObject):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int, list)

    def __init__(self, fetcher: CrossBibleFetcher, translations: list[str], books: list[str] | None):
        super().__init__()
        self.fetcher = fetcher
        self.translations = translations
        self.books = books
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        done, total, failures = self.fetcher.download_all(
            self.translations,
            progress_cb=lambda d, t, label: self.progress.emit(d, t, label),
            cancel_cb=lambda: self._cancel,
            books=self.books,
        )
        self.finished.emit(done, total, failures)


class TranslateWorker(QObject):
    """사전 다이얼로그용 단어 번역 워커."""

    done = pyqtSignal(str, str, str, str)   # source_lang, target_lang, translated, original
    error = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            from translator import translate
            src, tgt, translated = translate(self.text)
            self.done.emit(src, tgt, translated, self.text)
        except Exception as e:
            self.error.emit(str(e))


class DictionaryDialog(QDialog):
    """한↔영 단어 번역 팝업창."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dictionary.title"))
        self.resize(560, 380)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        prompt = QLabel(tr("dictionary.prompt"))
        prompt.setWordWrap(True)
        prompt.setStyleSheet("color:#888;")
        v.addWidget(prompt)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.returnPressed.connect(self._lookup)
        self.search_btn = QPushButton(tr("dictionary.search"))
        self.search_btn.clicked.connect(self._lookup)
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.search_btn)
        v.addLayout(input_row)

        self.result = QTextBrowser()
        self.result.setOpenExternalLinks(True)
        v.addWidget(self.result, 1)

        self._thread: QThread | None = None
        self._worker: TranslateWorker | None = None

        self.input_edit.setFocus()

    def _lookup(self):
        text = self.input_edit.text().strip()
        if not text:
            self.result.setHtml(f"<p style='color:#888'>{tr('dictionary.empty')}</p>")
            return

        if self._thread is not None:
            try:
                self._thread.quit()
                self._thread.wait()
            except Exception:
                pass

        self.search_btn.setEnabled(False)
        self.result.setHtml(f"<p style='color:#888'>{tr('verse.loading')}</p>")

        self._thread = QThread(self)
        self._worker = TranslateWorker(text)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()

    def _on_done(self, src: str, tgt: str, translated: str, original: str):
        safe_original = original.replace("<", "&lt;").replace(">", "&gt;")
        safe_translated = translated.replace("<", "&lt;").replace(">", "&gt;")
        html = (
            f"<p style='color:#888; font-size:9pt'>{src} → {tgt}</p>"
            f"<p style='font-size:11pt'><b>{safe_original}</b></p>"
            f"<hr/>"
            f"<p style='font-size:15pt'>{safe_translated}</p>"
        )
        self.result.setHtml(html)

    def _on_error(self, message: str):
        self.result.setHtml(
            f"<p style='color:#c33'>{tr('dictionary.error', message=message)}</p>"
        )

    def _cleanup(self):
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self.search_btn.setEnabled(True)


class DownloadSelectionDialog(QDialog):
    """다운로드할 번역본 + 책을 고르는 다이얼로그."""

    def __init__(self, default_translations: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("download.prompt_title"))
        self.resize(520, 640)

        from bible_books import BOOKS

        v = QVBoxLayout(self)
        v.setSpacing(8)

        intro = QLabel(tr("download.intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#888;")
        v.addWidget(intro)

        # 번역본 체크박스
        v.addWidget(_section_label(tr("download.translations_label"), level=2))
        trans_row = QHBoxLayout()
        self.trans_checks: dict[str, QCheckBox] = {}
        for code in CrossBibleFetcher.TRANSLATIONS:
            cb = QCheckBox(CrossBibleFetcher.TRANSLATION_LABELS[code])
            cb.setChecked(code in default_translations)
            cb.toggled.connect(self._refresh_summary)
            self.trans_checks[code] = cb
            trans_row.addWidget(cb)
        trans_row.addStretch(1)
        v.addLayout(trans_row)

        # 책 빠른 선택 버튼
        v.addWidget(_section_label(tr("download.books_label"), level=2))
        quick_row = QHBoxLayout()
        btn_all = QPushButton(tr("download.select_all_books"))
        btn_ot = QPushButton(tr("download.select_ot"))
        btn_nt = QPushButton(tr("download.select_nt"))
        btn_clear = QPushButton(tr("download.clear_books"))
        for b in (btn_all, btn_ot, btn_nt, btn_clear):
            quick_row.addWidget(b)
        quick_row.addStretch(1)
        v.addLayout(quick_row)

        # 66권 체크 가능 리스트
        self.book_list = QListWidget()
        self._items: list[QListWidgetItem] = []
        for en, ko, _, _, chapters in BOOKS:
            item = QListWidgetItem(f"{ko}  ({chapters}장)")
            item.setData(Qt.ItemDataRole.UserRole, en)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.book_list.addItem(item)
            self._items.append(item)
        self.book_list.itemChanged.connect(lambda _it: self._refresh_summary())
        v.addWidget(self.book_list, 1)

        # 빠른 선택 핸들러
        def set_all(state: Qt.CheckState):
            for it in self._items:
                it.setCheckState(state)
        def set_range(start: int, end: int):
            for i, it in enumerate(self._items):
                it.setCheckState(
                    Qt.CheckState.Checked if start <= i < end else Qt.CheckState.Unchecked
                )
        btn_all.clicked.connect(lambda: set_all(Qt.CheckState.Checked))
        btn_clear.clicked.connect(lambda: set_all(Qt.CheckState.Unchecked))
        btn_ot.clicked.connect(lambda: set_range(0, 39))   # 창세기~말라기
        btn_nt.clicked.connect(lambda: set_range(39, 66))  # 마태복음~요한계시록

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color:#666; padding-top:6px;")
        v.addWidget(self.summary_label)

        # OK / 취소
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText(tr("download.start"))
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        v.addWidget(btn_box)

        self._refresh_summary()

    def _refresh_summary(self):
        from bible_books import BOOKS

        translations = self.selected_translations()
        chosen_books = set(self.selected_books())
        trans_count = len(translations)
        books_count = len(chosen_books)
        chapters_sum = sum(
            chapters for en, _, _, _, chapters in BOOKS if en in chosen_books
        )
        total = chapters_sum * trans_count
        minutes = max(1, round(total * 0.7 / 60))
        self.summary_label.setText(
            tr(
                "download.summary",
                books_count=books_count,
                trans_count=trans_count,
                total=total,
                minutes=minutes,
            )
        )

    def selected_translations(self) -> list[str]:
        return [code for code, cb in self.trans_checks.items() if cb.isChecked()]

    def selected_books(self) -> list[str]:
        return [
            it.data(Qt.ItemDataRole.UserRole)
            for it in self._items
            if it.checkState() == Qt.CheckState.Checked
        ]


class SearchDialog(QDialog):
    """캐시된 본문에서 키워드 검색. 결과 더블클릭 시 메인 윈도우에서 그 절을 lookup."""

    SEARCH_LIMIT = 500

    verse_selected = pyqtSignal(str, int, int)  # book_en, chapter, verse

    def __init__(self, storage: Storage, default_translations: list[str], parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle(tr("search.title"))
        self.resize(720, 520)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        # 안내 — 캐시된 본문만 검색됨을 항상 표시
        intro = QLabel(tr("search.intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#888;")
        v.addWidget(intro)

        # 입력 행
        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText(tr("search.placeholder"))
        self.input_edit.returnPressed.connect(self._do_search)
        self.go_btn = QPushButton(tr("search.go"))
        self.go_btn.clicked.connect(self._do_search)
        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.go_btn)
        v.addLayout(input_row)

        # 번역본 체크박스
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel(tr("search.translations_label") + ":"))
        self.trans_checks: dict[str, QCheckBox] = {}
        for code in CrossBibleFetcher.TRANSLATIONS:
            cb = QCheckBox(CrossBibleFetcher.TRANSLATION_LABELS[code])
            cb.setChecked(code in default_translations)
            self.trans_checks[code] = cb
            filter_row.addWidget(cb)
        filter_row.addStretch(1)
        v.addLayout(filter_row)

        # 결과 테이블
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            tr("search.col_ref"),
            tr("search.col_translation"),
            tr("search.col_preview"),
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self._on_row_activated)
        v.addWidget(self.table, 1)

        self.status = QLabel(tr("search.jump_hint"))
        self.status.setStyleSheet("color:#888;")
        v.addWidget(self.status)

        self.input_edit.setFocus()

    def _selected_translations(self) -> list[str]:
        return [c for c, cb in self.trans_checks.items() if cb.isChecked()]

    def _do_search(self):
        query = self.input_edit.text().strip()
        translations = self._selected_translations()
        if not query or not translations:
            self.table.setRowCount(0)
            return

        rows = self.storage.search(query, translations=translations, limit=self.SEARCH_LIMIT)
        # 캐시 자체가 비어있는지 확인
        if not rows:
            stats = self.storage.stats()
            if not stats["verses_by_translation"]:
                self.status.setText(tr("search.empty_cache"))
            else:
                self.status.setText(tr("search.no_results"))
            self.table.setRowCount(0)
            return

        # 같은 절이 여러 번역에 다 있으면 모두 표시 (사용자가 비교 가능)
        from bible_books import BOOKS
        en_to_ko = {en: ko for en, ko, _, _, _ in BOOKS}

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            ref_str = f"{en_to_ko.get(r['book_en'], r['book_en'])} {r['chapter']}:{r['verse']}"
            preview = self._snippet(r["text"], query)
            ref_item = QTableWidgetItem(ref_str)
            ref_item.setData(Qt.ItemDataRole.UserRole, (r["book_en"], r["chapter"], r["verse"]))
            self.table.setItem(i, 0, ref_item)
            self.table.setItem(i, 1, QTableWidgetItem(
                CrossBibleFetcher.TRANSLATION_LABELS.get(r["translation"], r["translation"])
            ))
            self.table.setItem(i, 2, QTableWidgetItem(preview))
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)

        if len(rows) >= self.SEARCH_LIMIT:
            self.status.setText(tr("search.too_many", n=len(rows), limit=self.SEARCH_LIMIT))
        else:
            self.status.setText(tr("search.results_count", n=len(rows)))

    @staticmethod
    def _snippet(text: str, needle: str, radius: int = 30) -> str:
        idx = text.lower().find(needle.lower())
        if idx < 0:
            return text[:80] + ("…" if len(text) > 80 else "")
        start = max(0, idx - radius)
        end = min(len(text), idx + len(needle) + radius)
        out = text[start:end]
        if start > 0:
            out = "…" + out
        if end < len(text):
            out = out + "…"
        return out

    def _on_row_activated(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        book_en, chapter, verse = data
        self.verse_selected.emit(book_en, int(chapter), int(verse))


class LibraryDialog(QDialog):
    """저장된 구절 모음 불러오기/추가/삭제."""

    load_replace = pyqtSignal(list)  # list[Panel]
    load_add = pyqtSignal(list)      # list[Panel]

    def __init__(self, storage: Storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle(tr("library.dialog_title"))
        self.resize(560, 420)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        intro = QLabel(tr("library.intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#888;")
        v.addWidget(intro)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            tr("library.col_name"),
            tr("library.col_count"),
            tr("library.col_updated"),
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(lambda _i: self._load(replace=True))
        v.addWidget(self.table, 1)

        self.empty_label = QLabel(tr("library.empty"))
        self.empty_label.setStyleSheet("color:#888;")
        self.empty_label.setWordWrap(True)
        v.addWidget(self.empty_label)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton(tr("library.load_replace"))
        self.load_btn.clicked.connect(lambda: self._load(replace=True))
        self.add_btn = QPushButton(tr("library.load_add"))
        self.add_btn.clicked.connect(lambda: self._load(replace=False))
        self.delete_btn = QPushButton(tr("library.delete"))
        self.delete_btn.clicked.connect(self._delete)
        close_btn = QPushButton(tr("library.close"))
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        v.addLayout(btn_row)

        self.refresh()

    def refresh(self):
        rows = self.storage.list_collections()
        self.table.setRowCount(len(rows))
        for i, (name, updated) in enumerate(rows):
            payload = self.storage.load_collection(name) or "[]"
            count = sum(len(p.blocks) for p in deserialize_panels(payload))
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, name)
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.table.setItem(i, 2, QTableWidgetItem(updated))
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)
        has = len(rows) > 0
        self.empty_label.setVisible(not has)
        self.table.setVisible(has)
        for b in (self.load_btn, self.add_btn, self.delete_btn):
            b.setEnabled(has)

    def _selected_name(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _load(self, replace: bool):
        name = self._selected_name()
        if name is None:
            return
        panels = deserialize_panels(self.storage.load_collection(name) or "[]")
        if not panels:
            return
        (self.load_replace if replace else self.load_add).emit(panels)
        self.accept()

    def _delete(self):
        name = self._selected_name()
        if name is None:
            return
        confirm = QMessageBox.question(
            self,
            tr("library.delete_confirm_title"),
            tr("library.delete_confirm_body", name=name),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.storage.delete_collection(name)
        self.refresh()


class VersesWorker(QObject):
    """필요한 (구절, 번역본) 쌍의 '본문'만 가져온다. 원어/주석은 지연 로딩.

    데이터를 위치(index)가 아니라 Reference 로 식별하므로, 화면에서 순서를 바꿔도
    이미 받은 결과는 그대로 재사용된다(재조회 불필요).
    """

    verses_ready = pyqtSignal(object, str, list)   # ref, translation, verses
    error = pyqtSignal(object, str, str)           # ref, translation, message
    finished = pyqtSignal()

    def __init__(self, fetcher: CrossBibleFetcher,
                 targets: list[tuple[Reference, str]], force: bool = False):
        super().__init__()
        self.fetcher = fetcher
        self.targets = targets
        self.force = force
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        for ref, t in self.targets:
            if self._cancel:
                self.finished.emit()
                return
            try:
                verses = self.fetcher.get_verses(t, ref, force=self.force)
                self.verses_ready.emit(ref, t, verses)
            except Exception as e:
                self.error.emit(ref, t, str(e))
        self.finished.emit()


class ExtrasWorker(QObject):
    """한 절의 원어(interlinear) + 주석(commentary) 을 지연 조회."""

    interlinear_ready = pyqtSignal(list)
    commentary_ready = pyqtSignal(str)
    error = pyqtSignal(str, str)   # kind, message
    finished = pyqtSignal()

    def __init__(self, fetcher: CrossBibleFetcher, book_en: str, chapter: int, verse: int):
        super().__init__()
        self.fetcher = fetcher
        self.book_en = book_en
        self.chapter = chapter
        self.verse = verse

    def run(self):
        try:
            words = self.fetcher.get_interlinear(self.book_en, self.chapter, self.verse)
            self.interlinear_ready.emit(words)
        except Exception as e:
            self.error.emit("interlinear", str(e))
        try:
            text = self.fetcher.get_commentary(self.book_en, self.chapter, self.verse)
            self.commentary_ready.emit(text)
        except Exception as e:
            self.error.emit("commentary", str(e))
        self.finished.emit()


# ---------- 보조 위젯 ----------

def _section_label(text: str, *, level: int = 1) -> QLabel:
    lbl = QLabel(text)
    f = lbl.font()
    f.setBold(True)
    f.setPointSize(f.pointSize() + (2 if level == 1 else 1))
    lbl.setFont(f)
    return lbl


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class InterlinearTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels([
            tr("interlinear.col_strong"),
            tr("interlinear.col_original"),
            tr("interlinear.col_translit"),
            tr("interlinear.col_english"),
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_loading(self):
        self.setRowCount(1)
        item = QTableWidgetItem(tr("verse.loading"))
        item.setForeground(Qt.GlobalColor.gray)
        self.setItem(0, 0, item)
        for c in (1, 2, 3):
            self.setItem(0, c, QTableWidgetItem(""))
        self._fit_height()

    def set_words(self, words: list[dict[str, str]]):
        self.setRowCount(len(words))
        for row, wd in enumerate(words):
            for col, key in enumerate(("strong", "original", "translit", "english")):
                item = QTableWidgetItem(wd.get(key, ""))
                if key == "original":
                    f = item.font()
                    f.setPointSize(f.pointSize() + 2)
                    item.setFont(f)
                self.setItem(row, col, item)
        self._fit_height()

    def set_error(self, message: str):
        self.setRowCount(1)
        self.setItem(0, 0, QTableWidgetItem(tr("interlinear.error")))
        self.setItem(0, 1, QTableWidgetItem(message))
        self._fit_height()

    def _fit_height(self):
        self.resizeRowsToContents()
        header = self.horizontalHeader().height()
        rows = sum(self.rowHeight(r) for r in range(self.rowCount()))
        self.setFixedHeight(header + rows + 4)


class VerseBlock(QWidget):
    """절별 원어/주석/메모 블록. 접이식 + 지연 로딩.

    헤더 버튼을 펼칠 때 비로소 본체(원어 표·주석·메모)를 만들고, 그때 한 번만
    원어/주석을 네트워크/캐시에서 가져온다. 한 장 전체(수십~수백 절)를 띄워도
    펼치기 전에는 가벼운 헤더만 존재한다.
    """

    def __init__(self, ref: Reference, verse: int, storage: Storage, fetcher: CrossBibleFetcher):
        super().__init__()
        self.ref = ref
        self.verse = verse
        self.storage = storage
        self.fetcher = fetcher
        self._body_built = False
        self._extras_loaded = False
        self._ex_thread: QThread | None = None
        self._ex_worker: ExtrasWorker | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        self.toggle_btn = QPushButton(f"▶  {ref.book_ko} {ref.chapter}:{verse}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setStyleSheet("text-align:left; font-weight:bold; border:none; padding:2px;")
        self.toggle_btn.toggled.connect(self._on_toggled)
        header_row.addWidget(self.toggle_btn)
        links = QLabel(_biblehub_links_html(ref.book_en, ref.chapter, verse))
        links.setTextFormat(Qt.TextFormat.RichText)
        links.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        links.setOpenExternalLinks(True)
        header_row.addWidget(links, 1)
        v.addLayout(header_row)

        # 본체는 펼칠 때 만든다.
        self.body = QWidget()
        self.body.setVisible(False)
        self._body_layout = QVBoxLayout(self.body)
        self._body_layout.setContentsMargins(8, 0, 0, 0)
        self._body_layout.setSpacing(6)
        v.addWidget(self.body)

        v.addWidget(_hline())

    # ---- 펼치기/접기 ----

    def _on_toggled(self, checked: bool):
        self.toggle_btn.setText(
            f"{'▼' if checked else '▶'}  {self.ref.book_ko} {self.ref.chapter}:{self.verse}"
        )
        if checked and not self._body_built:
            self._build_body()
        self.body.setVisible(checked)
        if checked and not self._extras_loaded:
            self._load_extras()

    def expand(self):
        """프로그램적으로 펼치기 (nav 점프 시 사용)."""
        if not self.toggle_btn.isChecked():
            self.toggle_btn.setChecked(True)

    def _build_body(self):
        self._body_layout.addWidget(_section_label(tr("verse.interlinear_section"), level=2))
        self.interlinear = InterlinearTable()
        self._body_layout.addWidget(self.interlinear)

        self._body_layout.addWidget(_section_label(tr("verse.commentary_section"), level=2))
        self.commentary = QTextBrowser()
        self.commentary.setOpenExternalLinks(True)
        self.commentary.setFixedHeight(360)
        self._body_layout.addWidget(self.commentary)

        self._body_layout.addWidget(_section_label(tr("verse.note_section"), level=2))
        self.note = QPlainTextEdit()
        self.note.setPlaceholderText(tr("verse.note_placeholder"))
        self.note.setFixedHeight(150)
        self.note.setPlainText(
            self.storage.get_note(self.ref.book_en, self.ref.chapter, self.verse)
        )
        self.note.textChanged.connect(self._save_note)
        self._body_layout.addWidget(self.note)

        self._body_built = True

    # ---- 지연 원어/주석 로딩 ----

    def _load_extras(self):
        self._extras_loaded = True
        self.interlinear.set_loading()
        self.commentary.setHtml(f"<p style='color:#888'>{tr('verse.loading')}</p>")

        # 스레드를 블록이 아니라 최상위 윈도우에 귀속시킨다. 새 조회로 이 블록이
        # 삭제돼도 진행 중 스레드가 함께 파괴되지 않고 스스로 끝나 정리되도록.
        # (블록이 사라지면 워커→블록 슬롯 연결은 Qt 가 자동 해제하므로 안전)
        self._ex_thread = QThread(self.window())
        self._ex_worker = ExtrasWorker(self.fetcher, self.ref.book_en, self.ref.chapter, self.verse)
        self._ex_worker.moveToThread(self._ex_thread)
        self._ex_thread.started.connect(self._ex_worker.run)
        self._ex_worker.interlinear_ready.connect(self._set_interlinear)
        self._ex_worker.commentary_ready.connect(self._set_commentary)
        self._ex_worker.error.connect(self._on_extras_error)
        self._ex_worker.finished.connect(self._ex_thread.quit)
        self._ex_thread.finished.connect(self._ex_worker.deleteLater)
        self._ex_thread.finished.connect(self._ex_thread.deleteLater)
        self._ex_thread.finished.connect(self._clear_extras_refs)
        self._ex_thread.start()

    def _clear_extras_refs(self):
        self._ex_worker = None
        self._ex_thread = None

    def _save_note(self):
        self.storage.put_note(self.ref.book_en, self.ref.chapter, self.verse,
                              self.note.toPlainText())

    def _set_interlinear(self, words: list):
        self.interlinear.set_words(words)

    def _set_commentary(self, text: str):
        html_parts = []
        for block in text.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            if block.startswith("### "):
                html_parts.append(f"<h3>{block[4:].strip()}</h3>")
            else:
                safe = block.replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f"<p>{safe}</p>")
        self.commentary.setHtml(
            "\n".join(html_parts) or f"<p style='color:#888'>{tr('verse.no_commentary')}</p>"
        )

    def _on_extras_error(self, kind: str, message: str):
        if kind == "interlinear":
            self.interlinear.set_error(message)
        else:
            self.commentary.setHtml(
                f"<p style='color:#c33'>{tr('verse.commentary_failed')}<br><small>{message}</small></p>"
            )


def _wrap_in_scroll(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    return scroll


# ---------- 메인 윈도우 ----------

# 열려 있는 창들을 붙잡아 둔다 (참조가 사라지면 GC 되므로). 새 창을 Ctrl+N 으로 연다.
_OPEN_WINDOWS: list = []


class MainWindow(QMainWindow):
    MAX_PANELS = 4  # 가로 패널(세로 구절 묶음) 최대 개수

    def __init__(self, storage: Storage, fetcher: CrossBibleFetcher, settings: QSettings):
        super().__init__()
        self.storage = storage
        self.fetcher = fetcher
        self.settings = settings
        self._thread: QThread | None = None
        self._worker: VersesWorker | None = None
        self._dl_thread: QThread | None = None
        self._dl_worker: DownloadWorker | None = None

        # 패널(세로 구절 묶음)들. 좌측 가로 배치의 원본. self._passages 는 이를
        # 읽기 순서(좌→우, 위→아래)로 펼친 평면 리스트(우측 패널 순서용).
        # 본문/오류/절목록은 위치가 아니라 Reference 로 키잉 → 순서를 바꿔도 재사용.
        self._panels: list[Panel] = []
        self._passages: list[Reference] = []
        self._verse_data: dict[tuple[Reference, str], list] = {}
        self._verse_errors: dict[tuple[Reference, str], str] = {}
        self._passage_verses: dict[Reference, list[int]] = {}

        self.setWindowTitle(tr("app.title"))
        self.resize(1700, 1000)

        self._build_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addLayout(self._build_selector())
        root.addLayout(self._build_multi_input())
        root.addLayout(self._build_translation_filter())

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._build_translations_column())
        self._side_scroll = self._build_side_column()
        self._splitter.addWidget(self._side_scroll)
        self._splitter.setSizes([900, 800])
        root.addWidget(self._splitter, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(tr("status.ready"))

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._on_lookup)
        QShortcut(QKeySequence("F9"), self, activated=self.side_toggle_btn.toggle)

        self._on_book_changed(0)

    # ---- 메뉴 ----

    def _build_menu_bar(self):
        bar = self.menuBar()

        settings_menu = bar.addMenu(tr("menu.settings"))

        theme_menu = settings_menu.addMenu(tr("menu.theme"))
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        current_theme = self.settings.value("theme", "System")
        for name in THEMES:
            action = QAction(name, self, checkable=True)
            action.setData(name)
            action.setChecked(name == current_theme)
            action.triggered.connect(lambda _checked=False, n=name: self._on_theme_chosen(n))
            self._theme_group.addAction(action)
            theme_menu.addAction(action)

        lang_menu = settings_menu.addMenu(tr("menu.language"))
        self._lang_group = QActionGroup(self)
        self._lang_group.setExclusive(True)
        for code in LANGUAGES:
            action = QAction(LANGUAGE_LABELS[code], self, checkable=True)
            action.setData(code)
            action.setChecked(code == _CURRENT_LANG)
            action.triggered.connect(lambda _checked=False, c=code: self._on_language_chosen(c))
            self._lang_group.addAction(action)
            lang_menu.addAction(action)

        tools_menu = bar.addMenu(tr("menu.tools"))
        new_win_action = QAction(tr("menu.new_window"), self)
        new_win_action.setShortcut(QKeySequence("Ctrl+N"))
        new_win_action.triggered.connect(self._on_new_window)
        tools_menu.addAction(new_win_action)
        tools_menu.addSeparator()

        dl_action = QAction(tr("menu.download_all"), self)
        dl_action.triggered.connect(self._on_download_all)
        tools_menu.addAction(dl_action)

        search_action = QAction(tr("menu.search"), self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self._on_open_search)
        tools_menu.addAction(search_action)
        self._search_dialog: SearchDialog | None = None

        dict_action = QAction(tr("menu.dictionary"), self)
        dict_action.triggered.connect(self._on_open_dictionary)
        tools_menu.addAction(dict_action)
        self._dict_dialog: DictionaryDialog | None = None

        tools_menu.addSeparator()
        cache_action = QAction(tr("menu.cache_info"), self)
        cache_action.triggered.connect(self._on_open_cache_info)
        tools_menu.addAction(cache_action)

        export_action = QAction(tr("menu.export_db"), self)
        export_action.triggered.connect(self._on_export_db)
        tools_menu.addAction(export_action)

        import_action = QAction(tr("menu.import_db"), self)
        import_action.triggered.connect(self._on_import_db)
        tools_menu.addAction(import_action)

        library_menu = bar.addMenu(tr("menu.library"))
        lib_save_action = QAction(tr("library.save"), self)
        lib_save_action.triggered.connect(self._on_library_save)
        library_menu.addAction(lib_save_action)
        lib_open_action = QAction(tr("library.open"), self)
        lib_open_action.triggered.connect(self._on_library_open)
        library_menu.addAction(lib_open_action)
        self._library_dialog: LibraryDialog | None = None

        help_menu = bar.addMenu(tr("menu.help"))
        feedback_action = QAction(tr("menu.feedback"), self)
        feedback_action.triggered.connect(self._on_open_feedback)
        help_menu.addAction(feedback_action)

        about_action = QAction(tr("menu.about"), self)
        about_action.triggered.connect(self._on_open_about)
        help_menu.addAction(about_action)

    def _on_theme_chosen(self, theme: str):
        self.settings.setValue("theme", theme)
        self.settings.sync()  # 다음 실행에서 확실히 읽히도록 즉시 디스크에 flush
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, theme)

    def _on_new_window(self):
        # 같은 storage/fetcher/settings 를 공유하는 새 창을 연다 (캐시·메모 공유).
        win = MainWindow(self.storage, self.fetcher, self.settings)
        win.show()
        _OPEN_WINDOWS.append(win)

    def _on_language_chosen(self, lang: str):
        if lang == _CURRENT_LANG:
            return
        self.settings.setValue("language", lang)
        self.settings.sync()
        QMessageBox.information(
            self,
            tr("language.restart_title"),
            tr("language.restart_body"),
        )

    def closeEvent(self, event):
        # 종료 직전에 한 번 더 flush — 일부 OS/빌드 환경에서 안전망
        try:
            self.settings.sync()
        except Exception:
            pass
        super().closeEvent(event)

    # ---- 셀렉터 ----

    def _build_selector(self) -> QHBoxLayout:
        row = QHBoxLayout()

        row.addWidget(QLabel(tr("selector.book")))
        self.book_box = QComboBox()
        self.book_box.addItems(book_names_ko())
        self.book_box.setEditable(True)
        self.book_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.book_box.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.book_box.activated.connect(self._on_book_changed)
        row.addWidget(self.book_box, 1)

        row.addWidget(QLabel(tr("selector.chapter")))
        self.chap_box = QSpinBox()
        self.chap_box.setRange(1, 150)
        self.chap_box.valueChanged.connect(self._on_chap_changed)
        row.addWidget(self.chap_box)

        row.addWidget(QLabel(tr("selector.verse")))
        self.verse_start = QSpinBox()
        self.verse_start.setRange(1, 200)
        self.verse_start.setValue(1)
        row.addWidget(self.verse_start)

        row.addWidget(QLabel(tr("selector.range_sep")))
        self.verse_end = QSpinBox()
        self.verse_end.setRange(1, 200)
        self.verse_end.setValue(1)
        row.addWidget(self.verse_end)

        self.whole_check = QCheckBox(tr("selector.whole"))
        self.whole_check.setToolTip(tr("selector.whole_tooltip"))
        self.whole_check.toggled.connect(self._on_whole_toggled)
        row.addWidget(self.whole_check)

        self.lookup_btn = QPushButton(tr("selector.lookup"))
        self.lookup_btn.clicked.connect(self._on_lookup)
        row.addWidget(self.lookup_btn)

        self.add_btn = QPushButton(tr("selector.add"))
        self.add_btn.setToolTip(tr("selector.add_tooltip"))
        self.add_btn.clicked.connect(self._on_add)
        row.addWidget(self.add_btn)

        self.new_panel_btn = QPushButton(tr("selector.new_panel"))
        self.new_panel_btn.setToolTip(tr("selector.new_panel_tooltip"))
        self.new_panel_btn.clicked.connect(self._on_new_panel)
        row.addWidget(self.new_panel_btn)

        self.refresh_btn = QPushButton(tr("selector.refresh"))
        self.refresh_btn.setToolTip(tr("selector.refresh_tooltip"))
        self.refresh_btn.clicked.connect(self._on_refresh)
        row.addWidget(self.refresh_btn)

        row.addStretch(1)

        self.side_toggle_btn = QPushButton(tr("selector.side_on"))
        self.side_toggle_btn.setCheckable(True)
        self.side_toggle_btn.setChecked(True)
        self.side_toggle_btn.setToolTip(tr("selector.side_tooltip"))
        self.side_toggle_btn.toggled.connect(self._on_side_toggled)
        row.addWidget(self.side_toggle_btn)
        return row

    def _build_multi_input(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.multi_edit = QLineEdit()
        self.multi_edit.setPlaceholderText(tr("multi.placeholder"))
        self.multi_edit.setToolTip(tr("multi.tooltip"))
        self.multi_edit.returnPressed.connect(self._on_multi_lookup)
        row.addWidget(self.multi_edit, 1)
        multi_lookup_btn = QPushButton(tr("multi.lookup"))
        multi_lookup_btn.clicked.connect(self._on_multi_lookup)
        row.addWidget(multi_lookup_btn)
        multi_add_btn = QPushButton(tr("multi.add"))
        multi_add_btn.clicked.connect(self._on_multi_add)
        row.addWidget(multi_add_btn)
        return row

    def _on_whole_toggled(self, checked: bool):
        self.verse_start.setEnabled(not checked)
        self.verse_end.setEnabled(not checked)

    def _build_translation_filter(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("filter.show_translations")))
        self.translation_checks: dict[str, QCheckBox] = {}
        for code in CrossBibleFetcher.TRANSLATIONS:
            cb = QCheckBox(CrossBibleFetcher.TRANSLATION_LABELS[code])
            cb.setChecked(True)
            cb.toggled.connect(lambda checked, c=code: self._on_translation_toggled(c, checked))
            self.translation_checks[code] = cb
            row.addWidget(cb)
        row.addStretch(1)
        return row

    def _build_translations_column(self) -> QWidget:
        # 구절 패널들을 좌→우로 나란히 (최대 4). 각 패널은 자체 세로 스크롤을 가진다.
        self._translations_container = QWidget()
        self._left_layout = QHBoxLayout(self._translations_container)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(6)
        return self._translations_container

    def _build_side_column(self) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(4)

        # 절 점프 네비게이션 — 가로 스크롤로 감싸 한 줄을 넘쳐도(전체 장 등) 안전.
        self._nav_bar = QWidget()
        self._nav_layout = QHBoxLayout(self._nav_bar)
        self._nav_layout.setContentsMargins(4, 4, 4, 4)
        self._nav_layout.setSpacing(4)
        self._nav_layout.addStretch(1)
        nav_scroll = QScrollArea()
        nav_scroll.setWidget(self._nav_bar)
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFixedHeight(44)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        wrapper_layout.addWidget(nav_scroll)

        self._side_container = QWidget()
        self._side_layout = QVBoxLayout(self._side_container)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.setSpacing(0)
        self._side_layout.addStretch(1)
        self.verse_blocks: dict[tuple[Reference, int], VerseBlock] = {}

        self._side_scroll_inner = _wrap_in_scroll(self._side_container)
        wrapper_layout.addWidget(self._side_scroll_inner, 1)
        return wrapper

    # ---- passage 보기 (다중 구절 + 번갈아보기 + 지연 로딩) ----

    @staticmethod
    def _esc(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _clear_left(self):
        while self._left_layout.count():
            item = self._left_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _apply_panels(self, panels: list[Panel], force: bool = False):
        """패널 구조를 정규화해 적용하고, 필요한 것만 조회한다.

        본문/오류/절목록은 Reference 로 키잉되어 있어, 순서를 바꾸거나 블록을 옮겨도
        이미 받은 데이터는 그대로 재사용한다 → 재정렬/삭제는 재조회 없이 즉시 반영.
        새로 생긴 구절(또는 force) 만 백그라운드로 조회한다.

        - 전역 중복 제거(같은 구절은 첫 등장만) · 빈 패널 유지 · 패널 최대 MAX_PANELS 개.
        """
        seen: set[Reference] = set()
        norm: list[Panel] = []
        for p in panels:
            blocks: list[Reference] = []
            for ref in p.blocks:
                if ref not in seen:
                    seen.add(ref)
                    blocks.append(ref)
            norm.append(Panel(blocks, p.interleave))
        if len(norm) > self.MAX_PANELS:
            norm = norm[:self.MAX_PANELS]
            self.statusBar().showMessage(tr("passage.max_reached", n=self.MAX_PANELS), 4000)
        self._panels = norm
        flat = [ref for p in norm for ref in p.blocks]
        self._passages = flat

        # 화면에서 사라진 구절의 데이터는 정리 (메모리/혼선 방지)
        present = set(flat)
        self._verse_data = {k: v for k, v in self._verse_data.items() if k[0] in present}
        self._verse_errors = {k: v for k, v in self._verse_errors.items() if k[0] in present}
        self._passage_verses = {r: v for r, v in self._passage_verses.items() if r in present}
        # 범위 구절의 절 번호는 즉시 안다 (우측 블록 바로 빌드). 장 전체는 본문 도착 후.
        for ref in flat:
            if not ref.whole_chapter and ref not in self._passage_verses:
                self._passage_verses[ref] = ref.verse_numbers()

        # 캐시에 있는 본문은 UI 스레드에서 즉시(동기 SQL) 채운다. 그래야 캐시된 번역본이
        # '캐시 안 된 번역본의 네트워크 대기' 뒤에 줄 서지 않고 바로 뜬다.
        # 진짜 없는 (구절, 번역본) 만 백그라운드 네트워크 조회 대상(targets)으로 남긴다.
        enabled = self._enabled_translations()
        targets: list[tuple[Reference, str]] = []
        for ref in flat:
            for t in enabled:
                if (ref, t) in self._verse_data:
                    continue
                if not force:
                    cached = self.fetcher.get_cached(t, ref)
                    if cached is not None:
                        self._verse_data[(ref, t)] = cached
                        if ref.whole_chapter and ref not in self._passage_verses:
                            self._passage_verses[ref] = [n for n, _ in cached]
                        continue
                targets.append((ref, t))

        # 화면을 그린다 (캐시된 본문은 이미 채워져 바로 보임). 우측 블록은 재사용.
        self._rebuild_side()
        self._render_left()

        if flat:
            head = flat[0].header_ko + (f" 외 {len(flat) - 1}" if len(flat) > 1 else "")
            self.setWindowTitle(tr("app.title_with_ref", ref=head))
        else:
            self.setWindowTitle(tr("app.title"))

        self._fetch(targets, force)

    def _fetch(self, targets: list[tuple[Reference, str]], force: bool = False):
        # 진행 중 워커는 기다리지 않고 분리한다. blockSignals 만으론 '이미 큐에 쌓인'
        # 신호가 그대로 전달돼 옛 결과가 새 화면을 오염시키므로 연결 자체를 끊는다.
        if self._thread is not None:
            try:
                if self._worker is not None:
                    self._worker.cancel()
                    self._worker.disconnect()
                    self._worker.blockSignals(True)
                self._thread.quit()
            except Exception:
                pass
            self._worker = None
            self._thread = None

        if not targets:
            if self._passages:
                self.statusBar().showMessage(tr("status.done"), 2000)
            return

        if self._passages:
            head = self._passages[0].header_ko
            self.statusBar().showMessage(
                tr("status.looking_up", ref_ko=head, ref_en=self._passages[0].header_en)
            )

        self._thread = QThread(self)
        self._worker = VersesWorker(self.fetcher, targets, force=force)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.verses_ready.connect(self._on_verses_ready)
        self._worker.error.connect(self._on_verses_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._on_finished)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    # ---- 좌측(본문) 렌더링 ----

    def _passage_verse_set(self, ref: Reference, enabled: list[str]) -> list[int]:
        nums: set[int] = set()
        for t in enabled:
            data = self._verse_data.get((ref, t))
            if data:
                nums.update(n for n, _ in data)
        if not nums and not ref.whole_chapter:
            nums.update(ref.verse_numbers())
        return sorted(nums)

    def _render_left(self):
        self._clear_left()
        if not self._panels:
            return
        enabled = self._enabled_translations()
        self._translations_container.setUpdatesEnabled(False)
        try:
            for panel_idx, panel in enumerate(self._panels):
                self._left_layout.addWidget(
                    self._render_panel(panel_idx, panel, enabled), 1
                )
        finally:
            self._translations_container.setUpdatesEnabled(True)

    def _render_panel(self, panel_idx: int, panel: Panel,
                      enabled: list[str]) -> QWidget:
        col = QWidget()
        cv = QVBoxLayout(col)
        cv.setContentsMargins(4, 6, 4, 4)
        cv.setSpacing(3)

        # 패널 상단 바: (번갈아보기 토글) + 패널 삭제 🗑
        top = QHBoxLayout()
        top.setSpacing(4)
        if panel.blocks:
            il = QCheckBox(tr("filter.interleave"))
            il.setChecked(panel.interleave)
            il.setToolTip(tr("filter.interleave_tooltip"))
            il.toggled.connect(lambda ch, p=panel_idx: self._set_panel_interleave(p, ch))
            top.addWidget(il)
        else:
            top.addWidget(self._muted(tr("panel.empty")), 1)
        top.addStretch(1)
        delp = QPushButton("🗑")
        delp.setFixedSize(24, 20)
        delp.setToolTip(tr("panel.remove_tooltip"))
        delp.clicked.connect(lambda _c=False, p=panel_idx: self._remove_panel(p))
        top.addWidget(delp)
        cv.addLayout(top)

        if not panel.blocks:
            cv.addStretch(1)
            return col

        inner = QWidget()
        iv = QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(4)
        for block_idx, ref in enumerate(panel.blocks):
            iv.addWidget(self._render_block(panel_idx, block_idx, ref, enabled, panel.interleave))
            if block_idx < len(panel.blocks) - 1:
                iv.addWidget(_hline())
        iv.addStretch(1)
        cv.addWidget(_wrap_in_scroll(inner), 1)
        return col

    def _render_block(self, panel_idx: int, block_idx: int,
                      ref: Reference, enabled: list[str], interleave: bool) -> QWidget:
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(2, 2, 2, 2)
        bl.setSpacing(2)

        bl.addWidget(_section_label(ref.header_ko, level=2))
        sub = QLabel(ref.header_en)
        sub.setStyleSheet("color:#888; font-size:9pt;")
        bl.addWidget(sub)

        # 버튼: ◀ ▶ (패널 간 이동) · ↑ ↓ (패널 안 순서) · ✂ split · ✕ 제거
        n_panels = len(self._panels)
        n_blocks = len(self._panels[panel_idx].blocks)
        controls = [
            ("◀", tr("block.move_left"),
             lambda _c=False, p=panel_idx, b=block_idx: self._move_block_panel(p, b, -1), panel_idx > 0),
            ("▶", tr("block.move_right"),
             lambda _c=False, p=panel_idx, b=block_idx: self._move_block_panel(p, b, +1), panel_idx < n_panels - 1),
            ("↑", tr("block.move_up"),
             lambda _c=False, p=panel_idx, b=block_idx: self._move_block(p, b, -1), block_idx > 0),
            ("↓", tr("block.move_down"),
             lambda _c=False, p=panel_idx, b=block_idx: self._move_block(p, b, +1), block_idx < n_blocks - 1),
            ("✂", tr("passage.split_tooltip"),
             lambda _c=False, p=panel_idx, b=block_idx: self._split_block(p, b), True),
            ("✕", tr("passage.remove_tooltip"),
             lambda _c=False, p=panel_idx, b=block_idx: self._remove_block(p, b), True),
        ]
        brow = QHBoxLayout()
        brow.setSpacing(1)
        brow.addStretch(1)
        for text, tip, slot, on in controls:
            b = QPushButton(text)
            b.setFixedSize(22, 20)
            b.setToolTip(tip)
            b.setEnabled(on)
            b.clicked.connect(slot)
            brow.addWidget(b)
        bl.addLayout(brow)

        if interleave:
            verses = self._passage_verse_set(ref, enabled)
            if not verses:
                bl.addWidget(self._muted(tr("verse.loading")))
            for n in verses:
                bl.addWidget(self._interleave_widget(ref, n, enabled))
        else:
            for t in enabled:
                bl.addWidget(self._translation_subblock(ref, t))
        return box

    @staticmethod
    def _muted(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#888;")
        lbl.setWordWrap(True)
        return lbl

    def _translation_subblock(self, ref: Reference, t: str) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 2, 0, 4)
        v.setSpacing(2)
        name = QLabel(CrossBibleFetcher.TRANSLATION_LABELS.get(t, t))
        nf = name.font()
        nf.setBold(True)
        name.setFont(nf)
        v.addWidget(name)

        body = QLabel()
        body.setWordWrap(True)
        body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        if t in ("GAE", "KLB"):
            bf = body.font()
            bf.setPointSize(bf.pointSize() + 1)
            body.setFont(bf)

        if (ref, t) in self._verse_errors:
            body.setText(
                f"<span style='color:#c33'>{tr('verse.fetch_failed')}<br>"
                f"<small>{self._esc(self._verse_errors[(ref, t)])}</small></span>"
            )
        else:
            data = self._verse_data.get((ref, t))
            if data is None:
                body.setText(f"<span style='color:#888'>{tr('verse.loading')}</span>")
            else:
                parts = [f"<b>{n}</b>&nbsp;&nbsp;{self._esc(txt)}" for n, txt in data]
                body.setText("<br>".join(parts))
        v.addWidget(body)
        return box

    def _interleave_widget(self, ref: Reference, n: int, enabled: list[str]) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 4, 0, 4)
        v.setSpacing(1)
        v.addWidget(QLabel(f"<b>{n}</b>"))
        for t in enabled:
            label = CrossBibleFetcher.TRANSLATION_LABELS.get(t, t)
            line = QLabel(
                f"<span style='color:#999'>{label}</span>&nbsp;&nbsp;{self._verse_text(ref, t, n)}"
            )
            line.setWordWrap(True)
            line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            line.setContentsMargins(14, 0, 0, 0)
            if t in ("GAE", "KLB"):
                lf = line.font()
                lf.setPointSize(lf.pointSize() + 1)
                line.setFont(lf)
            v.addWidget(line)
        return box

    def _verse_text(self, ref: Reference, t: str, n: int) -> str:
        if (ref, t) in self._verse_errors:
            return "<span style='color:#c33'>—</span>"
        data = self._verse_data.get((ref, t))
        if data is None:
            return "<span style='color:#888'>…</span>"
        for vn, txt in data:
            if vn == n:
                return self._esc(txt)
        return "<span style='color:#bbb'>—</span>"

    # ---- 우측(원어/주석/메모) 빌드 ----

    def _rebuild_side(self):
        """우측 패널을 읽기 순서(왼쪽 패널부터 위→아래)로 재구성한다.

        VerseBlock 은 (구절, 절) 키로 '재사용'한다 — 순서만 바뀌면 위젯을 새로 만들지
        않고 떼었다 다시 끼우므로 빠르고, 펼침·원어/주석·메모 상태가 유지된다.
        """
        old = self.verse_blocks  # (ref, verse) -> VerseBlock (재사용 후보)
        # 레이아웃에서 모두 떼어낸다. VerseBlock 은 삭제하지 않고 보관(재사용), 나머지는 삭제.
        while self._side_layout.count() > 1:
            w = self._side_layout.takeAt(0).widget()
            if w is None:
                continue
            w.setParent(None)
            if not isinstance(w, VerseBlock):
                w.deleteLater()
        while self._nav_layout.count() > 1:
            w = self._nav_layout.takeAt(0).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        self.verse_blocks = {}
        for ref in self._passages:
            verses = self._passage_verses.get(ref)
            if verses:
                self._append_side_passage(ref, verses, old)

        # 더 이상 화면에 없는 옛 블록은 정리
        for key, blk in old.items():
            if key not in self.verse_blocks:
                blk.setParent(None)
                blk.deleteLater()

    def _append_side_passage(self, ref: Reference, verses: list[int], old: dict):
        insert = self._side_layout.count() - 1
        header = _section_label(f"{ref.header_ko}  ({ref.header_en})", level=1)
        self._side_layout.insertWidget(insert, header)
        insert += 1

        nav_insert = self._nav_layout.count() - 1
        nav_label = QLabel(f"{ref.book_ko}{ref.chapter}:")
        nav_label.setStyleSheet("color:#888; padding:0 2px;")
        self._nav_layout.insertWidget(nav_insert, nav_label)
        nav_insert += 1

        for n in verses:
            key = (ref, n)
            block = old.pop(key, None)  # 있으면 재사용 (상태 유지)
            if block is None:
                block = VerseBlock(ref, n, self.storage, self.fetcher)
            self.verse_blocks[key] = block
            self._side_layout.insertWidget(insert, block)
            insert += 1

            btn = QPushButton(str(n))
            btn.setFixedHeight(24)
            btn.setStyleSheet("padding: 0 8px;")
            btn.setToolTip(f"{ref.book_ko} {ref.chapter}:{n}")
            btn.clicked.connect(lambda _checked=False, r=ref, num=n: self._scroll_to(r, num))
            self._nav_layout.insertWidget(nav_insert, btn)
            nav_insert += 1

    def _scroll_to(self, ref: Reference, verse: int):
        block = self.verse_blocks.get((ref, verse))
        if block is None:
            return
        block.expand()
        self._side_scroll_inner.ensureWidgetVisible(block, 0, 8)

    # ---- 선택 처리 ----

    def _on_book_changed(self, idx: int):
        ko = self.book_box.currentText()
        info = lookup_by_ko(ko)
        if not info:
            return
        _, _, chapters = info
        self.chap_box.setRange(1, chapters)
        self.chap_box.setValue(1)

    def _on_chap_changed(self, _value: int):
        self.verse_start.setValue(1)
        self.verse_end.setValue(1)

    def _current_ref(self) -> Reference | None:
        ko = self.book_box.currentText()
        info = lookup_by_ko(ko)
        if not info:
            return None
        en, ko_canonical, _ = info
        if self.whole_check.isChecked():
            return Reference(en, ko_canonical, self.chap_box.value(), 1, 1, whole_chapter=True)
        vs = self.verse_start.value()
        ve = max(self.verse_end.value(), vs)
        return Reference(en, ko_canonical, self.chap_box.value(), vs, ve)

    def _copy_panels(self) -> list[Panel]:
        return [Panel(list(p.blocks), p.interleave) for p in self._panels]

    def _on_lookup(self):
        ref = self._current_ref()
        if ref is None:
            return
        self._apply_panels([Panel([ref])])  # 교체: 한 패널 한 구절

    def _on_add(self):
        # ＋추가: 맨 왼쪽 패널에 쌓는다 (패널이 없으면 하나 만든다).
        ref = self._current_ref()
        if ref is None:
            return
        panels = self._copy_panels()
        if panels:
            panels[0].blocks.append(ref)
        else:
            panels = [Panel([ref])]
        self._apply_panels(panels)

    def _on_new_panel(self):
        if len(self._panels) >= self.MAX_PANELS:
            QMessageBox.information(
                self, tr("passage.max_title"), tr("passage.max_body", n=self.MAX_PANELS)
            )
            return
        self._apply_panels(self._copy_panels() + [Panel([])])

    def _on_refresh(self):
        # 현재 화면의 구절을 캐시 무시하고 다시 가져온다 (오래되거나 누락된 본문 갱신).
        if self._panels:
            self._apply_panels(self._panels, force=True)

    # ---- 블록/패널 조작 ----

    def _remove_block(self, panel_idx: int, block_idx: int):
        panels = self._copy_panels()
        if 0 <= panel_idx < len(panels) and 0 <= block_idx < len(panels[panel_idx].blocks):
            del panels[panel_idx].blocks[block_idx]
            self._apply_panels(panels)

    def _remove_panel(self, panel_idx: int):
        panels = self._copy_panels()
        if 0 <= panel_idx < len(panels):
            del panels[panel_idx]
            self._apply_panels(panels)

    def _move_block(self, panel_idx: int, block_idx: int, delta: int):
        # 패널 안에서 위/아래 순서 이동
        panels = self._copy_panels()
        blocks = panels[panel_idx].blocks
        j = block_idx + delta
        if 0 <= block_idx < len(blocks) and 0 <= j < len(blocks):
            blocks[block_idx], blocks[j] = blocks[j], blocks[block_idx]
            self._apply_panels(panels)

    def _move_block_panel(self, panel_idx: int, block_idx: int, delta: int):
        # 블록을 왼쪽/오른쪽 패널로 옮긴다 (그 패널 맨 아래에 쌓임)
        q = panel_idx + delta
        if not (0 <= panel_idx < len(self._panels) and 0 <= q < len(self._panels)):
            return
        panels = self._copy_panels()
        if not (0 <= block_idx < len(panels[panel_idx].blocks)):
            return
        ref = panels[panel_idx].blocks.pop(block_idx)
        panels[q].blocks.append(ref)
        self._apply_panels(panels)

    def _split_block(self, panel_idx: int, block_idx: int):
        """블록의 절 범위를 위/아래 둘로 나눠 같은 패널에 쌓는다 ([lo..k], [k+1..hi])."""
        if not (0 <= panel_idx < len(self._panels)):
            return
        if not (0 <= block_idx < len(self._panels[panel_idx].blocks)):
            return
        ref = self._panels[panel_idx].blocks[block_idx]
        if ref.whole_chapter:
            verses = self._passage_verses.get(ref)
            if not verses:
                QMessageBox.information(self, tr("split.title"), tr("split.need_text"))
                return
            lo, hi = verses[0], verses[-1]
        else:
            lo, hi = ref.verse_start, ref.verse_end
        if hi - lo < 1:
            QMessageBox.information(self, tr("split.title"), tr("split.too_small"))
            return
        k, ok = QInputDialog.getInt(
            self, tr("split.title"), tr("split.label", lo=lo, hi=hi),
            (lo + hi) // 2, lo, hi - 1,
        )
        if not ok:
            return
        a = Reference(ref.book_en, ref.book_ko, ref.chapter, lo, k)
        b = Reference(ref.book_en, ref.book_ko, ref.chapter, k + 1, hi)

        # 반쪽 두 구절의 본문은 부모가 이미 받은 데이터를 잘라 채운다 → 재조회 없이 즉시.
        for (rk, t), pdata in list(self._verse_data.items()):
            if rk == ref:
                self._verse_data[(a, t)] = [(n, x) for n, x in pdata if lo <= n <= k]
                self._verse_data[(b, t)] = [(n, x) for n, x in pdata if k + 1 <= n <= hi]
        for (rk, t), perr in list(self._verse_errors.items()):
            if rk == ref:
                self._verse_errors[(a, t)] = perr
                self._verse_errors[(b, t)] = perr

        panels = self._copy_panels()
        panels[panel_idx].blocks[block_idx:block_idx + 1] = [a, b]
        self._apply_panels(panels)

    # ---- 라이브러리 ----

    def _on_library_save(self):
        if not self._passages:
            QMessageBox.information(self, tr("library.save_title"), tr("library.save_empty"))
            return
        name, ok = QInputDialog.getText(self, tr("library.save_title"), tr("library.save_label"))
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        # 패널 구조(위치·묶음·번갈아보기)까지 저장.
        self.storage.save_collection(name, serialize_panels(self._panels))
        if self._library_dialog is not None:
            self._library_dialog.refresh()
        self.statusBar().showMessage(
            tr("library.saved", name=name, count=len(self._passages)), 4000
        )

    def _on_library_open(self):
        if self._library_dialog is None:
            self._library_dialog = LibraryDialog(self.storage, self)
            # 불러오기: 저장된 패널 구조 그대로 교체. 추가: 그 패널들을 뒤에 붙임.
            self._library_dialog.load_replace.connect(self._apply_panels)
            self._library_dialog.load_add.connect(
                lambda panels: self._apply_panels(self._copy_panels() + panels)
            )
        self._library_dialog.refresh()
        self._library_dialog.show()
        self._library_dialog.raise_()
        self._library_dialog.activateWindow()

    def _parse_multi(self) -> list[Reference] | None:
        text = self.multi_edit.text().strip()
        if not text:
            QMessageBox.information(self, tr("parse.none_title"), tr("parse.none_body"))
            return None
        refs, errors = parse_references(text)
        if errors:
            QMessageBox.warning(
                self, tr("parse.problem_title"),
                tr("parse.problem_unparsed", tokens=", ".join(errors)),
            )
        return refs

    def _add_refs_to_first_panel(self, refs: list[Reference]):
        panels = self._copy_panels()
        if not panels:
            panels = [Panel([])]
        panels[0].blocks.extend(refs)
        self._apply_panels(panels)

    def _on_multi_lookup(self):
        refs = self._parse_multi()
        if not refs:
            return
        self._apply_panels([Panel([r]) for r in refs])  # 교체: 각 구절을 패널 하나씩

    def _on_multi_add(self):
        refs = self._parse_multi()
        if not refs:
            return
        self._add_refs_to_first_panel(refs)  # 맨 왼쪽 패널에 쌓기

    def _on_verses_ready(self, ref: Reference, translation: str, verses: list):
        self._verse_data[(ref, translation)] = verses
        self._verse_errors.pop((ref, translation), None)
        # 장 전체는 본문이 도착해야 절 수를 안다 — 첫 도착 시 우측 블록을 (재사용하며) 빌드.
        if ref.whole_chapter and ref not in self._passage_verses:
            nums = [n for n, _ in verses]
            if nums:
                self._passage_verses[ref] = nums
                self._rebuild_side()
        self._render_left()

    def _on_verses_error(self, ref: Reference, translation: str, message: str):
        self._verse_errors[(ref, translation)] = message
        self._render_left()

    def _on_finished(self):
        self.statusBar().showMessage(tr("status.done"), 3000)
        self._worker = None
        self._thread = None

    def _on_side_toggled(self, checked: bool):
        self._side_scroll.setVisible(checked)
        if checked:
            self._splitter.setSizes([900, 800])
        self.side_toggle_btn.setText(
            tr("selector.side_on") if checked else tr("selector.side_off")
        )

    def _set_panel_interleave(self, panel_idx: int, checked: bool):
        # 패널별 번갈아보기 — 좌측만 다시 그림(재조회 없음).
        if 0 <= panel_idx < len(self._panels):
            self._panels[panel_idx].interleave = checked
            self._render_left()

    def _on_translation_toggled(self, code: str, checked: bool):
        # 최소 한 개는 켜둔다
        if not any(cb.isChecked() for cb in self.translation_checks.values()):
            cb = self.translation_checks[code]
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            self.statusBar().showMessage(tr("status.min_one_translation"), 3000)
            return
        # 켠 번역본의 본문이 아직 없으면 그 번역만 조회. 끄면 좌측만 다시 그림.
        missing = checked and any(
            (ref, code) not in self._verse_data for ref in self._passages
        )
        if missing:
            self._apply_panels(self._panels)
        else:
            self._render_left()

    def _enabled_translations(self) -> list[str]:
        return [
            code for code in CrossBibleFetcher.TRANSLATIONS
            if self.translation_checks[code].isChecked()
        ]

    # ---- 도움말 ----

    def _on_open_feedback(self):
        QDesktopServices.openUrl(QUrl("https://github.com/yeonju7kim/CrossBible/issues"))

    def _on_open_about(self):
        version_path = _resource_path("version.txt")
        try:
            version = version_path.read_text(encoding="utf-8").strip()
        except OSError:
            version = ""
        if not version:
            version = tr("about.unknown_version")
        QMessageBox.about(
            self,
            tr("about.title"),
            tr("about.body", version=version),
        )

    # ---- DB 백업 / 복원 ----

    def _on_export_db(self):
        import shutil
        src = Path(self.storage.path)
        # commit 후 디스크에 반영
        try:
            self.storage.conn.commit()
        except Exception:
            pass
        default_name = f"crossbible-cache-{src.stat().st_mtime:.0f}.db"
        default_dir = str(Path.home() / default_name)
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            tr("db.export.title"),
            default_dir,
            tr("db.export.filter"),
        )
        if not path_str:
            return
        try:
            shutil.copy2(src, path_str)
            QMessageBox.information(
                self,
                tr("db.export.success_title"),
                tr("db.export.success_body", path=path_str),
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                tr("db.export.error_title"),
                tr("db.export.error_body", message=str(e)),
            )

    def _on_import_db(self):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("db.import.title"),
            str(Path.home()),
            tr("db.import.filter"),
        )
        if not path_str:
            return
        confirm = QMessageBox.question(
            self,
            tr("db.import.confirm_title"),
            tr("db.import.confirm_body"),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            result = self.storage.import_from(Path(path_str))
            QMessageBox.information(
                self,
                tr("db.import.success_title"),
                tr(
                    "db.import.success_body",
                    verses=result["verses_added"],
                    blobs=result["blobs_added"],
                ),
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                tr("db.import.error_title"),
                tr("db.import.error_body", message=str(e)),
            )

    # ---- 캐시 정보 ----

    def _on_open_cache_info(self):
        stats = self.storage.stats()
        path = stats["path"]
        size_mb = stats["size_bytes"] / (1024 * 1024)

        verses_map = stats["verses_by_translation"]
        if verses_map:
            summary = ", ".join(
                f"{CrossBibleFetcher.TRANSLATION_LABELS.get(code, code)} {n:,}"
                for code, n in sorted(verses_map.items())
            )
            verses_line = tr("cache.verses_line", summary=summary, total=f"{sum(verses_map.values()):,}")
        else:
            verses_line = tr("cache.verses_none")

        body = (
            tr("cache.intro")
            + "\n\n"
            + tr("cache.path_label") + ": " + path + "\n"
            + tr("cache.size_label") + f": {size_mb:.2f} MB\n\n"
            + tr("cache.contents_label") + ":\n"
            + "  • " + verses_line + "\n"
            + "  • " + tr("cache.interlinear_line", n=f"{stats['interlinear']:,}") + "\n"
            + "  • " + tr("cache.commentary_line", n=f"{stats['commentary']:,}") + "\n"
            + "  • " + tr("cache.notes_line", n=f"{stats['notes']:,}")
        )

        mbox = QMessageBox(self)
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setWindowTitle(tr("cache.title"))
        mbox.setText(body)
        open_btn = mbox.addButton(tr("cache.open_folder"), QMessageBox.ButtonRole.ActionRole)
        mbox.addButton(tr("cache.close"), QMessageBox.ButtonRole.RejectRole)
        mbox.exec()

        if mbox.clickedButton() is open_btn:
            folder = Path(path).parent
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # ---- 검색 ----

    def _on_open_search(self):
        if self._search_dialog is None:
            self._search_dialog = SearchDialog(
                self.storage,
                default_translations=self._enabled_translations(),
                parent=self,
            )
            self._search_dialog.verse_selected.connect(self._on_search_jump)
        self._search_dialog.show()
        self._search_dialog.raise_()
        self._search_dialog.activateWindow()
        self._search_dialog.input_edit.setFocus()

    def _on_search_jump(self, book_en: str, chapter: int, verse: int):
        # 검색 결과 더블클릭 → 화면을 비우지 않고 '맨 왼쪽 패널'에 그 절을 추가.
        # 검색 다이얼로그는 모드리스라 그대로 열려 있어 계속 추가할 수 있다.
        from bible_books import BOOKS
        ko = next((k for en, k, _, _, _ in BOOKS if en == book_en), None)
        if ko is None:
            return
        self._add_refs_to_first_panel([Reference(book_en, ko, chapter, verse, verse)])

    # ---- 사전 ----

    def _on_open_dictionary(self):
        # 모드리스로 한 번만 열어 재사용
        if self._dict_dialog is None:
            self._dict_dialog = DictionaryDialog(self)
        self._dict_dialog.show()
        self._dict_dialog.raise_()
        self._dict_dialog.activateWindow()
        self._dict_dialog.input_edit.setFocus()

    # ---- 전체 다운로드 ----

    def _on_download_all(self):
        if self._dl_thread is not None:
            QMessageBox.information(
                self, tr("download.title"), tr("download.in_progress")
            )
            return

        dialog = DownloadSelectionDialog(
            default_translations=self._enabled_translations(), parent=self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        translations = dialog.selected_translations()
        books = dialog.selected_books()
        if not translations or not books:
            QMessageBox.information(
                self, tr("download.title"), tr("download.no_selection")
            )
            return

        from bible_books import BOOKS

        chapters_sum = sum(
            chapters for en, _, _, _, chapters in BOOKS if en in set(books)
        )
        total = chapters_sum * len(translations)

        self._dl_dialog = QProgressDialog(
            tr("download.preparing"), tr("download.cancel"), 0, total, self
        )
        self._dl_dialog.setWindowTitle(tr("download.title"))
        self._dl_dialog.setMinimumDuration(0)
        self._dl_dialog.setAutoClose(False)
        self._dl_dialog.setAutoReset(False)
        self._dl_dialog.setValue(0)

        self._dl_thread = QThread(self)
        self._dl_worker = DownloadWorker(self.fetcher, translations, books)
        self._dl_worker.moveToThread(self._dl_thread)
        self._dl_thread.started.connect(self._dl_worker.run)

        self._dl_worker.progress.connect(self._on_dl_progress)
        self._dl_worker.finished.connect(self._on_dl_finished)
        self._dl_worker.finished.connect(self._dl_thread.quit)
        self._dl_thread.finished.connect(self._dl_worker.deleteLater)
        self._dl_thread.finished.connect(self._dl_thread.deleteLater)
        self._dl_dialog.canceled.connect(self._on_dl_cancel_clicked)

        self._dl_thread.start()
        self._dl_dialog.show()

    def _on_dl_cancel_clicked(self):
        # 사용자가 취소 누르면: 워커에 취소 신호 보내고, 다이얼로그는 곧바로 숨김.
        # 워커는 다음 0.1초 안에 throttle 루프에서 빠져나와 마무리한다.
        if self._dl_worker is not None:
            self._dl_worker.cancel()
        if self._dl_dialog is not None:
            self._dl_dialog.hide()

    def _on_dl_progress(self, done: int, total: int, label: str):
        if hasattr(self, "_dl_dialog") and self._dl_dialog is not None:
            self._dl_dialog.setMaximum(total)
            self._dl_dialog.setValue(done)
            self._dl_dialog.setLabelText(label)

    def _on_dl_finished(self, done: int, total: int, failures: list):
        if hasattr(self, "_dl_dialog") and self._dl_dialog is not None:
            self._dl_dialog.close()
            self._dl_dialog = None
        self._dl_worker = None
        self._dl_thread = None

        if done < total and len(failures) == 0:
            QMessageBox.information(
                self,
                tr("download.canceled_title"),
                tr("download.canceled_body", done=done, total=total),
            )
            return

        mbox = QMessageBox(self)
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setWindowTitle(tr("download.done_title"))
        mbox.setText(tr("download.done_body", done=done, total=total, failures=len(failures)))

        if failures:
            from bible_books import BOOKS
            en_to_ko = {en: ko for en, ko, _, _, _ in BOOKS}
            lines = []
            for translation, book_en, chapter, msg in failures:
                label = CrossBibleFetcher.TRANSLATION_LABELS.get(translation, translation)
                ko = en_to_ko.get(book_en, book_en)
                lines.append(f"[{label}] {ko} {chapter}장 — {msg}")
            mbox.setDetailedText("\n".join(lines))

        mbox.exec()


def _resource_path(rel: str) -> Path:
    import sys

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel


def run():
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("CrossBible")
    app.setOrganizationName("CrossBible")

    settings = QSettings("CrossBible", "CrossBible")
    saved_lang = settings.value("language", "ko")
    set_language(saved_lang if saved_lang in LANGUAGES else "ko")

    saved_theme = settings.value("theme", "System")
    apply_theme(app, saved_theme if saved_theme in THEMES else "System")

    icon_path = _resource_path("assets/icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    base = Path.home() / ".crossbible"
    storage = Storage(base / "data.db")
    fetcher = CrossBibleFetcher(storage)

    win = MainWindow(storage, fetcher, settings)
    win.show()
    _OPEN_WINDOWS.append(win)
    sys.exit(app.exec())
