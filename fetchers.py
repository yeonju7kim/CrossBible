"""성구·원어·주석 fetchers.

소스
----
- 개역개정 (GAE):     대한성서공회 https://www.bskorea.or.kr
- 우리말성경 (WLB):   https://nocr.net/korwrm
- 현대인의 성경 (KLB) / NIV / ESV: https://www.biblegateway.com
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

from nocr_data import NOCR_CHAPTER_POSTS
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
    "Amos": "amo", "Obadiah": "oba", "Jonah": "jnh", "Micah": "mic",
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

        # 범위 안에 실제로 없는 절(예: 디모데후서 1장은 18절까지)은 그냥 건너뛴다.
        # 본문을 하나도 못 찾았을 때만 실패로 처리.
        if not verses:
            raise RuntimeError(f"Bible Gateway: 본문을 찾지 못함 ({ref.header_en} {version})")
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

        if not verses:
            raise RuntimeError(f"대한성서공회: 본문을 찾지 못함 ({ref.header_ko})")
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


# ---------- nocr.net: 우리말성경 (WLB) ----------

class NocrFetcher:
    """nocr.net/korwrm 의 우리말성경 본문 조회.

    각 장이 별도 글로 게시되어 있고, 글 본문 안에 "절번호:절번호 본문" 평문이
    <br/><br/> 로 구분되어 들어 있다. 사이트 자체의 절 번호 표기를 그대로 사용.
    """

    BASE = "https://nocr.net/korwrm"

    def fetch(self, ref: Reference, version: str = "WLB") -> list[tuple[int, str]]:
        all_verses = dict(self.fetch_chapter(ref.book_en, ref.chapter))
        result = [(n, t) for n, t in sorted(all_verses.items())
                  if ref.verse_start <= n <= ref.verse_end]
        if not result:
            raise RuntimeError(f"우리말성경: 본문을 찾지 못함 ({ref.header_ko})")
        return result

    def fetch_chapter(self, book_en: str, chapter: int) -> list[tuple[int, str]]:
        chapters = NOCR_CHAPTER_POSTS.get(book_en)
        if chapters is None:
            raise RuntimeError(f"우리말성경 책 매핑 없음: {book_en}")
        post_id = chapters.get(chapter)
        if post_id is None:
            raise RuntimeError(f"우리말성경 장 매핑 없음: {book_en} {chapter}")
        url = f"{self.BASE}/{post_id}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"
        r.raise_for_status()
        return self._parse_chapter(r.text, chapter)

    @staticmethod
    def _parse_chapter(html: str, chapter: int) -> list[tuple[int, str]]:
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")
        if article is None:
            raise RuntimeError("nocr.net 본문 컨테이너(article) 없음")
        body = article.find("div", class_=re.compile(r"xe_content"))
        if body is None:
            body = article
        # <br/><br/> 가 절 구분자. 줄바꿈으로 텍스트화 후 라인 단위 파싱.
        for br in body.find_all("br"):
            br.replace_with("\n")
        raw = body.get_text("\n", strip=False)

        verses: dict[int, str] = {}
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^(\d+):(\d+)\s+(.+)$", line)
            if not m:
                continue
            chap_n = int(m.group(1))
            if chap_n != chapter:
                continue
            verse_n = int(m.group(2))
            text = re.sub(r"\s+", " ", m.group(3)).strip()
            if not text:
                continue
            verses[verse_n] = (verses.get(verse_n, "") + " " + text).strip()
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

    TRANSLATIONS = ["GAE", "WLB", "KLB", "NIV", "ESV"]
    TRANSLATION_LABELS = {
        "GAE": "개역개정",
        "WLB": "우리말성경",
        "KLB": "현대인의 성경",
        "NIV": "NIV",
        "ESV": "ESV",
    }

    def __init__(self, storage: Storage):
        self.storage = storage
        self.bg = BibleGatewayFetcher()
        self.bsk = BsKoreaFetcher()
        self.nocr = NocrFetcher()
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
            return self.nocr.fetch_chapter(book_en, chapter)
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

    def get_whole_chapter(self, translation: str, book_en: str, chapter: int,
                          force: bool = False) -> list[tuple[int, str]]:
        """장 전체 조회. 캐시에 있으면 그대로, 없으면 챕터 단위로 받아 캐시.

        force=True 면 캐시를 무시하고 다시 받아 덮어쓴다 (오래되거나 누락된 장 갱신).
        """
        if not force:
            cached = self.storage.get_chapter_verses(translation, book_en, chapter)
            if cached:
                return cached
        self._throttle()
        verses = self.fetch_chapter(translation, book_en, chapter)
        if verses:
            self.storage.put_verses(translation, book_en, chapter, verses)
        return verses

    def get_cached(self, translation: str, ref: Reference) -> list[tuple[int, str]] | None:
        """캐시에만 있으면 즉시 반환, 없으면 None. 네트워크/throttle 없음 (UI 스레드용)."""
        if ref.whole_chapter:
            return self.storage.get_chapter_verses(translation, ref.book_en, ref.chapter) or None
        return self.storage.get_verses(translation, ref)

    def get_verses(self, translation: str, ref: Reference, force: bool = False) -> list[tuple[int, str]]:
        if ref.whole_chapter:
            return self.get_whole_chapter(translation, ref.book_en, ref.chapter, force=force)
        if not force:
            cached = self.storage.get_verses(translation, ref)
            if cached is not None:
                return cached
        self._throttle()
        if translation == "GAE":
            verses = self.bsk.fetch(ref, "GAE")
        elif translation == "WLB":
            verses = self.nocr.fetch(ref, "WLB")
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
