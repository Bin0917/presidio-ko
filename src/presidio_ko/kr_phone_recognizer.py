from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class KrPhoneRecognizer(PatternRecognizer):
    r"""
    한국 전화번호(휴대폰, 지역번호 유선전화)를 인식한다.

    - 휴대폰: 010/011/016/017/018/019. 구분자는 생략 가능.
    - 유선: 02, 031~033, 041~044, 051~055, 061~064 지역번호와 070 인터넷전화.
      구분자 없는 숫자열(0212345678)은 다른 번호와 구분이 어려워 구분자를 필수로 둔다.
    - 앞자리 0 대신 국제 형식 +82도 받는다(+82 10-1234-5678).
    - 구분자: 공백, 점, 유니코드 대시(\p{Pd}: 하이픈, en dash 등). PDF·OCR 추출문에는
      하이픈 대신 다른 대시가 섞여 나온다. Presidio는 패턴을 regex 모듈로 컴파일한다.

    경계는 \b 대신 lookaround를 쓴다. 한글도 \w라서 "010-1234-5678로"처럼 조사가
    붙으면 "8"과 "로" 사이에 단어 경계가 없어 \b로는 매칭이 깨진다. 대신 앞에 숫자나
    영문자가 붙은 경우(영숫자 ID)와 뒤에 대시·점과 숫자가 이어지는 경우(더 긴 번호의
    일부)는 제외한다.

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    COUNTRY_CODE = "kr"

    PATTERNS = [
        Pattern(
            "KR Mobile Phone",
            r"(?<![\dA-Za-z])(?:0|\+82[\p{Pd}\s.]?)"
            r"1[016789][\p{Pd}\s.]?\d{3,4}[\p{Pd}\s.]?\d{4}(?![\p{Pd}.]?\d)",
            0.5,
        ),
        Pattern(
            "KR Landline Phone",
            r"(?<![\dA-Za-z])(?:0|\+82[\p{Pd}\s.]?)"
            r"(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4]|70)"
            r"[\p{Pd}\s.]\d{3,4}[\p{Pd}\s.]\d{4}(?![\p{Pd}.]?\d)",
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
            context=context if context is not None else self.CONTEXT,
            supported_language=supported_language,
            name=name,
        )
