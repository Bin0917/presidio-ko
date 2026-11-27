from presidio_analyzer import Pattern

from ._common import DASH, END, START, KoreanPatternRecognizer

_GAP = r"[\t\p{Zs}]"
_SEP = rf"(?:{_GAP}*(?:{DASH}|[.·ㆍ・]){_GAP}*|{_GAP}+)"
_TRUNK = rf"(?:0|(?:\+82|\(\+82\)){_SEP}?(?:\(0\){_GAP}*|0)?)"
_MOBILE = r"1[016789]"
_AREA = r"(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4]|70|50[2-8])"
_LOCAL = rf"\d{{3,4}}{_SEP}\d{{4}}"
_PAREN = rf"(?:\(|{START}(?<!\())0"
_PAREN_CLOSE = rf"\){_GAP}*(?:{DASH}{_GAP}*)?"


class KrPhoneRecognizer(KoreanPatternRecognizer):
    ENTITY = "KR_PHONE"

    PATTERNS = [
        Pattern(
            "KR Mobile Phone",
            START
            + _TRUNK
            + _MOBILE
            + rf"(?:{_SEP}\d{{3,4}}{_SEP}?|\d{{3,4}}{_SEP})\d{{4}}"
            + END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (no separator)",
            START + r"(?<![A-Za-z])" + _TRUNK + _MOBILE + r"\d{7,8}" + END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (parenthesized)",
            _PAREN + _MOBILE + _PAREN_CLOSE + _LOCAL + END,
            0.5,
        ),
        Pattern(
            "KR Landline Phone",
            START + _TRUNK + _AREA + _SEP + _LOCAL + END,
            0.4,
        ),
        Pattern(
            "KR Landline Phone (parenthesized)",
            _PAREN + _AREA + _PAREN_CLOSE + _LOCAL + END,
            0.4,
        ),
    ]

    CONTEXT = [
        "전화",
        "연락처",
        "휴대폰",
        "핸드폰",
        "팩스",
        "안심번호",
        "phone",
        "mobile",
        "tel",
        "hp",
        "fax",
    ]
