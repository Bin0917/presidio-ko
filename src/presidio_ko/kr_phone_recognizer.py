from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class KrPhoneRecognizer(PatternRecognizer):
    """
    한국 전화번호(휴대폰, 지역번호 유선전화)를 인식한다.

    - 휴대폰: 010/011/016/017/018/019. 구분자(-, 공백)는 생략 가능.
    - 유선: 02, 031~033, 041~044, 051~055, 061~064 지역번호와 070 인터넷전화.
      구분자 없는 숫자열(0212345678)은 다른 번호와 구분이 어려워 구분자를 필수로 둔다.

    경계는 \\b 대신 숫자 lookaround를 쓴다. 한글도 \\w라서 "010-1234-5678로"처럼
    조사가 붙으면 "8"과 "로" 사이에 단어 경계가 없어 \\b로는 매칭이 깨진다.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    COUNTRY_CODE = "kr"

    PATTERNS = [
        Pattern(
            "KR Mobile Phone",
            r"(?<!\d)01[016789][-\s]?\d{3,4}[-\s]?\d{4}(?!\d)",
            0.5,
        ),
        Pattern(
            "KR Landline Phone",
            r"(?<!\d)0(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4]|70)[-\s]\d{3,4}[-\s]\d{4}(?!\d)",
            0.4,
        ),
    ]

    CONTEXT = ["전화", "연락처", "휴대폰", "핸드폰", "phone", "mobile"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ko",
        supported_entity: str = "KR_PHONE",
        name: Optional[str] = None,
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context else self.CONTEXT,
            supported_language=supported_language,
            name=name,
        )
