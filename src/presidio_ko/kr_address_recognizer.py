from presidio_analyzer import Pattern

from ._common import COLON_GAP, GAP, KoreanPatternRecognizer

_SIDO = (
    "서울특별시|서울시|서울|부산광역시|부산시|부산|대구광역시|대구시|대구|인천광역시|인천시|인천|광주광역시|광주"
    "|대전광역시|대전시|대전|울산광역시|울산시|울산|세종특별자치시|세종시|세종|경기도|경기|강원특별자치도|강원도|강원"
    "|충청북도|충북|충청남도|충남|전북특별자치도|전라북도|전북|전라남도|전남|경상북도|경북"
    "|경상남도|경남|제주특별자치도|제주도|제주"
)
_EUPMYEON = r"[가-힣]{1,5}[읍면]\s?"
_SIGUNGU = rf"(?:[가-힣]{{1,7}}(?:시|군|구)\s?){{1,2}}(?:{_EUPMYEON})?"
_NUMBER = r"\d+(?:-\d+)?"
_ROAD = rf"[가-힣0-9]{{1,12}}(?:로|길)(?:\s?\d+(?:번길|길))?\s?{_NUMBER}(?!번?길)"
_LOT = rf"[가-힣0-9]{{1,12}}(?:동|리|가)\s?산?\s?{_NUMBER}(?:번지)?"
_UNIT = (
    r"(?:(?:[A-Za-z]|에이|비|씨|디|\d+)동|(?:지하\s?)?\d+층|\d+호(?!선)"
    r"|\([^)\s]{1,10}동\))"
)
_NOT_NAME = r"(?![가-힣A-Za-z0-9]{0,15}[서는은을를의에고며와과도](?![가-힣A-Za-z0-9]))"
_BUILDING = (
    rf"(?:,?\s?{_NOT_NAME}[가-힣A-Za-z][가-힣A-Za-z0-9]{{1,14}}"
    rf"(?:\s{_NOT_NAME}[가-힣A-Za-z0-9]{{1,15}}){{0,2}}"
    r"\s?(?=(?:[A-Za-z]|\d+)동|\d+호(?!선)))?"
)
_DETAIL = rf"(?:,\s?\d{{1,4}}-\d{{1,4}}(?![\d-]))?{_BUILDING}(?:,?\s?{_UNIT})*"
_START = r"(?<![가-힣0-9])"
_LABEL = rf"(?<=(?:주소지?|소재지|수령지|배송지|거주지)[은는]?{GAP}{COLON_GAP})"
_HEAD = (
    rf"{_START}(?:(?:(?:{_SIDO})\s?|{_LABEL}){_SIGUNGU}"
    rf"|세종(?:특별자치시|시)?\s?{_EUPMYEON})"
)


class KrAddressRecognizer(KoreanPatternRecognizer):
    ENTITY = "KR_ADDRESS"

    PATTERNS = [
        Pattern("KR Address (road)", rf"{_HEAD}{_ROAD}{_DETAIL}(?!\d)", 0.6),
        Pattern("KR Address (lot)", rf"{_HEAD}{_LOT}{_DETAIL}(?!\d)", 0.5),
    ]

    CONTEXT = ["주소", "소재지", "수령지", "배송지", "거주지", "address"]
