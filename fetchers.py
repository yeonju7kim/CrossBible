"""성구·원어·주석 fetchers.

소스
----
- 개역개정 (GAE):     대한성서공회 https://www.bskorea.or.kr
- 우리말성경 (WLB):   유튜버전(YouVersion) bible.com  (best-effort, 없으면 안내)
- NIV / ESV:          https://www.biblegateway.com
- 원어/Interlinear:   https://biblehub.com/interlinear/{book}/{c}-{v}.htm
- 주석:               https://biblehub.com/commentaries/{book}/{c}-{v}.htm

모두 사용자 본인 머신에서 캐시 우선 조회. 본문은 코드에 임베드하지 않는다.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from reference import Reference
from storage import Storage


# ---------- 대한성서공회 책 코드 ----------

BSKOREA_BOOK_CODES = {
    "Genesis": "gen", "Exodus": "exo", "Leviticus": "lev", "Numbers": "num",
    "Deuteronomy": "deu", "Joshua": "jos", "Judges": "jdg", "Ruth": "rut",
    "1 Samuel": "1sa", "2 Samuel": "2sa", "1 Kings": "1ki", "2 Kings": "2ki",
    "1 Chronicles": "1ch", "2 Chronicles": "2ch", "Ezra": "ezr",
    "Nehemiah": "neh", "Esther": "est", "Job": "job", "Psalms": "psa",
    "Proverbs": "pro", "Ecclesiastes": "ecc", "Song of Songs": "sng",
    "Isaiah": "isa", "Jeremiah": "jer", "Lamentations": "lam",
    "Ezekiel": "ezk", "Daniel": "dan", "Hosea": "hos", "Joel": "jol",
    "Amos": "amo", "Obadiah": "oba", "Jonah": "jon", "Micah": "mic",
    "Nahum": "nam", "Habakkuk": "hab", "Zephaniah": "zep", "Haggai": "hag",
    "Zechariah": "zec", "Malachi": "mal",
    "Matthew": "mat", "Mark": "mrk", "Luke": "luk", "John": "jhn",
    "Acts": "act", "Romans": "rom", "1 Corinthians": "1co",
    "2 Corinthians": "2co", "Galatians": "gal", "Ephesians": "eph",
    "Philippians": "php", "Colossians": "col",
    "1 Thessalonians": "1th", "2 Thessalonians": "2th",
    "1 Timothy": "1ti", "2 Timothy": "2ti", "Titus": "tit",
    "Philemon": "phm", "Hebrews": "heb", "James": "jas",
    "1 Peter": "1pe", "2 Peter": "2pe", "1 John": "1jn", "2 John": "2jn",
    "3 John": "3jn", "Jude": "jud", "Revelation": "rev",
}

# biblehub 은 책 이름을 소문자·언더스코어로 표기. "1 Samuel" → "1_samuel".
BIBLEHUB_BOOK_SLUGS = {
    "Genesis": "genesis", "Exodus": "exodus", "Leviticus": "leviticus",
    "Numbers": "numbers", "Deuteronomy": "deuteronomy", "Joshua": "joshua",
    "Judges": "judges", "Ruth": "ruth",
    "1 Samuel": "1_samuel", "2 Samuel": "2_samuel",
    "1 Kings": "1_kings", "2 Kings": "2_kings",
    "1 Chronicles": "1_chronicles", "2 Chronicles": "2_chronicles",
    "Ezra": "ezra", "Nehemiah": "nehemiah", "Esther": "esther",
    "Job": "job", "Psalms": "psalms", "Proverbs": "proverbs",
    "Ecclesiastes": "ecclesiastes", "Song of Songs": "songs",
    "Isaiah": "isaiah", "Jeremiah": "jeremiah", "Lamentations": "lamentations",
    "Ezekiel": "ezekiel", "Daniel": "daniel", "Hosea": "hosea",
    "Joel": "joel", "Amos": "amos", "Obadiah": "obadiah", "Jonah": "jonah",
    "Micah": "micah", "Nahum": "nahum", "Habakkuk": "habakkuk",
    "Zephaniah": "zephaniah", "Haggai": "haggai", "Zechariah": "zechariah",
    "Malachi": "malachi",
    "Matthew": "matthew", "Mark": "mark", "Luke": "luke", "John": "john",
    "Acts": "acts", "Romans": "romans",
    "1 Corinthians": "1_corinthians", "2 Corinthians": "2_corinthians",
    "Galatians": "galatians", "Ephesians": "ephesians",
    "Philippians": "philippians", "Colossians": "colossians",
    "1 Thessalonians": "1_thessalonians", "2 Thessalonians": "2_thessalonians",
    "1 Timothy": "1_timothy", "2 Timothy": "2_timothy",
    "Titus": "titus", "Philemon": "philemon", "Hebrews": "hebrews",
    "James": "james",
    "1 Peter": "1_peter", "2 Peter": "2_peter",
    "1 John": "1_john", "2 John": "2_john", "3 John": "3_john",
    "Jude": "jude", "Revelation": "revelation",
}

# bible.com (YouVersion) 책 약어 — 우리말성경(WLB) 등 다국어 공통.
YOUVERSION_BOOK_CODES = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM",
    "Deuteronomy": "DEU", "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT",
    "1 Samuel": "1SA", "2 Samuel": "2SA", "1 Kings": "1KI", "2 Kings": "2KI",
    "1 Chronicles": "1CH", "2 Chronicles": "2CH", "Ezra": "EZR",
    "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalms": "PSA",
    "Proverbs": "PRO", "Ecclesiastes": "ECC", "Song of Songs": "SNG",
    "Isaiah": "ISA", "Jeremiah": "JER", "Lamentations": "LAM",
    "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS", "Joel": "JOL",
    "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON", "Micah": "MIC",
    "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG",
    "Zechariah": "ZEC", "Malachi": "MAL",
    "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN",
    "Acts": "ACT", "Romans": "ROM", "1 Corinthians": "1CO",
    "2 Corinthians": "2CO", "Galatians": "GAL", "Ephesians": "EPH",
    "Philippians": "PHP", "Colossians": "COL",
    "1 Thessalonians": "1TH", "2 Thessalonians": "2TH",
    "1 Timothy": "1TI", "2 Timothy": "2TI", "Titus": "TIT",
    "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS",
    "1 Peter": "1PE", "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN",
    "3 John": "3JN", "Jude": "JUD", "Revelation": "REV",
}

# YouVersion 번역본 ID. WLB(우리말성경) = 2308.
YOUVERSION_VERSIONS = {
    "WLB": 2308,
}


USER_AGENT = "Mozilla/5.0 (CrossBible study app)"
HEADERS = {"User-Agent": USER_AGENT}


# ---------- Bible Gateway: NIV / ESV ----------

class BibleGatewayFetcher:
    URL = "https://www.biblegateway.com/passage/"

    def fetch(self, ref: Reference, version: str) -> list[tuple[int, str]]:
        q = {"search": ref.header_en, "version": version}
        r = requests.get(self.URL + "?" + urlencode(q), headers=HEADERS, timeout=20)
        r.raise_for_status()
        return self._parse(r.text, ref, version)

    def fetch_chapter(self, book_en: str, chapter: int, version: str) -> list[tuple[int, str]]:
        """챕터 전체의 모든 절을 받는다 (절 범위 필터 없음, 누락 검사 없음)."""
        q = {"search": f"{book_en} {chapter}", "version": version}
        r = requests.get(self.URL + "?" + urlencode(q), headers=HEADERS, timeout=20)
        r.raise_for_status()
        return self._parse_chapter(r.text, chapter)

    @staticmethod
    def _parse(html: str, ref: Reference, version: str) -> list[tuple[int, str]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".passage-text")
        if container is None:
            raise RuntimeError(f"Bible Gateway: passage-text 없음 ({ref.header_en} {version})")

        for sel in [
            "sup.crossreference", "sup.footnote", "div.footnotes",
            "div.crossrefs", "h3", "h4", "span.chapternum",
        ]:
            for tag in container.select(sel):
                tag.decompose()

        # 클래스 한 줄에 (chap, verse) 쌍이 1개 이상 들어 있다 (e.g. "Gen-1-6-Gen-1-7"
        # 처럼 묶음 절). 모두 추출해서 같은 본문 텍스트를 해당 절들에 부여.
        verses: dict[int, str] = {}
        for span in container.select("span.text"):
            class_str = " ".join(span.get("class", []))
            matched = set()
            for chap_s, verse_s in re.findall(r"[A-Za-z]\w*-(\d+)-(\d+)", class_str):
                if int(chap_s) == ref.chapter:
                    matched.add(int(verse_s))
            matched = {n for n in matched if ref.verse_start <= n <= ref.verse_end}
            if not matched:
                continue
            for sup in span.select("sup.versenum"):
                sup.decompose()
            text = span.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            for n in matched:
                verses[n] = (verses.get(n, "") + " " + text).strip()

        missing = [n for n in ref.verse_numbers() if n not in verses]
        if missing:
            raise RuntimeError(f"Bible Gateway 누락 절 {missing} ({ref.header_en} {version})")
        return sorted(verses.items())

    @staticmethod
    def _parse_chapter(html: str, chapter: int) -> list[tuple[int, str]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".passage-text")
        if container is None:
            raise RuntimeError("Bible Gateway: passage-text 없음")
        for sel in [
            "sup.crossreference", "sup.footnote", "div.footnotes",
            "div.crossrefs", "h3", "h4", "span.chapternum",
        ]:
            for tag in container.select(sel):
                tag.decompose()

        verses: dict[int, str] = {}
        for span in container.select("span.text"):
            class_str = " ".join(span.get("class", []))
            matched = set()
            for chap_s, verse_s in re.findall(r"[A-Za-z]\w*-(\d+)-(\d+)", class_str):
                if int(chap_s) == chapter:
                    matched.add(int(verse_s))
            if not matched:
                continue
            for sup in span.select("sup.versenum"):
                sup.decompose()
            text = span.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            for n in matched:
                verses[n] = (verses.get(n, "") + " " + text).strip()
        return sorted(verses.items())


# ---------- 대한성서공회: 개역개정 ----------

class BsKoreaFetcher:
    URL = "https://www.bskorea.or.kr/bible/korbibReadpage.php"

    def fetch(self, ref: Reference, version: str = "GAE") -> list[tuple[int, str]]:
        code = BSKOREA_BOOK_CODES.get(ref.book_en)
        if code is None:
            raise RuntimeError(f"대한성서공회 책 코드 없음: {ref.book_en}")
        q = {"version": version, "book": code, "chap": str(ref.chapter)}
        r = requests.get(self.URL + "?" + urlencode(q), headers=HEADERS, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"
        r.raise_for_status()
        return self._parse(r.text, ref)

    def fetch_chapter(self, book_en: str, chapter: int, version: str = "GAE") -> list[tuple[int, str]]:
        code = BSKOREA_BOOK_CODES.get(book_en)
        if code is None:
            raise RuntimeError(f"대한성서공회 책 코드 없음: {book_en}")
        q = {"version": version, "book": code, "chap": str(chapter)}
        r = requests.get(self.URL + "?" + urlencode(q), headers=HEADERS, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"
        r.raise_for_status()
        return self._parse_chapter(r.text)

    @staticmethod
    def _parse(html: str, ref: Reference) -> list[tuple[int, str]]:
        # 정규식으로 tdBible1 div 안쪽을 잘라내면 안쪽에 중첩된 각주 <div> 의
        # 첫 </div> 에서 잘려 17절 이후가 사라지는 사고가 난다 (예: 고전 1:17).
        # BeautifulSoup 으로 #tdBible1 컨테이너를 직접 잡아 안전하게 파싱.
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("#tdBible1")
        if container is None:
            raise RuntimeError(f"대한성서공회 본문 컨테이너(#tdBible1) 없음 ({ref.header_ko})")

        for tag in container.select(
            "div.D2, a.comment, [id^='voice'], .chapNum, .smallTitle"
        ):
            tag.decompose()

        verses: dict[int, str] = {}
        for outer in container.find_all("span", recursive=True):
            num_tag = outer.find("span", class_="number", recursive=False)
            if num_tag is None:
                continue
            num_text = num_tag.get_text(strip=True)
            if not num_text.isdigit():
                continue
            n = int(num_text)
            if not (ref.verse_start <= n <= ref.verse_end):
                continue
            num_tag.extract()
            text = outer.get_text(separator="", strip=False)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                verses[n] = text

        missing = [n for n in ref.verse_numbers() if n not in verses]
        if missing:
            raise RuntimeError(f"대한성서공회 누락 절 {missing} ({ref.header_ko})")
        return sorted(verses.items())

    @staticmethod
    def _parse_chapter(html: str) -> list[tuple[int, str]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("#tdBible1")
        if container is None:
            raise RuntimeError("대한성서공회 본문 컨테이너(#tdBible1) 없음")
        for tag in container.select(
            "div.D2, a.comment, [id^='voice'], .chapNum, .smallTitle"
        ):
            tag.decompose()

        verses: dict[int, str] = {}
        for outer in container.find_all("span", recursive=True):
            num_tag = outer.find("span", class_="number", recursive=False)
            if num_tag is None:
                continue
            num_text = num_tag.get_text(strip=True)
            if not num_text.isdigit():
                continue
            n = int(num_text)
            num_tag.extract()
            text = outer.get_text(separator="", strip=False)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                verses[n] = text
        return sorted(verses.items())


# ---------- YouVersion (bible.com): 우리말성경 ----------

class YouVersionFetcher:
    """bible.com 의 정적 HTML 페이지에서 본문 추출.

    URL 예: https://www.bible.com/bible/2308/GEN.1.WLB
    페이지 안에 ``"reference":{...}, "content":"…"`` 형태의 JSON 조각이
    포함되어 있어 그 안에서 절 단위 텍스트를 뽑는다.
    """

    BASE = "https://www.bible.com/bible"

    def fetch(self, ref: Reference, version: str = "WLB") -> list[tuple[int, str]]:
        version_id = YOUVERSION_VERSIONS.get(version)
        if version_id is None:
            raise RuntimeError(f"YouVersion version 미지원: {version}")
        slug = YOUVERSION_BOOK_CODES.get(ref.book_en)
        if slug is None:
            raise RuntimeError(f"YouVersion 책 코드 없음: {ref.book_en}")
        url = f"{self.BASE}/{version_id}/{slug}.{ref.chapter}.{version}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return self._parse(r.text, ref)

    @staticmethod
    def _parse(html: str, ref: Reference) -> list[tuple[int, str]]:
        soup = BeautifulSoup(html, "html.parser")

        verses: dict[int, str] = {}
        # bible.com 본문은 <span class="verse vN">… 형태로 절 단위 표시.
        for span in soup.select("span.verse"):
            classes = span.get("class", [])
            num = None
            for c in classes:
                m = re.match(r"^v(\d+)$", c)
                if m:
                    num = int(m.group(1))
                    break
            if num is None:
                continue
            if not (ref.verse_start <= num <= ref.verse_end):
                continue
            for label in span.select("span.label"):
                label.decompose()
            for note in span.select("span.note, span.footnote, span.heading"):
                note.decompose()
            text = span.get_text(separator="", strip=False)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                verses[num] = (verses.get(num, "") + " " + text).strip()

        missing = [n for n in ref.verse_numbers() if n not in verses]
        if missing:
            raise RuntimeError(f"YouVersion 누락 절 {missing} ({ref.header_ko})")
        return sorted(verses.items())


# ---------- biblehub: interlinear (원어) ----------

class BibleHubInterlinearFetcher:
    """절별 interlinear 페이지에서 단어별 (Strong, 원어, 음역, 영어) 추출."""

    BASE = "https://biblehub.com/interlinear"

    def fetch(self, book_en: str, chapter: int, verse: int) -> list[dict[str, str]]:
        slug = BIBLEHUB_BOOK_SLUGS.get(book_en)
        if slug is None:
            raise RuntimeError(f"biblehub 책 슬러그 없음: {book_en}")
        url = f"{self.BASE}/{slug}/{chapter}-{verse}.htm"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return self._parse(r.text)

    @staticmethod
    def _parse(html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        # biblehub interlinear: 단어별 <table class="tablefloat"><td>…</td></table>.
        # 셀 안의 의미 있는 span:
        #   .pos       — Strong's number
        #   .translit  — 음역
        #   .greek / .hebrew — 원어
        #   .eng       — 영어 의미
        # 두 번째 .strongsnt 는 품사 표시(Adv 등) — 영어 의미 뒤에 붙임.
        words: list[dict[str, str]] = []

        def text(el) -> str:
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el else ""

        for tf in soup.select("table.tablefloat"):
            td = tf.find("td")
            if td is None:
                continue
            pos = td.select_one("span.pos")
            translit = td.select_one("span.translit")
            original = td.select_one("span.greek, span.hebrew")
            eng = td.select_one("span.eng")
            # 품사 span (두 번째 strongsnt, [e] 가 아닌 것)
            grammar = ""
            for s in td.select("span.strongsnt"):
                t = text(s)
                if t and t != "[e]" and not t.isdigit():
                    grammar = t
                    break
            if not (original or translit):
                continue
            english = text(eng)
            if grammar:
                english = f"{english} ({grammar})" if english else grammar
            words.append({
                "strong": text(pos),
                "original": text(original),
                "translit": text(translit),
                "english": english,
            })

        return words


# ---------- biblehub: commentaries ----------

class BibleHubCommentaryFetcher:
    BASE = "https://biblehub.com/commentaries"

    def fetch(self, book_en: str, chapter: int, verse: int) -> str:
        slug = BIBLEHUB_BOOK_SLUGS.get(book_en)
        if slug is None:
            raise RuntimeError(f"biblehub 책 슬러그 없음: {book_en}")
        url = f"{self.BASE}/{slug}/{chapter}-{verse}.htm"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return self._parse(r.text)

    @staticmethod
    def _parse(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for sel in ["script", "style", "iframe", "ins", "noscript"]:
            for tag in soup.select(sel):
                tag.decompose()

        box = soup.select_one("#leftbox .padleft") or soup.select_one("#leftbox")
        if box is None:
            return "주석 본문을 추출하지 못했습니다."

        # 헤더 div 앞에 마커를 삽입한 뒤 HTML 을 통째로 text 화.
        for h in box.select("div.vheading2"):
            h.insert_before("\n\n###HEAD###")
            h.insert_after("\n\n")
        # 단락 구분: <p> 태그 자리에 빈 줄 삽입
        for p in box.find_all("p"):
            p.insert_before("\n\n")
        # 광고/링크 컨테이너 제거
        for sel in ["#ad1", "#leftbox .commentaries", ".cverse2", ".cverse3", ".comtype"]:
            for tag in box.select(sel):
                tag.decompose()

        raw = box.get_text("\n", strip=False)
        # 정리: 헤더 마커 → ### , 다중 공백/줄바꿈 정돈
        raw = raw.replace("###HEAD###", "### ")
        # 줄 단위로 모은 뒤 인접 공백 정리
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.split("\n")]
        # 빈 줄로 단락 구분
        out: list[str] = []
        buf: list[str] = []
        for ln in lines:
            if not ln:
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            elif ln.startswith("### "):
                if buf:
                    out.append(" ".join(buf))
                    buf = []
                out.append(ln)
            else:
                buf.append(ln)
        if buf:
            out.append(" ".join(buf))

        body = "\n\n".join(out).strip()
        return body or "주석 본문을 추출하지 못했습니다."


# ---------- 통합 ----------

class CrossBibleFetcher:
    """모든 소스 통합. 캐시 우선, 미스시 네트워크."""

    POLITE_DELAY_SEC = 0.7

    # 우리말성경(WLB)은 무료로 공개된 정형 API/페이지가 없어 현재 미연동.
    # 대신 BibleGateway 의 KLB(현대인의 성경)를 두 번째 한국어 번역으로 사용.
    TRANSLATIONS = ["GAE", "KLB", "NIV", "ESV"]
    TRANSLATION_LABELS = {
        "GAE": "개역개정",
        "KLB": "현대인의 성경",
        "NIV": "NIV",
        "ESV": "ESV",
    }

    def __init__(self, storage: Storage):
        self.storage = storage
        self.bg = BibleGatewayFetcher()
        self.bsk = BsKoreaFetcher()
        self.yv = YouVersionFetcher()
        self.interlinear = BibleHubInterlinearFetcher()
        self.commentary = BibleHubCommentaryFetcher()
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < self.POLITE_DELAY_SEC:
            time.sleep(self.POLITE_DELAY_SEC - elapsed)
        self._last_call = time.time()

    # ---- 챕터 단위 다운로드 (오프라인 사전 캐시용) ----

    def fetch_chapter(self, translation: str, book_en: str, chapter: int) -> list[tuple[int, str]]:
        if translation == "GAE":
            return self.bsk.fetch_chapter(book_en, chapter, "GAE")
        if translation in ("NIV", "ESV", "KLB"):
            return self.bg.fetch_chapter(book_en, chapter, translation)
        if translation == "WLB":
            # WLB(YouVersion)은 현재 미연동 — 다운로드도 건너뜀
            raise RuntimeError("WLB는 미연동 번역본입니다")
        raise RuntimeError(f"Unsupported translation: {translation}")

    def download_all(
        self,
        translations,
        progress_cb=None,
        cancel_cb=None,
        books=None,
    ):
        """선택한 책들의 모든 장을 받아 캐시.

        translations: 다운로드할 번역 코드 리스트
        books: 다운로드할 책 영문명 리스트. None 이면 66권 모두.
        progress_cb(done:int, total:int, label:str) — 진행 콜백
        cancel_cb() -> bool — True 반환 시 중단
        반환: (done, total, failures: list[(translation, book_en, chapter, msg)])
        """
        from bible_books import BOOKS

        if books is None:
            book_set = None
        else:
            book_set = set(books)

        selected_books = [
            (en, ko, chapters)
            for en, ko, _, _, chapters in BOOKS
            if book_set is None or en in book_set
        ]

        total = sum(chapters for _, _, chapters in selected_books) * len(translations)
        done = 0
        failures: list[tuple[str, str, int, str]] = []

        for translation in translations:
            label = self.TRANSLATION_LABELS.get(translation, translation)
            for book_en, book_ko, max_chap in selected_books:
                for chap in range(1, max_chap + 1):
                    if cancel_cb and cancel_cb():
                        return done, total, failures
                    if self.storage.chapter_cached(translation, book_en, chap):
                        done += 1
                        if progress_cb:
                            progress_cb(done, total, f"{label} · {book_ko} {chap}장 (캐시됨)")
                        continue
                    # cancel 을 빠르게 인지하도록 throttle 을 0.1초 단위로 쪼개 대기
                    if not self._throttle_interruptible(cancel_cb):
                        return done, total, failures
                    try:
                        verses = self.fetch_chapter(translation, book_en, chap)
                        if verses:
                            self.storage.put_verses(translation, book_en, chap, verses)
                        else:
                            failures.append((translation, book_en, chap, "절 없음"))
                    except Exception as e:
                        failures.append((translation, book_en, chap, str(e)))
                    done += 1
                    if progress_cb:
                        progress_cb(done, total, f"{label} · {book_ko} {chap}장")

        return done, total, failures

    def _throttle_interruptible(self, cancel_cb=None) -> bool:
        """0.1초 단위로 sleep 하면서 cancel_cb 를 체크. 취소되면 False 반환."""
        target = self._last_call + self.POLITE_DELAY_SEC
        while time.time() < target:
            if cancel_cb and cancel_cb():
                self._last_call = time.time()
                return False
            time.sleep(min(0.1, max(0.0, target - time.time())))
        self._last_call = time.time()
        return True

    # ---- 본문 ----

    def get_verses(self, translation: str, ref: Reference) -> list[tuple[int, str]]:
        cached = self.storage.get_verses(translation, ref)
        if cached is not None:
            return cached
        self._throttle()
        if translation == "GAE":
            verses = self.bsk.fetch(ref, "GAE")
        elif translation == "WLB":
            verses = self.yv.fetch(ref, "WLB")
        elif translation in ("NIV", "ESV", "KLB"):
            verses = self.bg.fetch(ref, translation)
        else:
            raise RuntimeError(f"Unsupported translation: {translation}")
        self.storage.put_verses(translation, ref.book_en, ref.chapter, verses)
        return verses

    # ---- 원어 ----

    def get_interlinear(self, book_en: str, chapter: int, verse: int) -> list[dict[str, str]]:
        import json
        cached = self.storage.get_blob("interlinear", book_en, chapter, verse)
        if cached is not None:
            return json.loads(cached)
        self._throttle()
        words = self.interlinear.fetch(book_en, chapter, verse)
        self.storage.put_blob("interlinear", book_en, chapter, verse, json.dumps(words, ensure_ascii=False))
        return words

    # ---- 주석 ----

    def get_commentary(self, book_en: str, chapter: int, verse: int) -> str:
        cached = self.storage.get_blob("commentary", book_en, chapter, verse)
        if cached is not None:
            return cached
        self._throttle()
        text = self.commentary.fetch(book_en, chapter, verse)
        self.storage.put_blob("commentary", book_en, chapter, verse, text)
        return text
