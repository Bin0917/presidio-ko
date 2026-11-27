from presidio_analyzer import Pattern

from ._common import END, START, KoreanPatternRecognizer

# 형식이 공개 표준이 아니라서 라벨 바로 뒤의 10~12자리만 받는다
_LABEL = (
    r"(?<=(?:건강보험증?[\t\p{Zs}]?번호|보험증[\t\p{Zs}]?번호|건보[\t\p{Zs}]?번호)"
    r"[은는]?[\t\p{Zs}]*[:：]?[\t\p{Zs}]*)"
)


class KrHealthInsuranceRecognizer(KoreanPatternRecognizer):
    """ "건강보험증번호" 같은 라벨 뒤의 건강보험증 번호를 인식한다."""

    ENTITY = "KR_HEALTH_INSURANCE"

    PATTERNS = [
        Pattern(
            "KR Health Insurance Number",
            rf"{_LABEL}{START}[0-9]{{1,2}}-?[0-9]{{9,10}}{END}",
            0.6,
        )
    ]

    CONTEXT = ["건강보험", "보험증"]
