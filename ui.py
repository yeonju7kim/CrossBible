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
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
        "download.title": "전체 다운로드",
        "download.prompt_title": "전체 다운로드",
        "download.prompt_body": (
            "현재 체크된 번역본 ({translations}) 의 모든 책·장을 받아 캐시합니다.\n"
            "총 {total}개 페이지 호출, 약 {minutes}분 소요. 사이 약 0.7초씩 throttle.\n\n"
            "본문은 사용자 본인 PC의 SQLite 캐시에만 저장됩니다. "
            "개인 학습/연구 용도로만 사용해 주세요.\n\n"
            "지금 시작할까요?"
        ),
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
        "download.title": "Download all",
        "download.prompt_title": "Download all chapters",
        "download.prompt_body": (
            "This will cache every book/chapter of the currently enabled translations ({translations}).\n"
            "Total: {total} page requests, ~{minutes} minutes (throttled ~0.7s each).\n\n"
            "Text is stored only in your local SQLite cache. "
            "For personal study/research use.\n\n"
            "Start now?"
        ),
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

    def __init__(self, fetcher: CrossBibleFetcher, translations: list[str]):
        super().__init__()
        self.fetcher = fetcher
        self.translations = translations
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        done, total, failures = self.fetcher.download_all(
            self.translations,
            progress_cb=lambda d, t, label: self.progress.emit(d, t, label),
            cancel_cb=lambda: self._cancel,
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

        dict_action = QAction(tr("menu.dictionary"), self)
        dict_action.triggered.connect(self._on_open_dictionary)
        tools_menu.addAction(dict_action)
        self._dict_dialog: DictionaryDialog | None = None

        tools_menu.addSeparator()
        cache_action = QAction(tr("menu.cache_info"), self)
        cache_action.triggered.connect(self._on_open_cache_info)
        tools_menu.addAction(cache_action)

    def _on_theme_chosen(self, theme: str):
        self.settings.setValue("theme", theme)
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, theme)

    def _on_language_chosen(self, lang: str):
        if lang == _CURRENT_LANG:
            return
        self.settings.setValue("language", lang)
        QMessageBox.information(
            self,
            tr("language.restart_title"),
            tr("language.restart_body"),
        )

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

    def _build_side_column(self) -> QScrollArea:
        self._side_container = QWidget()
        self._side_layout = QVBoxLayout(self._side_container)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.setSpacing(0)
        self._side_layout.addStretch(1)
        self.verse_blocks: dict[int, VerseBlock] = {}
        return _wrap_in_scroll(self._side_container)

    def _rebuild_side(self, ref: Reference):
        for block in self.verse_blocks.values():
            block.setParent(None)
            block.deleteLater()
        self.verse_blocks.clear()
        stretch_idx = self._side_layout.count() - 1
        for v in ref.verse_numbers():
            block = VerseBlock(ref, v, self.storage)
            block.set_loading()
            self.verse_blocks[v] = block
            self._side_layout.insertWidget(stretch_idx, block)
            stretch_idx += 1

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

        from bible_books import BOOKS

        translations = self._enabled_translations()
        if not translations:
            return
        per_translation_pages = sum(chapters for _, _, _, _, chapters in BOOKS)
        total = per_translation_pages * len(translations)
        minutes = max(1, round(total * 0.7 / 60))
        label_list = ", ".join(CrossBibleFetcher.TRANSLATION_LABELS[t] for t in translations)

        confirm = QMessageBox.question(
            self,
            tr("download.prompt_title"),
            tr(
                "download.prompt_body",
                translations=label_list,
                total=total,
                minutes=minutes,
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._dl_dialog = QProgressDialog(
            tr("download.preparing"), tr("download.cancel"), 0, total, self
        )
        self._dl_dialog.setWindowTitle(tr("download.title"))
        self._dl_dialog.setMinimumDuration(0)
        self._dl_dialog.setAutoClose(False)
        self._dl_dialog.setAutoReset(False)
        self._dl_dialog.setValue(0)

        self._dl_thread = QThread(self)
        self._dl_worker = DownloadWorker(self.fetcher, translations)
        self._dl_worker.moveToThread(self._dl_thread)
        self._dl_thread.started.connect(self._dl_worker.run)

        self._dl_worker.progress.connect(self._on_dl_progress)
        self._dl_worker.finished.connect(self._on_dl_finished)
        self._dl_worker.finished.connect(self._dl_thread.quit)
        self._dl_thread.finished.connect(self._dl_worker.deleteLater)
        self._dl_thread.finished.connect(self._dl_thread.deleteLater)
        self._dl_dialog.canceled.connect(self._dl_worker.cancel)

        self._dl_thread.start()
        self._dl_dialog.show()

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
