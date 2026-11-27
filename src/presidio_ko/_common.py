from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

# 전각 숫자·＋·괄호를 ASCII로 바꾼다. 패턴의 0·1·+ 리터럴과 계좌 필터의 "0" 비교는
# ASCII만 보므로, 그대로 두면 전각 전화번호가 계좌로 잡힌다.
# 한 글자씩 바꾸므로 결과 위치가 원문과 같다
FULL_WIDTH = str.maketrans("０１２３４５６７８９＋（）", "0123456789+()")

# 가명 자리표시자에 쓰는 한국어 이름. 없는 엔티티는 엔티티 이름을 그대로 쓴다
ENTITY_LABELS = {
    "PERSON": "이름",
    "KR_PHONE": "전화번호",
    "KR_BANK_ACCOUNT": "계좌번호",
    "KR_ADDRESS": "주소",
    "KR_RRN": "주민등록번호",
    "KR_FRN": "외국인등록번호",
    "KR_BRN": "사업자등록번호",
    "KR_PASSPORT": "여권번호",
    "KR_DRIVER_LICENSE": "운전면허번호",
    "KR_VEHICLE_PLATE": "차량번호",
    "KR_HEALTH_INSURANCE": "건강보험증번호",
    "CREDIT_CARD": "카드번호",
    "EMAIL_ADDRESS": "이메일",
}

# 가변 길이 lookbehind 안의 공백은 길이를 제한한다. 무제한이면 긴 공백 입력에서
# 매칭 시간이 입력 길이의 제곱 이상으로 늘어난다
GAP = r"[	\p{Zs}]{0,3}"
COLON_GAP = rf"(?:[:：]{GAP})?"

# 유니코드 대시(\p{Pd}: 하이픈, en dash 등)와 OCR에 섞이는 빼기 기호(U+2212).
# Presidio는 패턴을 regex 모듈로 컴파일하므로 \p{...}를 쓸 수 있다
DASH = r"[\p{Pd}\u2212]"
# 앞에 숫자나 "숫자+대시"가 붙거나 뒤에 대시·숫자가 이어지면 더 긴 번호의 일부다
START = rf"(?<!\d)(?<!\d{DASH})"
END = rf"(?!{DASH}?\d)"


class KoreanPatternRecognizer(PatternRecognizer):
    """전각 숫자를 ASCII로 바꿔 검사하는 한국어 PatternRecognizer 공통 부분."""

    COUNTRY_CODE = "kr"
    ENTITY: str
    PATTERNS: List[Pattern]
    CONTEXT: List[str]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ko",
        supported_entity: Optional[str] = None,
        name: Optional[str] = None,
    ):
        super().__init__(
            supported_entity=supported_entity or self.ENTITY,
            patterns=patterns if patterns else self.PATTERNS,
            context=context if context is not None else self.CONTEXT,
            supported_language=supported_language,
            name=name,
        )

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        return super().analyze(
            text.translate(FULL_WIDTH), entities, nlp_artifacts, regex_flags
        )
