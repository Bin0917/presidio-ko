import re
from typing import Optional

from presidio_analyzer import Pattern

from ._common import COLON_GAP, DASH, END, GAP, START, KoreanPatternRecognizer

BANK_FORMATS = [
    (3, 2, 6),
    (3, 3, 6),
    (4, 3, 6),
    (6, 2, 6),
    (3, 6, 5),
    (4, 2, 7),
    (4, 4, 4),
    (3, 4, 4, 2),
    (3, 4, 4, 3),
    (3, 6, 2, 3),
    (3, 2, 6, 1),
]

_PHONE_SHAPES = {(3, 3, 4), (3, 4, 4), (4, 3, 4), (4, 4, 4)}
_MOBILE_PREFIXES = ("010", "011", "016", "017", "018", "019")

_START = START + r"(?<![A-Za-z])(?!(?<=\+)82)"
_KNOWN = "|".join(DASH.join(rf"[0-9]{{{n}}}" for n in shape) for shape in BANK_FORMATS)
_LABEL = (
    rf"(?<=(?:계좌(?:번호)?|은행|뱅크|예금주{GAP}\S{{1,10}})[은는]?{GAP}{COLON_GAP})"
)
_BANK_PREFIX = rf"(?<=(?:국민|신한|우리|하나|기업|산업|토스){GAP}{COLON_GAP})"


def _starts_with_date(groups):
    year, month, day = groups[:3]
    return (
        len(year) == 4
        and year[:2] in ("19", "20")
        and len(month) <= 2
        and 1 <= int(month) <= 12
        and len(day) <= 2
        and 1 <= int(day) <= 31
    )


class KrBankAccountRecognizer(KoreanPatternRecognizer):
    ENTITY = "KR_BANK_ACCOUNT"

    PATTERNS = [
        Pattern("KR Bank Account (known format)", _START + f"(?:{_KNOWN})" + END, 0.4),
        Pattern(
            "KR Bank Account (after bank name)",
            _BANK_PREFIX + _START + f"(?:{_KNOWN})" + END,
            0.6,
        ),
        Pattern(
            "KR Bank Account (other format)",
            _START + rf"[0-9]{{3,6}}(?:{DASH}[0-9]{{1,7}}){{2,3}}" + END,
            0.1,
        ),
        Pattern(
            "KR Bank Account (after label)",
            _LABEL + START + rf"[0-9]{{10,14}}{END}",
            0.4,
        ),
        Pattern(
            "KR Bank Account (space separated, after label)",
            _LABEL
            + START
            + r"[0-9]{3,6}(?:[	\p{Zs}][0-9]{2,7}){2,3}"
            + END
            + r"(?![	\p{Zs}]\d)",
            0.4,
        ),
    ]

    CONTEXT = [
        "계좌",
        "계좌번호",
        "은행",
        "입금",
        "account",
        "bank",
        "농협",
        "수협",
        "신협",
        "우체국",
        "새마을",
        "카카오뱅크",
        "케이뱅크",
        "토스뱅크",
        "SC제일",
        "씨티",
        "예금주",
        "뱅크",
        "송금",
        "이체",
        "환불",
    ]

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        groups = re.split(r"\D", pattern_text)
        shape = tuple(len(group) for group in groups)
        digits = sum(shape)
        if not 10 <= digits <= 14:
            return False
        if (len(groups) >= 3 and _starts_with_date(groups)) or shape == (3, 2, 5):
            return False
        if pattern_text[0] == "0" and (shape in _PHONE_SHAPES or len(shape) == 1):
            return False
        if (
            pattern_text.startswith(_MOBILE_PREFIXES)
            and len(shape) == 3
            and digits <= 11
        ):
            return False
        return None
