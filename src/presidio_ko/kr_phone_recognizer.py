from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

# 전각 숫자·＋·괄호를 ASCII로 바꾼다. 패턴의 0·1·+ 리터럴과 계좌 필터의 "0" 비교는
# ASCII만 보므로, 그대로 두면 전각 전화번호가 계좌로 잡힌다.
# 한 글자씩 바꾸므로 결과 위치가 원문과 같다
FULL_WIDTH = str.maketrans("０１２３４５６７８９＋（）", "0123456789+()")

# 대시: 유니코드 대시(\p{Pd}: 하이픈, en dash 등)와 OCR에 섞이는 빼기 기호(U+2212).
# Presidio는 패턴을 regex 모듈로 컴파일하므로 \p{...}를 쓸 수 있다
DASH = r"[\p{Pd}−]"
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
_END = rf"(?!{DASH}?\d)"
_LOCAL = rf"\d{{3,4}}{_SEP}\d{{4}}"
# 괄호 지역번호: (02) 123-4567, 02)123-4567
_PAREN = r"(?:\(|(?<![\d(]))0"


class KrPhoneRecognizer(PatternRecognizer):
    r"""
    한국 전화번호(휴대폰, 지역번호 유선전화, 안심번호)를 인식한다.

    - 휴대폰: 010/011/016/017/018/019. 구분자는 생략 가능.
    - 유선: 02, 031~033, 041~044, 051~055, 061~064 지역번호, 070 인터넷전화,
      0502~0508 안심번호. 구분자 없는 숫자열(0212345678)은 다른 번호와 구분이
      어려워 구분자를 필수로 둔다.
    - 괄호 지역번호도 받는다: (02) 123-4567, (010) 1234-5678, 02)123-4567.
    - 앞자리 0 대신 국제 형식도 받는다: +82 10-1234-5678, +82 010-1234-5678,
      +82 (0)10-1234-5678, (+82) 10-1234-5678.
    - 구분자: 대시(유니코드 대시와 빼기 기호 U+2212), 점, 가로 공백. 대시·점 앞뒤의
      공백도 허용한다(010 - 1234 - 5678). 줄바꿈은 구분자로 보지 않는다.
    - 080 수신자부담, 15XX·16XX·18XX 대표번호는 개인 연락처가 아니라서 잡지 않는다.

    경계는 \b 대신 lookaround를 쓴다. 한글도 \w라서 "010-1234-5678로"처럼 조사가
    붙으면 "8"과 "로" 사이에 단어 경계가 없어 \b로는 매칭이 깨진다. 앞에 숫자나
    "숫자+대시"가 붙거나 뒤에 대시·숫자가 이어지면(더 긴 번호의 일부) 제외한다. 앞에
    영문자가 바로 붙은 경우는 구분자 없는 번호만 제외한다("ORD01012345678"은 ID,
    "HP010-1234-5678"은 전화번호).

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    COUNTRY_CODE = "kr"

    PATTERNS = [
        Pattern(
            "KR Mobile Phone",
            _START
            + _TRUNK
            + _MOBILE
            + rf"(?:{_SEP}\d{{3,4}}(?:{_SEP})?|\d{{3,4}}{_SEP})\d{{4}}"
            + _END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (no separator)",
            rf"(?<![\dA-Za-z])(?<!\d{DASH})" + _TRUNK + _MOBILE + r"\d{7,8}" + _END,
            0.5,
        ),
        Pattern(
            "KR Mobile Phone (parenthesized)",
            _PAREN + _MOBILE + rf"\){_GAP}*" + _LOCAL + _END,
            0.5,
        ),
        Pattern(
            "KR Landline Phone",
            _START + _TRUNK + _AREA + _SEP + _LOCAL + _END,
            0.4,
        ),
        Pattern(
            "KR Landline Phone (parenthesized)",
            _PAREN + _AREA + rf"\){_GAP}*" + _LOCAL + _END,
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

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        return super().analyze(
            text.translate(FULL_WIDTH), entities, nlp_artifacts, regex_flags
        )
