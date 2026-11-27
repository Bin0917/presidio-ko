import heapq
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult

FULL_WIDTH = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}

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

GAP = r"[	\p{Zs}]{0,3}"
COLON_GAP = rf"(?:[:：]{GAP})?"

DASH = r"[\p{Pd}\u2212]"
START = rf"(?<!\d)(?<!\d{DASH})"
END = rf"(?!{DASH}?\d)"


def drop_overlaps(results: List[RecognizerResult]) -> List[RecognizerResult]:
    merged: List[RecognizerResult] = []
    for r in sorted(results, key=lambda r: (r.entity_type, r.start)):
        m = merged[-1] if merged else None
        if m and m.entity_type == r.entity_type and r.start < m.end:
            merged[-1] = _cut(m, m.start, max(m.end, r.end), max(m.score, r.score))
        else:
            merged.append(r)
    heap = [(r.start, -r.end, i, r) for i, r in enumerate(merged)]
    heapq.heapify(heap)
    count = len(heap)
    kept: List[RecognizerResult] = []
    while heap:
        r = heapq.heappop(heap)[3]
        k = kept[-1] if kept else None
        if k is None or k.end <= r.start:
            kept.append(r)
        elif r.end <= k.end:
            if (r.start, r.end) == (k.start, k.end) and r.score > k.score:
                kept[-1] = r
        elif (r.score, r.end - r.start) > (k.score, k.end - k.start):
            kept[-1] = _cut(k, k.start, r.start, k.score)
            kept.append(r)
        else:
            heapq.heappush(heap, (k.end, -r.end, count, _cut(r, k.end, r.end, r.score)))
            count += 1
    return kept


def _cut(r: RecognizerResult, start: int, end: int, score: float) -> RecognizerResult:
    return RecognizerResult(r.entity_type, start, end, score)


class KoreanPatternRecognizer(PatternRecognizer):
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
