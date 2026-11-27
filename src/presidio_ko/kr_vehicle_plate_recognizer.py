from presidio_analyzer import Pattern

from ._common import END, START, KoreanPatternRecognizer

_REGION = (
    "서울|부산|대구|인천|광주|대전|울산|세종|경기|강원"
    "|충북|충남|전북|전남|경북|경남|제주"
)
# 자가용·사업용·렌터카 용도문자. 호는 호수("101호 1234")와 구별되지 않아 뺀다
_USE = "가나다라마거너더러머버서어저고노도로모보소오조구누두루무부수우주바사아자배하허"


class KrVehiclePlateRecognizer(KoreanPatternRecognizer):
    """한국 자동차 번호판(12가 3456, 123가 4567, 서울12가3456)을 인식한다."""

    ENTITY = "KR_VEHICLE_PLATE"

    PATTERNS = [
        Pattern(
            "KR Vehicle Plate",
            rf"(?:(?:{_REGION})\s?)?{START}\d{{2,3}}\s?[{_USE}]\s?\d{{4}}{END}(?!원)",
            0.5,
        )
    ]

    CONTEXT = ["차량", "차량번호", "번호판", "자동차", "주차"]
