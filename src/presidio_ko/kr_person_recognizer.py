import regex
from presidio_analyzer import EntityRecognizer, RecognizerResult

# 한국어 spaCy 모델은 "김민수님의"처럼 조사까지 붙여 인물(PS)로 잡는다.
# 이름 뒤의 조사·호칭을 떼고, 성씨와 길이로 이름인지 다시 확인한다.
_SURNAMES = set(
    "김이박최정강조윤장임한오서신권황안송류유홍전고문양손배백허남심노하곽성차주우구민나진지엄채원천방공현"
    "함변염여추도소석선설마길연위표명기반왕금옥육인맹제모탁국어은편용예경봉사부독"
)
_PARTICLES = [
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "의",
    "와",
    "과",
    "도",
    "만",
    "께",
    "로",
]
_SUFFIXES = sorted(
    {"님", "씨"}
    | {t + p for t in ("님", "씨") for p in _PARTICLES}
    | set(_PARTICLES)
    | {"에게서", "에게", "한테", "께서", "에서", "으로", "이고요", "이고", "이며"}
    | {"입니다", "이에요", "이다"},
    key=len,
    reverse=True,
)
# 성씨로 시작하는 양식 라벨(임대인, 이체일시)이 이름으로 잡히지 않게 한다
_FIELD_WORDS = set(
    """주문번호 송장번호 이체일시 임대인 임차인 사원명 서명 성명 대표 고객 이름
    성함 이체 이메일 주소 주민 송금 계좌 담당자 수신인 대표자 환자명 보호자
    근로자 사용자 상담사 수령인 문의 이용자 입금 출금 거래 금액 일시 번호
    사원 환자 보호 근로 임대 임차 주문 송장 고객명 연락처 연락 전화번호 휴대폰
    핸드폰 신한 국민 우리 하나 기업 신협 우체국 신용""".split()
)
_LABELED = regex.compile(
    r"(?:성명|이름|예금주|고객명|대표자|대표이사|담당자|수신인|받는\s?분|보내는\s?분"
    r"|임대인|임차인|근로자|환자명|보호자)[은는]?"
    r"(?:[ \t]{1,3}(?:성명|이름|성함))?[ \t]{0,3}(?:[:：][ \t]{0,3})?([가-힣]+)"
)
# spaCy가 "유성구" 같은 지명을 인물로 잡는다. 라벨 뒤 이름에는 적용하지 않는다
_PLACE_ENDINGS = ("시", "군", "구")
_PS_LABELS = {"PS", "PERSON"}


def _strip_suffix(word: str) -> str:
    # 한 글자 조사는 이름 끝 글자와 구별되지 않아("박하은") 세 글자 이상 남을 때만 뗀다
    for suffix in _SUFFIXES:
        keep = 3 if len(suffix) == 1 else 2
        if word.endswith(suffix) and len(word) - len(suffix) >= keep:
            return word[: -len(suffix)]
    return word


def _is_name(word: str) -> bool:
    return (
        regex.fullmatch(r"[가-힣]{2,4}", word) is not None
        and word[0] in _SURNAMES
        and word not in _FIELD_WORDS
    )


class KrPersonRecognizer(EntityRecognizer):
    """
    한국어 이름(PERSON)을 인식한다.

    - 이름 라벨(성명, 예금주, 임대인 등) 바로 뒤의 한글 2~4자: 0.85. spaCy 없이도 된다.
    - spaCy 한국어 모델이 인물(PS)로 잡은 말에서 조사를 뗀 이름: 0.6.

    같은 범위는 높은 점수 하나만 남긴다. 영문으로 쓴 외국인 이름은 잡지 않는다.
    """

    ENTITY = "PERSON"

    def __init__(self, supported_language: str = "ko", name: str | None = None):
        super().__init__(
            supported_entities=[self.ENTITY],
            supported_language=supported_language,
            name=name,
        )

    def load(self) -> None:
        pass

    def analyze(self, text, entities, nlp_artifacts=None):
        if self.ENTITY not in entities:
            return []
        spans = {}
        entities_found = nlp_artifacts.entities if nlp_artifacts is not None else []
        for ent in entities_found:
            if ent.label_ in _PS_LABELS:
                name = _strip_suffix(ent.text.strip())
                if _is_name(name) and not name.endswith(_PLACE_ENDINGS):
                    start = ent.start_char + ent.text.index(name)
                    spans[start, start + len(name)] = 0.6
        for match in _LABELED.finditer(text):
            name = _strip_suffix(match.group(1))
            if _is_name(name):
                start = match.start(1)
                spans[start, start + len(name)] = 0.85
        return [
            RecognizerResult(self.ENTITY, start, end, score)
            for (start, end), score in spans.items()
        ]
