"""PyQt6 메인 윈도우."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from bible_books import BOOKS, book_chapters, book_names_ko, lookup_by_ko
from fetchers import CrossBibleFetcher
from reference import Reference
from storage import Storage


# ---------- 백그라운드 작업 ----------

class FetchWorker(QObject):
    """단일 절(또는 절 범위)의 모든 데이터를 백그라운드에서 가져온다."""

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

class TranslationPanel(QWidget):
    """번역본 하나 — 라벨 + 본문."""

    def __init__(self, translation: str, label: str):
        super().__init__()
        self.translation = translation

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(4)

        head = QLabel(label)
        head_font = head.font()
        head_font.setBold(True)
        head_font.setPointSize(head_font.pointSize() + 1)
        head.setFont(head_font)
        v.addWidget(head)

        self.body = QTextBrowser()
        self.body.setOpenExternalLinks(True)
        # 한국어 번역본 글꼴 살짝 키움
        if translation in ("GAE", "WLB"):
            body_font = self.body.font()
            body_font.setPointSize(body_font.pointSize() + 1)
            self.body.setFont(body_font)
        v.addWidget(self.body, 1)

    def set_verses(self, verses: list[tuple[int, str]]):
        lines = []
        for n, text in verses:
            lines.append(f"<p><b>{n}</b>  {text}</p>")
        self.body.setHtml("".join(lines))

    def set_error(self, message: str):
        self.body.setHtml(
            f"<p style='color:#a00'>가져오기 실패<br><small>{message}</small></p>"
        )

    def set_loading(self):
        self.body.setHtml("<p style='color:#888'>불러오는 중…</p>")


class VerseTabs(QTabWidget):
    """절별 원어 / 주석 / 메모 표시. 절 단위로 서브탭."""

    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self.setDocumentMode(True)
        # kind별 위젯 보관: {(kind, verse_num): widget}
        self._widgets: dict[tuple[str, int], QWidget] = {}
        # 현재 ref
        self._ref: Reference | None = None
        # 절 단위 탭 묶음
        self._verse_widget_tabs: dict[int, QTabWidget] = {}

    def reset(self, ref: Reference):
        self.clear()
        self._widgets.clear()
        self._verse_widget_tabs.clear()
        self._ref = ref

        for v in ref.verse_numbers():
            verse_tab = QTabWidget()
            verse_tab.setDocumentMode(True)

            interlinear = QTableWidget(0, 4)
            interlinear.setHorizontalHeaderLabels(["Strong", "원어", "음역", "영어"])
            interlinear.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            interlinear.verticalHeader().setVisible(False)
            interlinear.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self._widgets[("interlinear", v)] = interlinear
            verse_tab.addTab(interlinear, "원어 (BibleHub)")

            commentary = QTextBrowser()
            commentary.setOpenExternalLinks(True)
            self._widgets[("commentary", v)] = commentary
            verse_tab.addTab(commentary, "주석")

            note = QPlainTextEdit()
            note.setPlaceholderText("이 절에 대한 메모를 입력하세요. (자동 저장)")
            note.setPlainText(self.storage.get_note(ref.book_en, ref.chapter, v))
            note.textChanged.connect(lambda v=v, note=note: self._save_note(v, note))
            self._widgets[("note", v)] = note
            verse_tab.addTab(note, "메모")

            self._verse_widget_tabs[v] = verse_tab
            self.addTab(verse_tab, f"{ref.chapter}:{v}")

    def _save_note(self, verse: int, widget: QPlainTextEdit):
        if self._ref is None:
            return
        self.storage.put_note(self._ref.book_en, self._ref.chapter, verse, widget.toPlainText())

    def set_interlinear(self, verse: int, words: list[dict[str, str]]):
        w = self._widgets.get(("interlinear", verse))
        if not isinstance(w, QTableWidget):
            return
        w.setRowCount(len(words))
        for row, wd in enumerate(words):
            for col, key in enumerate(("strong", "original", "translit", "english")):
                item = QTableWidgetItem(wd.get(key, ""))
                if key == "original":
                    f = item.font()
                    f.setPointSize(f.pointSize() + 2)
                    item.setFont(f)
                w.setItem(row, col, item)

    def set_commentary(self, verse: int, text: str):
        w = self._widgets.get(("commentary", verse))
        if not isinstance(w, QTextBrowser):
            return
        # 매우 단순한 markdown→html: ### 헤더와 빈줄 단위 단락만 처리.
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
        w.setHtml("\n".join(html_parts) or "<p style='color:#888'>주석 없음</p>")

    def set_error(self, kind: str, verse: int, message: str):
        w = self._widgets.get((kind, verse))
        if isinstance(w, QTextBrowser):
            w.setHtml(f"<p style='color:#a00'>{kind} 가져오기 실패<br><small>{message}</small></p>")
        elif isinstance(w, QTableWidget):
            w.setRowCount(1)
            w.setColumnCount(1)
            w.setHorizontalHeaderLabels(["오류"])
            w.setItem(0, 0, QTableWidgetItem(message))


# ---------- 메인 윈도우 ----------

class MainWindow(QMainWindow):
    def __init__(self, storage: Storage, fetcher: CrossBibleFetcher):
        super().__init__()
        self.storage = storage
        self.fetcher = fetcher
        self._thread: QThread | None = None
        self._worker: FetchWorker | None = None

        self.setWindowTitle("CrossBible — 다중 번역 성경 학습")
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        root.addLayout(self._build_selector())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._build_translations())
        split.addWidget(self._build_side())
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("준비됨")

        # 단축키
        QShortcut(QKeySequence("Return"), self.book_box, activated=self._on_lookup)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._on_lookup)

        self._on_book_changed(0)

    # ---- UI 구성 ----

    def _build_selector(self) -> QHBoxLayout:
        row = QHBoxLayout()

        row.addWidget(QLabel("책"))
        self.book_box = QComboBox()
        self.book_box.addItems(book_names_ko())
        self.book_box.currentIndexChanged.connect(self._on_book_changed)
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

    def _build_translations(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.panels: dict[str, TranslationPanel] = {}
        # 4개 패널을 2x2 로 — 가로폭이 좁아도 깨지지 않게 grid 대신 splitter 중첩
        top = QSplitter(Qt.Orientation.Horizontal)
        bottom = QSplitter(Qt.Orientation.Horizontal)
        codes = CrossBibleFetcher.TRANSLATIONS
        for i, code in enumerate(codes):
            parent = top if i < 2 else bottom
            p = TranslationPanel(code, CrossBibleFetcher.TRANSLATION_LABELS[code])
            self.panels[code] = p
            parent.addWidget(p)

        v_split = QSplitter(Qt.Orientation.Vertical)
        v_split.addWidget(top)
        v_split.addWidget(bottom)
        v_split.setStretchFactor(0, 1)
        v_split.setStretchFactor(1, 1)
        layout.addWidget(v_split)
        return container

    def _build_side(self) -> QWidget:
        self.verse_tabs = VerseTabs(self.storage)
        return self.verse_tabs

    # ---- 선택 처리 ----

    def _on_book_changed(self, idx: int):
        ko = self.book_box.currentText()
        info = lookup_by_ko(ko)
        if not info:
            return
        _, _, chapters = info
        self.chap_box.setRange(1, chapters)
        self.chap_box.setValue(1)
        # 절 범위는 실제 본문을 모르므로 표준 최대치 200으로 둠

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
        self.verse_tabs.reset(ref)

        # include_extras: 절 수가 너무 많지 않을 때만 원어/주석 가져옴
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
        self.verse_tabs.set_interlinear(verse, words)

    def _on_commentary_ready(self, verse: int, text: str):
        self.verse_tabs.set_commentary(verse, text)

    def _on_error(self, source: str, message: str):
        if source in self.panels:
            self.panels[source].set_error(message)
        else:
            # interlinear/commentary 류는 절별 메시지에 verse 번호 포함됨
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
