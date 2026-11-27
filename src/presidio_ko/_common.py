from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

# 전각 숫자·＋·괄호를 ASCII로 바꾼다. 패턴의 0·1·+ 리터럴과 계좌 필터의 "0" 비교는
# ASCII만 보므로, 그대로 두면 전각 전화번호가 계좌로 잡힌다.
# 한 글자씩 바꾸므로 결과 위치가 원문과 같다
FULL_WIDTH = str.maketrans("０１２３４５６７８９＋（）", "0123456789+()")

# 유니코드 대시(\p{Pd}: 하이픈, en dash 등)와 OCR에 섞이는 빼기 기호(U+2212).
# Presidio는 패턴을 regex 모듈로 컴파일하므로 \p{...}를 쓸 수 있다
DASH = r"[\p{Pd}\u2212]"
# 뒤에 대시·숫자가 이어지면 더 긴 번호의 일부다
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
