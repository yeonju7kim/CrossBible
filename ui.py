"""PyQt6 메인 윈도우 — 메뉴바, i18n, 테마, 오프라인 다운로드."""
from __future__ import annotations

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
    QFrame,
    QHBoxLayout,
    QHeaderView,
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
        "status.extras_progress": "원어/주석 {done}/{total} 처리 중…",
        "status.min_one_translation": "번역본을 최소 하나는 켜두세요.",
        "selector.book": "책",
        "selector.chapter": "장",
        "selector.verse": "절",
        "selector.range_sep": "~",
        "selector.lookup": "조회 (Ctrl+Enter)",
        "selector.side_on": "원어/주석/메모 패널",
        "selector.side_off": "원어/주석/메모 패널 (꺼짐)",
        "selector.side_tooltip": "F9: 오른쪽 패널 켜기/끄기",
        "filter.show_translations": "표시할 번역:",
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
        "lookup.range_too_big_title": "범위 큼",
        "lookup.range_too_big_body": "한 번에 20절 이하로 조회해 주세요.",
        "menu.settings": "설정",
        "menu.tools": "도구",
        "menu.theme": "테마",
        "menu.language": "언어",
        "menu.download_all": "전체 다운로드…",
        "menu.search": "검색…",
        "search.title": "본문 검색 (캐시 안)",
        "search.placeholder": "키워드 (한/영, 부분 일치)",
        "search.go": "검색",
        "search.translations_label": "번역본",
        "search.col_ref": "참조",
        "search.col_translation": "번역",
        "search.col_preview": "미리보기",
        "search.results_count": "{n}건",
        "search.no_results": "결과 없음",
        "search.too_many": "{n}건 (처음 {limit}건만 표시)",
        "search.empty_cache": "캐시가 비어 있습니다. 도구 → 성경 다운로드… 로 본문을 먼저 받으세요.",
        "search.jump_hint": "두 번 클릭하면 그 절로 이동합니다.",
        "menu.help": "도움말",
        "menu.feedback": "건의사항 · 이슈 보내기…",
        "menu.cache_info": "캐시 정보…",
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
        "status.extras_progress": "Original / commentary {done}/{total}…",
        "status.min_one_translation": "Keep at least one translation enabled.",
        "selector.book": "Book",
        "selector.chapter": "Chap",
        "selector.verse": "Verse",
        "selector.range_sep": "~",
        "selector.lookup": "Look up (Ctrl+Enter)",
        "selector.side_on": "Original / Commentary / Notes",
        "selector.side_off": "Original / Commentary / Notes (off)",
        "selector.side_tooltip": "F9: toggle the right panel",
        "filter.show_translations": "Show translations:",
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
        "lookup.range_too_big_title": "Range too big",
        "lookup.range_too_big_body": "Please look up at most 20 verses at a time.",
        "menu.settings": "Settings",
        "menu.tools": "Tools",
        "menu.theme": "Theme",
        "menu.language": "Language",
        "menu.download_all": "Download all chapters…",
        "menu.search": "Search…",
        "search.title": "Search Bible text (cached)",
        "search.placeholder": "Keyword (Korean or English, substring)",
        "search.go": "Search",
        "search.translations_label": "Translations",
        "search.col_ref": "Reference",
        "search.col_translation": "Translation",
        "search.col_preview": "Preview",
        "search.results_count": "{n} result(s)",
        "search.no_results": "No results",
        "search.too_many": "{n} matches (showing first {limit})",
        "search.empty_cache": "Cache is empty. Run Tools → Download Bible first.",
        "search.jump_hint": "Double-click a row to jump to that verse.",
        "menu.help": "Help",
        "menu.feedback": "Send feedback / open an issue…",
        "menu.cache_info": "Cache info…",
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


class FetchWorker(QObject):
    verses_ready = pyqtSignal(str, list)
    interlinear_ready = pyqtSignal(int, list)
    commentary_ready = pyqtSignal(int, str)
    error = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, fetcher: CrossBibleFetcher, ref: Reference, translations: list[str]):
        super().__init__()
        self.fetcher = fetcher
        self.ref = ref
        self.translations = translations
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        for t in self.translations:
            if self._cancel:
                break
            try:
                verses = self.fetcher.get_verses(t, self.ref)
                self.verses_ready.emit(t, verses)
            except Exception as e:
                self.error.emit(t, str(e))

        for v in self.ref.verse_numbers():
            if self._cancel:
                break
            try:
                words = self.fetcher.get_interlinear(self.ref.book_en, self.ref.chapter, v)
                self.interlinear_ready.emit(v, words)
            except Exception as e:
                self.error.emit("interlinear", f"v{v}: {e}")
            try:
                text = self.fetcher.get_commentary(self.ref.book_en, self.ref.chapter, v)
                self.commentary_ready.emit(v, text)
            except Exception as e:
                self.error.emit("commentary", f"v{v}: {e}")

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


class TranslationPanel(QWidget):
    def __init__(self, translation: str, label: str):
        super().__init__()
        self.translation = translation

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 12, 8, 12)
        v.setSpacing(6)

        v.addWidget(_section_label(label, level=1))

        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        if translation in ("GAE", "KLB"):
            f = self.body.font()
            f.setPointSize(f.pointSize() + 1)
            self.body.setFont(f)
        v.addWidget(self.body)

    def set_verses(self, verses: list[tuple[int, str]]):
        lines = []
        for n, text in verses:
            lines.append(f"<p style='margin:2px 0'><b>{n}</b>&nbsp;&nbsp;{text}</p>")
        self.body.setText("".join(lines))

    def set_error(self, message: str):
        self.body.setText(
            f"<p style='color:#c33'>{tr('verse.fetch_failed')}<br><small>{message}</small></p>"
        )

    def set_loading(self):
        self.body.setText(f"<p style='color:#888'>{tr('verse.loading')}</p>")


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
    def __init__(self, ref: Reference, verse: int, storage: Storage):
        super().__init__()
        self.ref = ref
        self.verse = verse
        self.storage = storage

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 12, 8, 12)
        v.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        header_row.addWidget(_section_label(f"{ref.book_ko} {ref.chapter}:{verse}", level=1))
        links = QLabel(_biblehub_links_html(ref.book_en, ref.chapter, verse))
        links.setTextFormat(Qt.TextFormat.RichText)
        links.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        links.setOpenExternalLinks(True)
        header_row.addWidget(links, 1)
        v.addLayout(header_row)

        v.addWidget(_section_label(tr("verse.interlinear_section"), level=2))
        self.interlinear = InterlinearTable()
        v.addWidget(self.interlinear)

        v.addWidget(_section_label(tr("verse.commentary_section"), level=2))
        self.commentary = QTextBrowser()
        self.commentary.setOpenExternalLinks(True)
        self.commentary.setFixedHeight(360)
        v.addWidget(self.commentary)

        v.addWidget(_section_label(tr("verse.note_section"), level=2))
        self.note = QPlainTextEdit()
        self.note.setPlaceholderText(tr("verse.note_placeholder"))
        self.note.setFixedHeight(150)
        self.note.setPlainText(storage.get_note(ref.book_en, ref.chapter, verse))
        self.note.textChanged.connect(self._save_note)
        v.addWidget(self.note)

        v.addWidget(_hline())

    def _save_note(self):
        self.storage.put_note(self.ref.book_en, self.ref.chapter, self.verse,
                              self.note.toPlainText())

    def set_interlinear(self, words: list[dict[str, str]]):
        self.interlinear.set_words(words)

    def set_commentary(self, text: str):
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

    def set_loading(self):
        self.interlinear.set_loading()
        self.commentary.setHtml(f"<p style='color:#888'>{tr('verse.loading')}</p>")

    def set_interlinear_error(self, message: str):
        self.interlinear.set_error(message)

    def set_commentary_error(self, message: str):
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

class MainWindow(QMainWindow):
    def __init__(self, storage: Storage, fetcher: CrossBibleFetcher, settings: QSettings):
        super().__init__()
        self.storage = storage
        self.fetcher = fetcher
        self.settings = settings
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None
        self._dl_thread: QThread | None = None
        self._dl_worker: DownloadWorker | None = None

        self.setWindowTitle(tr("app.title"))
        self.resize(1700, 1000)

        self._build_menu_bar()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addLayout(self._build_selector())
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

        help_menu = bar.addMenu(tr("menu.help"))
        feedback_action = QAction(tr("menu.feedback"), self)
        feedback_action.triggered.connect(self._on_open_feedback)
        help_menu.addAction(feedback_action)

    def _on_theme_chosen(self, theme: str):
        self.settings.setValue("theme", theme)
        self.settings.sync()  # 다음 실행에서 확실히 읽히도록 즉시 디스크에 flush
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, theme)

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

        self.lookup_btn = QPushButton(tr("selector.lookup"))
        self.lookup_btn.clicked.connect(self._on_lookup)
        row.addWidget(self.lookup_btn)

        row.addStretch(1)

        self.side_toggle_btn = QPushButton(tr("selector.side_on"))
        self.side_toggle_btn.setCheckable(True)
        self.side_toggle_btn.setChecked(True)
        self.side_toggle_btn.setToolTip(tr("selector.side_tooltip"))
        self.side_toggle_btn.toggled.connect(self._on_side_toggled)
        row.addWidget(self.side_toggle_btn)
        return row

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

    def _build_translations_column(self) -> QScrollArea:
        self._translations_container = QWidget()
        layout = QVBoxLayout(self._translations_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.panels: dict[str, TranslationPanel] = {}
        for i, code in enumerate(CrossBibleFetcher.TRANSLATIONS):
            panel = TranslationPanel(code, CrossBibleFetcher.TRANSLATION_LABELS[code])
            self.panels[code] = panel
            layout.addWidget(panel)
            if i < len(CrossBibleFetcher.TRANSLATIONS) - 1:
                layout.addWidget(_hline())

        layout.addStretch(1)
        return _wrap_in_scroll(self._translations_container)

    def _build_side_column(self) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(4)

        # 절 점프 네비게이션 — 스크롤 영역 위에 고정. 절을 받을 때마다 _rebuild_side 가
        # 버튼을 다시 채운다.
        self._nav_bar = QWidget()
        self._nav_layout = QHBoxLayout(self._nav_bar)
        self._nav_layout.setContentsMargins(4, 4, 4, 4)
        self._nav_layout.setSpacing(4)
        self._nav_layout.addStretch(1)
        wrapper_layout.addWidget(self._nav_bar)

        self._side_container = QWidget()
        self._side_layout = QVBoxLayout(self._side_container)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.setSpacing(0)
        self._side_layout.addStretch(1)
        self.verse_blocks: dict[int, VerseBlock] = {}

        self._side_scroll_inner = _wrap_in_scroll(self._side_container)
        wrapper_layout.addWidget(self._side_scroll_inner, 1)
        return wrapper

    def _rebuild_side(self, ref: Reference):
        # 기존 절 블록 제거
        for block in self.verse_blocks.values():
            block.setParent(None)
            block.deleteLater()
        self.verse_blocks.clear()

        # 네비 버튼 제거 (마지막 stretch 는 유지)
        while self._nav_layout.count() > 1:
            item = self._nav_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        stretch_idx = self._side_layout.count() - 1
        nav_insert = self._nav_layout.count() - 1  # stretch 앞 자리
        for v in ref.verse_numbers():
            block = VerseBlock(ref, v, self.storage)
            block.set_loading()
            self.verse_blocks[v] = block
            self._side_layout.insertWidget(stretch_idx, block)
            stretch_idx += 1

            btn = QPushButton(str(v))
            btn.setFixedHeight(24)
            btn.setStyleSheet("padding: 0 8px;")
            btn.setToolTip(f"{ref.book_ko} {ref.chapter}:{v}")
            btn.clicked.connect(lambda _checked=False, num=v: self._scroll_to_verse(num))
            self._nav_layout.insertWidget(nav_insert, btn)
            nav_insert += 1

    def _scroll_to_verse(self, verse: int):
        block = self.verse_blocks.get(verse)
        if block is None:
            return
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
        vs = self.verse_start.value()
        ve = max(self.verse_end.value(), vs)
        return Reference(en, ko_canonical, self.chap_box.value(), vs, ve)

    def _on_lookup(self):
        ref = self._current_ref()
        if ref is None:
            return
        if ref.verse_end - ref.verse_start > 20:
            QMessageBox.warning(
                self,
                tr("lookup.range_too_big_title"),
                tr("lookup.range_too_big_body"),
            )
            return

        if self._thread is not None:
            try:
                if self._worker is not None:
                    self._worker.cancel()
                self._thread.quit()
                self._thread.wait()
            except Exception:
                pass

        self.statusBar().showMessage(
            tr("status.looking_up", ref_ko=ref.header_ko, ref_en=ref.header_en)
        )
        self.setWindowTitle(tr("app.title_with_ref", ref=ref.header_ko))

        enabled = self._enabled_translations()
        for code, panel in self.panels.items():
            if code in enabled:
                panel.set_loading()
        self._rebuild_side(ref)

        verse_count = ref.verse_end - ref.verse_start + 1
        self._extras_total = verse_count * 2
        self._extras_done = 0

        self._thread = QThread(self)
        self._worker = FetchWorker(self.fetcher, ref, enabled)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)

        self._worker.verses_ready.connect(self._on_verses_ready)
        self._worker.interlinear_ready.connect(self._on_interlinear_ready)
        self._worker.commentary_ready.connect(self._on_commentary_ready)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._on_finished)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_verses_ready(self, translation: str, verses: list):
        panel = self.panels.get(translation)
        if panel:
            panel.set_verses(verses)

    def _on_interlinear_ready(self, verse: int, words: list):
        block = self.verse_blocks.get(verse)
        if block:
            block.set_interlinear(words)
        self._bump_extras_progress()

    def _on_commentary_ready(self, verse: int, text: str):
        block = self.verse_blocks.get(verse)
        if block:
            block.set_commentary(text)
        self._bump_extras_progress()

    def _bump_extras_progress(self):
        self._extras_done += 1
        if self._extras_done < self._extras_total:
            self.statusBar().showMessage(
                tr("status.extras_progress", done=self._extras_done, total=self._extras_total)
            )

    def _on_error(self, source: str, message: str):
        if source in self.panels:
            self.panels[source].set_error(message)
        elif source == "interlinear":
            try:
                num = int(message.split(":")[0].lstrip("v"))
                block = self.verse_blocks.get(num)
                if block:
                    block.set_interlinear_error(message)
            except Exception:
                self.statusBar().showMessage(f"[{source}] {message}", 8000)
        elif source == "commentary":
            try:
                num = int(message.split(":")[0].lstrip("v"))
                block = self.verse_blocks.get(num)
                if block:
                    block.set_commentary_error(message)
            except Exception:
                self.statusBar().showMessage(f"[{source}] {message}", 8000)
        else:
            self.statusBar().showMessage(f"[{source}] {message}", 8000)

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

    def _on_translation_toggled(self, code: str, checked: bool):
        panel = self.panels.get(code)
        if panel is not None:
            panel.setVisible(checked)
        if not any(cb.isChecked() for cb in self.translation_checks.values()):
            cb = self.translation_checks[code]
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            if panel is not None:
                panel.setVisible(True)
            self.statusBar().showMessage(tr("status.min_one_translation"), 3000)

    def _enabled_translations(self) -> list[str]:
        return [
            code for code in CrossBibleFetcher.TRANSLATIONS
            if self.translation_checks[code].isChecked()
        ]

    # ---- 도움말 ----

    def _on_open_feedback(self):
        QDesktopServices.openUrl(QUrl("https://github.com/yeonju7kim/CrossBible/issues"))

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
        # 결과 클릭 → 셀렉터에 값 채우고 즉시 조회
        from bible_books import BOOKS
        ko = next((k for en, k, _, _, _ in BOOKS if en == book_en), None)
        if ko is None:
            return
        self.book_box.setCurrentText(ko)
        self._on_book_changed(self.book_box.currentIndex())
        self.chap_box.setValue(chapter)
        self.verse_start.setValue(verse)
        self.verse_end.setValue(verse)
        self._on_lookup()

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
        else:
            QMessageBox.information(
                self,
                tr("download.done_title"),
                tr("download.done_body", done=done, total=total, failures=len(failures)),
            )


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
    sys.exit(app.exec())
