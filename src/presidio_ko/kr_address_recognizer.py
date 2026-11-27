from presidio_analyzer import Pattern

from ._common import KoreanPatternRecognizer

# 정식 명칭이 약칭을 포함하므로 긴 것을 앞에 둔다
_SIDO = (
    "서울특별시|서울시|서울|부산광역시|부산|대구광역시|대구|인천광역시|인천|광주광역시|광주"
    "|대전광역시|대전|울산광역시|울산|세종특별자치시|세종|경기도|경기|강원특별자치도|강원도|강원"
    "|충청북도|충북|충청남도|충남|전북특별자치도|전라북도|전북|전라남도|전남|경상북도|경북"
    "|경상남도|경남|제주특별자치도|제주도|제주"
)
_SIGUNGU = r"(?:[가-힣]{1,7}(?:시|군|구)\s?){1,2}"
_NUMBER = r"\d+(?:-\d+)?"
_ROAD = rf"[가-힣0-9]{{1,12}}(?:로|길)\s?{_NUMBER}"
_LOT = rf"[가-힣0-9]{{1,12}}(?:동|리|가)\s?산?\s?{_NUMBER}(?:번지)?"
# 건물명은 경계가 모호해 넣지 않는다
_DETAIL = r"(?:,?\s*(?:\d+동|\d+층|\d+호|\([^)\s]+동\)))*"
_START = r"(?<![가-힣0-9])"


class KrAddressRecognizer(KoreanPatternRecognizer):
    """
    한국 주소를 인식한다. 시도(생략 가능) + 시군구 + 도로명·건물번호 또는 지번에
    동·층·호 상세가 이어진 부분까지다. 지번 주소는 시도가 있어야 한다.
    """

    ENTITY = "KR_ADDRESS"

    PATTERNS = [
        Pattern(
            "KR Address (road)",
            rf"{_START}(?:(?:{_SIDO})\s?)?{_SIGUNGU}{_ROAD}{_DETAIL}(?!\d)",
            0.6,
        ),
        Pattern(
            "KR Address (lot)",
            rf"{_START}(?:{_SIDO})\s?{_SIGUNGU}{_LOT}{_DETAIL}(?!\d)",
            0.5,
        ),
    ]

    CONTEXT = ["주소", "소재지", "수령지", "배송지", "거주지", "address"]
