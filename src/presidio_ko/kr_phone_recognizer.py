from presidio_analyzer import Pattern

from ._common import DASH, END, KoreanPatternRecognizer

# 가로 공백만 구분자로 본다. 줄바꿈까지 받으면 표의 열처럼 줄마다 따로 적힌 숫자가
# 하나의 번호로 이어진다
_GAP = r"[\t\p{Zs}]"
# 숫자 묶음 사이 구분자: 대시·점(앞뒤 공백 허용) 또는 공백
_SEP = rf"(?:{_GAP}*(?:{DASH}|\.){_GAP}*|{_GAP}+)"
# 앞자리 0, 또는 국제 형식 +82 / (+82) 뒤에 0, (0)을 남기거나 생략한 것
_TRUNK = rf"(?:0|(?:\+82|\(\+82\)){_SEP}?(?:\(0\){_GAP}*|0)?)"
_MOBILE = r"1[016789]"
# 지역번호, 070 인터넷전화, 0502~0508 안심번호
_AREA = r"(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4]|70|50[2-8])"
_START = rf"(?<!\d)(?<!\d{DASH})"
_LOCAL = rf"\d{{3,4}}{_SEP}\d{{4}}"
# 괄호 지역번호: (02) 123-4567, 02)123-4567
_PAREN = rf"(?:\(|(?<![\d(])(?<!\d{DASH}))0"
_PAREN_CLOSE = rf"\){_GAP}*"


class KrPhoneRecognizer(KoreanPatternRecognizer):
    r"""
    한국 전화번호(휴대폰, 지역번호 유선전화, 안심번호)를 인식한다.

    - 휴대폰 010/011/016/017/018/019는 구분자를 생략해도 받는다.
    - 유선(지역번호, 070, 0502~0508 안심번호)은 구분자가 있어야 한다.
      구분자 없는 0212345678은 다른 숫자열과 구분하기 어렵다.
    - 괄호 지역번호와 국제 형식(+82, +82 (0), (+82))도 받는다.
    - 080 수신자부담과 15XX·16XX·18XX 대표번호는 개인 연락처가 아니라서 잡지 않는다.

    경계는 \b 대신 lookaround를 쓴다. 한글도 \w라서 "010-1234-5678로"처럼 조사가
    붙으면 \b가 성립하지 않는다. 앞에 숫자나 "숫자+대시"가 붙거나 뒤에 대시·숫자가
    이어지면 더 긴 번호의 일부로 보고 제외한다. 앞에 영문자가 바로 붙은 경우는 구분자
    없는 번호만 제외한다("ORD01012345678"은 ID, "HP010-1234-5678"은 전화번호).
    """

    ENTITY = "KR_PHONE"

    PATTERNS = [
        Pattern(
            "KR Mobile Phone",
            _START
            + _TRUNK
            + _MOBILE
            + rf"(?:{_SEP}\d{{3,4}}(?:{_SEP})?|\d{{3,4}}{_SEP})\d{{4}}"
            + END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (no separator)",
            rf"(?<![\dA-Za-z])(?<!\d{DASH})" + _TRUNK + _MOBILE + r"\d{7,8}" + END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (parenthesized)",
            _PAREN + _MOBILE + _PAREN_CLOSE + _LOCAL + END,
            0.5,
        ),
        Pattern(
            "KR Landline Phone",
            _START + _TRUNK + _AREA + _SEP + _LOCAL + END,
            0.4,
        ),
        Pattern(
            "KR Landline Phone (parenthesized)",
            _PAREN + _AREA + _PAREN_CLOSE + _LOCAL + END,
            0.4,
        ),
    ]

    # 명함·서류의 라벨(Tel., HP, Fax)도 넣는다. 강화기는 부분 문자열로 비교한다
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
