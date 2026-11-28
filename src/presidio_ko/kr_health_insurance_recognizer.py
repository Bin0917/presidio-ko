from presidio_analyzer import Pattern

from ._common import COLON_GAP, END, GAP, START, KoreanPatternRecognizer

_LABEL = (
    rf"(?<=(?:건강보험증?{GAP}번호|보험증{GAP}번호|건보{GAP}번호)"
    rf"[은는]?{GAP}{COLON_GAP})"
)


class KrHealthInsuranceRecognizer(KoreanPatternRecognizer):
    ENTITY = "KR_HEALTH_INSURANCE"

    PATTERNS = [
        Pattern(
            "KR Health Insurance Number",
            rf"{_LABEL}{START}[0-9]{{1,2}}-?[0-9]{{9,10}}{END}",
            0.6,
        )
    ]

    CONTEXT = ["건강보험", "보험증"]
