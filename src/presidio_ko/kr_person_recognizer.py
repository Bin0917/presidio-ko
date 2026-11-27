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
    r"|(?:사원|직원|주문자|구매자|신청자|작성자|가입자)명)(?:께서|[은는이가])?"
    r"(?:[ \t]{1,3}(?:성명|이름|성함))?[ \t]{0,3}(?:[:：][ \t]{0,3})?([가-힣]+)"
)
_DISTRICTS = set(
    """종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구
    은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구
    강남구 송파구 강동구 서구 동구 영도구 부산진구 동래구 남구 북구 해운대구 사하구
    금정구 연제구 수영구 사상구 기장군 수성구 달서구 달성군 군위군 미추홀구 연수구
    남동구 부평구 계양구 강화군 옹진군 광산구 유성구 대덕구 울주군 세종시
    수원시 장안구 권선구 팔달구 영통구 성남시 수정구 중원구 분당구 의정부시 안양시
    만안구 동안구 부천시 원미구 소사구 오정구 광명시 평택시 동두천시 안산시 상록구
    단원구 고양시 덕양구 일산동구 일산서구 과천시 구리시 남양주시 오산시 시흥시
    군포시 의왕시 하남시 용인시 처인구 기흥구 수지구 파주시 이천시 안성시 김포시
    화성시 만세구 효행구 병점구 동탄구 광주시 양주시 포천시 여주시 연천군 가평군
    양평군 춘천시 원주시 강릉시 동해시 태백시 속초시 삼척시 홍천군 횡성군 영월군
    평창군 정선군 철원군 화천군 양구군 인제군 고성군 양양군 청주시 상당구 서원구
    흥덕구 청원구 충주시 제천시 보은군 옥천군 영동군 증평군 진천군 괴산군 음성군
    단양군 천안시 동남구 서북구 공주시 보령시 아산시 서산시 논산시 계룡시 당진시
    금산군 부여군 서천군 청양군 홍성군 예산군 태안군 전주시 완산구 덕진구 군산시
    익산시 정읍시 남원시 김제시 완주군 진안군 무주군 장수군 임실군 순창군 고창군
    부안군 목포시 여수시 순천시 나주시 광양시 담양군 곡성군 구례군 고흥군 보성군
    화순군 장흥군 강진군 해남군 영암군 무안군 함평군 영광군 장성군 완도군 진도군
    신안군 포항시 경주시 김천시 안동시 구미시 영주시 영천시 상주시 문경시 경산시
    의성군 청송군 영양군 영덕군 청도군 고령군 성주군 칠곡군 예천군 봉화군 울진군
    울릉군 창원시 의창구 성산구 마산합포구 마산회원구 진해구 진주시 통영시 사천시
    김해시 밀양시 거제시 양산시 의령군 함안군 창녕군 남해군 하동군 산청군 함양군
    거창군 합천군 제주시 서귀포시""".split()
)
_PS_LABELS = {"PS", "PERSON"}
_RIEUL = 8


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


def _labeled_score(word: str, name: str) -> float | None:
    if len(name) == 2 and word != name:
        return 0.4
    if len(name) != 3:
        return 0.85
    final = (ord(name[1]) - 0xAC00) % 28
    if name[2] == "은" and final:
        return 0.4
    particles = "을이과에" if final else "를는가와로에"
    if name[2] in particles or (name[2] == "로" and final == _RIEUL):
        return None
    return 0.85


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
                if _is_name(name) and name not in _DISTRICTS:
                    start = ent.start_char + ent.text.index(name)
                    spans[start, start + len(name)] = 0.6
        for match in _LABELED.finditer(text):
            name = _strip_suffix(match.group(1))
            score = _labeled_score(match.group(1), name) if _is_name(name) else None
            if score is not None:
                span = match.start(1), match.start(1) + len(name)
                spans[span] = max(score, spans.get(span, 0))
        return [
            RecognizerResult(self.ENTITY, start, end, score)
            for (start, end), score in spans.items()
        ]
