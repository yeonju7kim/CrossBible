"""66권 정규명 / 한글-영문 별칭 매핑 + 장수 정보."""
from __future__ import annotations

BOOKS: list[tuple[str, str, list[str], list[str], int]] = [
    ("Genesis", "창세기", ["Gen", "Ge", "Gn"], ["창"], 50),
    ("Exodus", "출애굽기", ["Exod", "Exo", "Ex"], ["출"], 40),
    ("Leviticus", "레위기", ["Lev", "Lv"], ["레"], 27),
    ("Numbers", "민수기", ["Num", "Nu", "Nm"], ["민"], 36),
    ("Deuteronomy", "신명기", ["Deut", "Dt"], ["신"], 34),
    ("Joshua", "여호수아", ["Josh", "Jos"], ["수"], 24),
    ("Judges", "사사기", ["Judg", "Jdg"], ["삿"], 21),
    ("Ruth", "룻기", ["Ru"], ["룻"], 4),
    ("1 Samuel", "사무엘상", ["1 Sam", "1Sam", "1 Sa", "1Sa"], ["삼상"], 31),
    ("2 Samuel", "사무엘하", ["2 Sam", "2Sam", "2 Sa", "2Sa"], ["삼하"], 24),
    ("1 Kings", "열왕기상", ["1 Kgs", "1Kgs", "1 Ki", "1Ki"], ["왕상"], 22),
    ("2 Kings", "열왕기하", ["2 Kgs", "2Kgs", "2 Ki", "2Ki"], ["왕하"], 25),
    ("1 Chronicles", "역대상", ["1 Chr", "1Chr", "1 Ch", "1Ch"], ["대상"], 29),
    ("2 Chronicles", "역대하", ["2 Chr", "2Chr", "2 Ch", "2Ch"], ["대하"], 36),
    ("Ezra", "에스라", ["Ezr"], ["스"], 10),
    ("Nehemiah", "느헤미야", ["Neh", "Ne"], ["느"], 13),
    ("Esther", "에스더", ["Esth", "Est"], ["에"], 10),
    ("Job", "욥기", ["Jb"], ["욥"], 42),
    ("Psalms", "시편", ["Psalm", "Ps", "Psa", "Pss"], ["시"], 150),
    ("Proverbs", "잠언", ["Prov", "Pro", "Pr"], ["잠"], 31),
    ("Ecclesiastes", "전도서", ["Eccl", "Ecc", "Ec", "Qoh"], ["전"], 12),
    ("Song of Songs", "아가", ["Song", "SOS", "Sng", "Song of Solomon"], ["아"], 8),
    ("Isaiah", "이사야", ["Isa", "Is"], ["사"], 66),
    ("Jeremiah", "예레미야", ["Jer", "Je"], ["렘"], 52),
    ("Lamentations", "예레미야애가", ["Lam", "La"], ["애"], 5),
    ("Ezekiel", "에스겔", ["Ezek", "Eze", "Ezk"], ["겔"], 48),
    ("Daniel", "다니엘", ["Dan", "Dn"], ["단"], 12),
    ("Hosea", "호세아", ["Hos", "Ho"], ["호"], 14),
    ("Joel", "요엘", ["Jl"], ["욜"], 3),
    ("Amos", "아모스", ["Am"], ["암"], 9),
    ("Obadiah", "오바댜", ["Obad", "Ob"], ["옵"], 1),
    ("Jonah", "요나", ["Jnh", "Jon"], ["욘"], 4),
    ("Micah", "미가", ["Mic", "Mc"], ["미"], 7),
    ("Nahum", "나훔", ["Nah", "Na"], ["나"], 3),
    ("Habakkuk", "하박국", ["Hab", "Hb"], ["합"], 3),
    ("Zephaniah", "스바냐", ["Zeph", "Zep", "Zph"], ["습"], 3),
    ("Haggai", "학개", ["Hag", "Hg"], ["학"], 2),
    ("Zechariah", "스가랴", ["Zech", "Zec", "Zch"], ["슥"], 14),
    ("Malachi", "말라기", ["Mal", "Ml"], ["말"], 4),
    ("Matthew", "마태복음", ["Matt", "Mat", "Mt"], ["마"], 28),
    ("Mark", "마가복음", ["Mrk", "Mk", "Mr"], ["막"], 16),
    ("Luke", "누가복음", ["Luk", "Lk"], ["눅"], 24),
    ("John", "요한복음", ["Jn", "Jhn"], ["요"], 21),
    ("Acts", "사도행전", ["Ac"], ["행"], 28),
    ("Romans", "로마서", ["Rom", "Ro", "Rm"], ["롬"], 16),
    ("1 Corinthians", "고린도전서", ["1 Cor", "1Cor", "1 Co", "1Co"], ["고전"], 16),
    ("2 Corinthians", "고린도후서", ["2 Cor", "2Cor", "2 Co", "2Co"], ["고후"], 13),
    ("Galatians", "갈라디아서", ["Gal", "Ga"], ["갈"], 6),
    ("Ephesians", "에베소서", ["Eph", "Ephes"], ["엡"], 6),
    ("Philippians", "빌립보서", ["Phil", "Php", "Pp"], ["빌"], 4),
    ("Colossians", "골로새서", ["Col"], ["골"], 4),
    ("1 Thessalonians", "데살로니가전서", ["1 Thess", "1Thess", "1 Th", "1Th"], ["살전"], 5),
    ("2 Thessalonians", "데살로니가후서", ["2 Thess", "2Thess", "2 Th", "2Th"], ["살후"], 3),
    ("1 Timothy", "디모데전서", ["1 Tim", "1Tim", "1 Ti", "1Ti"], ["딤전"], 6),
    ("2 Timothy", "디모데후서", ["2 Tim", "2Tim", "2 Ti", "2Ti"], ["딤후"], 4),
    ("Titus", "디도서", ["Tit"], ["딛"], 3),
    ("Philemon", "빌레몬서", ["Phlm", "Phm", "Pm"], ["몬"], 1),
    ("Hebrews", "히브리서", ["Heb"], ["히"], 13),
    ("James", "야고보서", ["Jas", "Jm"], ["약"], 5),
    ("1 Peter", "베드로전서", ["1 Pet", "1Pet", "1 Pe", "1Pe"], ["벧전"], 5),
    ("2 Peter", "베드로후서", ["2 Pet", "2Pet", "2 Pe", "2Pe"], ["벧후"], 3),
    ("1 John", "요한일서", ["1 Jn", "1Jn", "1 Jo", "1Jo"], ["요일"], 5),
    ("2 John", "요한이서", ["2 Jn", "2Jn", "2 Jo", "2Jo"], ["요이"], 1),
    ("3 John", "요한삼서", ["3 Jn", "3Jn", "3 Jo", "3Jo"], ["요삼"], 1),
    ("Jude", "유다서", [], ["유"], 1),
    ("Revelation", "요한계시록", ["Rev", "Re", "Apoc"], ["계"], 22),
]


def book_names_ko() -> list[str]:
    return [ko for _, ko, _, _, _ in BOOKS]


def lookup_by_ko(ko: str) -> tuple[str, str, int] | None:
    for en, k, _, _, chapters in BOOKS:
        if k == ko:
            return (en, k, chapters)
    return None


def book_chapters(book_en: str) -> int:
    for en, _, _, _, chapters in BOOKS:
        if en == book_en:
            return chapters
    raise KeyError(book_en)
