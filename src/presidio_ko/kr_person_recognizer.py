import re

from presidio_analyzer import EntityRecognizer, RecognizerResult

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
    | set(_PARTICLES)
    | {"에게서", "에게", "한테", "께서", "에서", "으로", "이고요", "이고", "이며"}
    | {"입니다", "이에요", "예요", "이다", "라고", "이라고", "이세요", "이랑", "랑"},
    key=len,
    reverse=True,
)
_FIELD_WORDS = set(
    """고객 고객명 국민 금액 기업 김밥 김치 문의 사용자 사원
    사원명 서명 성명 성함 송금 송장 신용 신한 신협 연락 연락처
    우리 우체국 이름 이메일 이용자 이체 임대 임대인 임차 임차인
    조회 주문 주민 주소 하나 신청인 주소지 정보 변경 전화 한도
    지정 정지 정정""".split()
)
_COMPOUND_SURNAMES = ("남궁", "황보", "제갈", "선우", "서문", "독고", "사공")
_LABELED = re.compile(
    r"(?:성명|성함|이름|예금주|고객명|대표자|대표\s?이사|담당자|수신인|받는\s?분|보내는\s?분"
    r"|임대인|임차인|근로자|환자명|보호자|수령인|수취인|신청인|계약자|보증인|피보험자"
    r"|(?:사원|직원|주문자|구매자|신청자|작성자|가입자)명)[은는]?"
    r"(?:[ \t]{1,3}(?:성명|이름|성함))?[ \t]{0,3}(?:[:：][ \t]{0,3})?([가-힣]+)"
)
_PLACE_ENDINGS = ("시", "군", "구")
_PS_LABELS = {"PS", "PERSON"}


def _strip_suffix(word: str) -> str:
    for _ in range(3):
        for suffix in _SUFFIXES:
            keep = 3 if len(suffix) == 1 else 2
            if word.endswith(suffix) and len(word) - len(suffix) >= keep:
                word = word[: -len(suffix)]
                break
        else:
            break
    return word


def _is_field_word(word: str) -> bool:
    return word in _FIELD_WORDS or any(
        word.endswith(s) and word[: -len(s)] in _FIELD_WORDS for s in _SUFFIXES
    )


def _is_name(word: str) -> bool:
    return (
        re.fullmatch(r"[가-힣]{2,4}", word) is not None
        and word[0] in _SURNAMES
        and not _is_field_word(word)
        and (len(word) < 4 or word.startswith(_COMPOUND_SURNAMES))
    )


class KrPersonRecognizer(EntityRecognizer):
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
