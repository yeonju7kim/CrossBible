"""PyQt6 메인 윈도우 — wide layout, 세로 스택, 양쪽 패널 스크롤."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
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


def _biblehub_links_html(book_en: str, chapter: int, verse: int) -> str:
    """절 헤더 옆에 표시할 BibleHub 링크 한 줄 (HTML)."""
    slug = BIBLEHUB_BOOK_SLUGS.get(book_en)
    if not slug:
        return ""
    base = "https://biblehub.com"
    cv = f"{chapter}-{verse}"
    parts = [
        f'<a href="{base}/{slug}/{cv}.htm">본문 비교</a>',
        f'<a href="{base}/interlinear/{slug}/{cv}.htm">원어</a>',
        f'<a href="{base}/commentaries/{slug}/{cv}.htm">주석</a>',
        f'<a href="{base}/lexicon/{slug}/{cv}.htm">렉시콘</a>',
    ]
    return (
        "<span style='font-size:10pt; color:#555'>BibleHub: "
        + " · ".join(parts)
        + "</span>"
    )


# ---------- 백그라운드 작업 ----------

class FetchWorker(QObject):
    verses_ready = pyqtSignal(str, list)            # translation, [(n, text)]
    interlinear_ready = pyqtSignal(int, list)       # verse_num, [{strong,...}]
    commentary_ready = pyqtSignal(int, str)         # verse_num, text
    error = pyqtSignal(str, str)                    # source, message
    finished = pyqtSignal()

    def __init__(self, fetcher: CrossBibleFetcher, ref: Reference, include_extras: bool):
        super().__init__()
        self.fetcher = fetcher
        self.ref = ref
        self.include_extras = include_extras
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        for t in CrossBibleFetcher.TRANSLATIONS:
            if self._cancel:
                break
            try:
                verses = self.fetcher.get_verses(t, self.ref)
                self.verses_ready.emit(t, verses)
            except Exception as e:
                self.error.emit(t, str(e))

        if self.include_extras and not self._cancel:
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
    """번역본 하나 — 라벨 + 본문 (QLabel, 자동 줄바꿈/자동 높이)."""

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
        # 한국어 번역본 글꼴 살짝 키움
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
            f"<p style='color:#a00'>가져오기 실패<br><small>{message}</small></p>"
        )

    def set_loading(self):
        self.body.setText("<p style='color:#888'>불러오는 중…</p>")


class InterlinearTable(QTableWidget):
    """모든 행을 표시하는 높이 고정 테이블."""

    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Strong", "원어", "음역", "영어"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # 내부 스크롤 끄기 — 부모 ScrollArea 가 처리
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
        self.setItem(0, 0, QTableWidgetItem("오류"))
        self.setItem(0, 1, QTableWidgetItem(message))
        self._fit_height()

    def _fit_height(self):
        self.resizeRowsToContents()
        header = self.horizontalHeader().height()
        rows = sum(self.rowHeight(r) for r in range(self.rowCount()))
        self.setFixedHeight(header + rows + 4)


class VerseBlock(QWidget):
    """한 절에 대한 [헤더 · 원어 · 주석 · 메모] 묶음."""

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

        v.addWidget(_section_label("원어 (BibleHub Interlinear)", level=2))
        self.interlinear = InterlinearTable()
        v.addWidget(self.interlinear)

        v.addWidget(_section_label("주석 (BibleHub Commentaries)", level=2))
        self.commentary = QTextBrowser()
        self.commentary.setOpenExternalLinks(True)
        self.commentary.setFixedHeight(360)
        v.addWidget(self.commentary)

        v.addWidget(_section_label("메모", level=2))
        self.note = QPlainTextEdit()
        self.note.setPlaceholderText("이 절에 대한 메모를 입력하세요. (자동 저장)")
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
        self.commentary.setHtml("\n".join(html_parts) or "<p style='color:#888'>주석 없음</p>")

    def set_loading(self):
        self.commentary.setHtml("<p style='color:#888'>불러오는 중…</p>")

    def set_interlinear_error(self, message: str):
        self.interlinear.set_error(message)

    def set_commentary_error(self, message: str):
        self.commentary.setHtml(
            f"<p style='color:#a00'>주석 가져오기 실패<br><small>{message}</small></p>"
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
    def __init__(self, storage: Storage, fetcher: CrossBibleFetcher):
        super().__init__()
        self.storage = storage
        self.fetcher = fetcher
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None

        self.setWindowTitle("CrossBible — 다중 번역 성경 학습")
        self.resize(1700, 1000)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addLayout(self._build_selector())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._build_translations_column())
        split.addWidget(self._build_side_column())
        split.setSizes([900, 800])
        root.addWidget(split, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("준비됨")

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._on_lookup)

        self._on_book_changed(0)

    # ---- UI 구성 ----

    def _build_selector(self) -> QHBoxLayout:
        row = QHBoxLayout()

        row.addWidget(QLabel("책"))
        self.book_box = QComboBox()
        self.book_box.addItems(book_names_ko())
        # 검색 가능한 콤보: "고" → 고린도전서/고린도후서/골로새서 처럼 시작 매칭으로 필터.
        self.book_box.setEditable(True)
        self.book_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.book_box.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # activated: 키보드/마우스로 항목을 명시적으로 선택한 순간만 발화.
        # currentIndexChanged 는 편집 중에도 발화되어 chap_box 초기화를 자꾸 트리거함.
        self.book_box.activated.connect(self._on_book_changed)
        row.addWidget(self.book_box, 1)

        row.addWidget(QLabel("장"))
        self.chap_box = QSpinBox()
        self.chap_box.setRange(1, 150)
        self.chap_box.valueChanged.connect(self._on_chap_changed)
        row.addWidget(self.chap_box)

        row.addWidget(QLabel("절"))
        self.verse_start = QSpinBox()
        self.verse_start.setRange(1, 200)
        self.verse_start.setValue(1)
        row.addWidget(self.verse_start)

        row.addWidget(QLabel("~"))
        self.verse_end = QSpinBox()
        self.verse_end.setRange(1, 200)
        self.verse_end.setValue(1)
        row.addWidget(self.verse_end)

        self.lookup_btn = QPushButton("조회 (Ctrl+Enter)")
        self.lookup_btn.clicked.connect(self._on_lookup)
        row.addWidget(self.lookup_btn)

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
        # 기존 블록 제거
        for block in self.verse_blocks.values():
            block.setParent(None)
            block.deleteLater()
        self.verse_blocks.clear()
        # stretch 위에 새 블록 삽입
        # stretch 가 항상 마지막 항목이라 가정 — 그 앞 위치에 insertWidget
        stretch_idx = self._side_layout.count() - 1
        for v in ref.verse_numbers():
            block = VerseBlock(ref, v, self.storage)
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
            QMessageBox.warning(self, "범위 큼", "한 번에 20절 이하로 조회해 주세요.")
            return

        # 이전 작업 정리
        if self._thread is not None:
            try:
                if self._worker is not None:
                    self._worker.cancel()
                self._thread.quit()
                self._thread.wait()
            except Exception:
                pass

        self.statusBar().showMessage(f"{ref.header_ko} ({ref.header_en}) 조회 중…")
        self.setWindowTitle(f"CrossBible — {ref.header_ko}")

        for panel in self.panels.values():
            panel.set_loading()
        self._rebuild_side(ref)

        include_extras = (ref.verse_end - ref.verse_start) <= 5

        self._thread = QThread(self)
        self._worker = FetchWorker(self.fetcher, ref, include_extras)
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

    def _on_commentary_ready(self, verse: int, text: str):
        block = self.verse_blocks.get(verse)
        if block:
            block.set_commentary(text)

    def _on_error(self, source: str, message: str):
        if source in self.panels:
            self.panels[source].set_error(message)
        elif source == "interlinear":
            # message 형식 "v3: ..."
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
        self.statusBar().showMessage("완료", 3000)
        self._worker = None
        self._thread = None


def run():
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("CrossBible")

    base = Path.home() / ".crossbible"
    storage = Storage(base / "data.db")
    fetcher = CrossBibleFetcher(storage)

    win = MainWindow(storage, fetcher)
    win.show()
    sys.exit(app.exec())
