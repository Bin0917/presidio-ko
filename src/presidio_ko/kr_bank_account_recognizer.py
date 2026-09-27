import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

# 은행별 하이픈 표기 형식(그룹별 자릿수). 출처는 README 참고.
BANK_FORMATS = [
    (3, 2, 6),  # 신한(구)·SC제일·대구
    (3, 3, 6),  # 신한·케이뱅크·신협·제주
    (4, 3, 6),  # 우리·광주
    (6, 2, 6),  # KB국민·우체국
    (3, 6, 5),  # 하나
    (4, 2, 7),  # 카카오뱅크
    (4, 4, 4),  # 토스뱅크·수협
    (3, 4, 4, 2),  # NH농협·부산
    (3, 4, 4, 3),  # KDB산업
    (3, 6, 2, 3),  # IBK기업
    (3, 2, 6, 1),  # 대구
]

# 0으로 시작하는 이 모양은 전화번호(0XX-XXXX-XXXX)나 050X 안심번호다
_PHONE_SHAPES = {(3, 3, 4), (3, 4, 4), (4, 3, 4), (4, 4, 4)}

# 숫자·영문자 바로 뒤, "숫자+대시" 뒤에서는 시작하지 않고(더 긴 번호·ID의 일부)
# 대시+숫자가 이어지면 끝나지 않는다. "신한-110-..."처럼 문자+대시 뒤는 허용한다.
# \p{Pd}는 하이픈·en dash 등 유니코드 대시 (Presidio는 패턴을 regex 모듈로 컴파일)
_START = r"(?<![\dA-Za-z])(?<!\d\p{Pd})"
_END = r"(?!\p{Pd}?\d)"
# 예: (3, 3, 6) → \d{3}\p{Pd}\d{3}\p{Pd}\d{6}
_KNOWN = "|".join(r"\p{Pd}".join(rf"\d{{{n}}}" for n in shape) for shape in BANK_FORMATS)


class KrBankAccountRecognizer(PatternRecognizer):
    """
    하이픈으로 표기한 한국 은행 계좌번호를 인식한다.

    - 은행별 표기 형식(BANK_FORMATS)과 그룹 자릿수가 맞으면 0.4
    - 그 밖의 3~4그룹 숫자열은 형식표에 없는 실제 계좌일 수 있어 0.1로 남긴다
    - validate_result가 계좌일 수 없는 모양을 걸러낸다: 10~14자리가 아닌 것(날짜·카드번호),
      날짜로 시작하는 것, 사업자등록번호(3-2-5), 0으로 시작하는 전화번호 모양

    계좌번호 체크섬은 은행마다 다르고 공개돼 있지 않아 검증할 수 없다. 그래서 형식이 맞아도
    점수를 올리지 않고 주변에 "계좌", "은행" 같은 단어가 있을 때만 올린다. 같은 모양의
    주문번호·문서번호는 계좌로 오탐될 수 있다.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    COUNTRY_CODE = "kr"

    PATTERNS = [
        Pattern("KR Bank Account (known format)", _START + f"(?:{_KNOWN})" + _END, 0.4),
        Pattern(
            "KR Bank Account (other format)",
            _START + r"\d{3,6}(?:\p{Pd}\d{1,7}){2,3}" + _END,
            0.1,
        ),
    ]

    CONTEXT = ["계좌", "계좌번호", "은행", "입금", "account", "bank"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ko",
        supported_entity: str = "KR_BANK_ACCOUNT",
        name: Optional[str] = None,
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
            name=name,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        계좌번호일 수 없는 모양만 걸러낸다.

        통과해도 True가 아닌 None을 돌려준다. PatternRecognizer는 True를 받으면 점수를
        1.0으로 올리는데, 체크섬 없는 형식 검증만으로는 그만큼 확신할 수 없기 때문이다.

        :param pattern_text: the text to validated.
        Only the part in text that was detected by the regex engine
        :return: False if it cannot be an account number, None otherwise.
        """
        shape = tuple(len(group) for group in re.split(r"\D", pattern_text))
        if not 10 <= sum(shape) <= 14:
            return False
        if shape[:3] == (4, 2, 2) or shape == (3, 2, 5):
            return False  # 날짜(YYYY-MM-DD…), 사업자등록번호
        if pattern_text[0] == "0" and shape in _PHONE_SHAPES:
            return False
        return None
