from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class KrBankAccountRecognizer(PatternRecognizer):
    """
    하이픈으로 표기한 한국 은행 계좌번호를 인식한다.

    정규식은 하이픈으로 이어진 3~4개 숫자 그룹을 넓게 찾고, validate_result가 그룹별
    자릿수를 은행별 표기 형식(BANK_FORMATS)과 대조한다. 날짜(4-2-2), 사업자등록번호(3-2-5),
    전화번호(3-4-4 등)는 목록에 없는 모양이라 걸러진다.

    계좌번호 체크섬은 은행마다 다르고 공개돼 있지 않아 검증할 수 없다. 그래서 형식이 맞아도
    점수를 올리지 않고(0.4 유지) 주변에 "계좌", "은행" 같은 단어가 있을 때만 올린다.
    같은 모양의 주문번호·문서번호는 계좌로 오탐될 수 있다.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    COUNTRY_CODE = "kr"

    # 은행별 하이픈 표기 형식(그룹별 자릿수). 3그룹 형식은 모두 마지막 그룹이 4자리 이상이다.
    BANK_FORMATS = {
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
    }

    PATTERNS = [
        Pattern(
            "KR Bank Account (hyphenated)",
            r"(?<![\d-])\d{3,6}(?:-\d{1,7}){2,3}(?![\d-])",
            0.4,
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
        그룹별 자릿수가 은행 표기 형식과 맞는지만 확인한다.

        형식이 맞아도 True가 아닌 None을 돌려준다. PatternRecognizer는 True를 받으면 점수를
        1.0으로 올리는데, 체크섬 없는 형식 검증만으로는 그만큼 확신할 수 없기 때문이다.

        :param pattern_text: the text to validated.
        Only the part in text that was detected by the regex engine
        :return: None if the format is known, False otherwise.
        """
        shape = tuple(len(group) for group in pattern_text.split("-"))
        return None if shape in self.BANK_FORMATS else False
