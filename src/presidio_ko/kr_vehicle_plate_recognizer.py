from presidio_analyzer import Pattern

from ._common import END, START, KoreanPatternRecognizer

_REGION = (
    "서울|부산|대구|인천|광주|대전|울산|세종|경기|강원"
    "|충북|충남|전북|전남|경북|경남|제주"
)
_USE = "가나다라마거너더러머버서어저고노도로모보소오조구누두루무부수우주바사아자배하허"


class KrVehiclePlateRecognizer(KoreanPatternRecognizer):
    ENTITY = "KR_VEHICLE_PLATE"

    PATTERNS = [
        Pattern(
            "KR Vehicle Plate",
            rf"(?:(?:{_REGION})\s?)?{START}\d{{2,3}}\s?[{_USE}]\s?\d{{4}}{END}(?!원)",
            0.5,
        )
    ]

    CONTEXT = ["차량", "차량번호", "번호판", "자동차", "주차"]
