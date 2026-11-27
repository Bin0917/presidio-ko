import pytest

from presidio_ko import KrPersonRecognizer

recognizer = KrPersonRecognizer()


def labeled(text):
    return [
        (text[r.start : r.end], r.score) for r in recognizer.analyze(text, ["PERSON"])
    ]


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("성명: 한지민 (생년월일 1995. 6. 12.)", "한지민"),
        ("예금주는 최서연입니다", "최서연"),
        ("받는 분: 강다은  입금계좌", "강다은"),
        ("보내는분 오세훈", "오세훈"),
        ("임대인 조현우 (주민등록번호", "조현우"),
        ("담당자：남궁민수", "남궁민수"),
        ("환자명: 송하윤", "송하윤"),
        ("예금주 박하은", "박하은"),
        ("보호자 성명: 최수진", "최수진"),
        ("임대인 성명 김철수", "김철수"),
        ("담당자 이름: 박영희", "박영희"),
        ("수령인: 장하늘", "장하늘"),
        ("수취인 김민수", "김민수"),
        ("신청인: 박보검", "박보검"),
        ("성함: 김민수", "김민수"),
        ("계약자 손흥민", "손흥민"),
        ("보증인 성명 이도현", "이도현"),
        ("피보험자 윤서아", "윤서아"),
        ("주문자명: 정해인", "정해인"),
        ("사원명: 이지은", "이지은"),
        ("대표 이사 김철수", "김철수"),
        ("성명: 주민호", "주민호"),
        ("수취인 김민수를 확인", "김민수"),
    ],
)
def test_label_gives_high_score(text, name):
    assert labeled(text) == [(name, 0.85)]


@pytest.mark.parametrize(
    "text",
    [
        "성명: 가나다",
        "성명: 홍",
        "임차인 임대인",
        "이름: 이체일시",
        "성명:\n김민수",
        "주문번호 송장번호 이체일시 사원명 서명",
        "수령인 정보 입력",
        "수령인 변경",
        "수령인 정보를 다시 입력해주세요",
        "신청인 주소가 바뀌었습니다",
        "성명 변경을 신청합니다",
        "계약자 전화는 받지 않습니다",
        "담당자 조회를 눌러 주세요",
        "보증인 한도를 확인하세요",
        "수취인 지정을 해제",
        "예금주 정정을 요청",
        "가입자명 정지를 해제",
        "성함 서명을 받으세요",
    ],
)
def test_label_without_a_person_gives_nothing(text):
    assert labeled(text) == []


def found(analyzer, text):
    results = analyzer.analyze(text=text, language="ko", entities=["PERSON"])
    return [(text[r.start : r.end], r.score) for r in results]


def test_spacy_person_strips_particles(korean_analyzer):
    assert found(korean_analyzer, "김민수님의 주소는 서울입니다") == [("김민수", 0.6)]
    assert found(korean_analyzer, "회의에서 박지성이 발표했다") == [("박지성", 0.6)]


def test_label_and_spacy_on_same_name_report_once(korean_analyzer):
    assert found(korean_analyzer, "예금주는 최서연") == [("최서연", 0.85)]


def test_field_labels_are_not_people(korean_analyzer):
    text = (
        "주문번호 2026-1103 송장번호 6543 임대인 조현우 임차인 윤성호 이체일시 사원명"
    )
    assert [name for name, _ in found(korean_analyzer, text)] == ["조현우", "윤성호"]


def test_romanized_foreign_name_is_out_of_scope(korean_analyzer):
    assert found(korean_analyzer, "임차인 Nguyen Van An 입니다") == []


def test_other_field_labels_after_a_name_label_are_not_people():
    assert labeled("보호자 연락처: 010-6543-2109") == []


def test_form_labels_tagged_by_spacy_are_not_people(korean_analyzer):
    assert found(korean_analyzer, "신청인: 박보검") == [("박보검", 0.85)]
    assert found(korean_analyzer, "주소지 광주광역시 북구 용봉로 77") == []


def test_bank_names_and_districts_are_not_people(korean_analyzer):
    assert found(korean_analyzer, "엄마: 용돈 보냈다 신한 110-234-567890 맞지?") == []
    assert found(korean_analyzer, "주소 대전광역시 유성구 대학로 99") == []


@pytest.mark.parametrize(
    "text",
    [
        "김치찌개 2인분 주문했어요.",
        "김밥천국에서 점심을 먹었다",
        "택배 송장번호 6123-4567-8901 조회",
        "주문번호 조회 김밥 먹자",
    ],
)
def test_foods_and_lookup_words_are_not_people(korean_analyzer, text):
    assert found(korean_analyzer, text) == []


def test_four_letter_names_need_a_compound_surname():
    assert labeled("성명: 남궁민수") == [("남궁민수", 0.85)]
    assert labeled("성명: 김치찌개") == []


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("고객명: 홍길동님께서 오셨습니다", "홍길동"),
        ("고객명: 홍길동님에게 연락", "홍길동"),
        ("예금주 홍길동씨에게 송금", "홍길동"),
        ("수취인 김민수씨한테 보냄", "김민수"),
        ("담당자 김민수님으로 변경", "김민수"),
        ("이름은 김민수라고 합니다", "김민수"),
        ("성명: 김민수예요", "김민수"),
        ("성명: 김민준이에요", "김민준"),
        ("성명: 김민수입니다", "김민수"),
        ("성명: 김민수이고 연락처는", "김민수"),
        ("성명: 김민준이며 주소는", "김민준"),
        ("성함: 김민수님이세요", "김민수"),
    ],
)
def test_honorific_and_ending_are_stripped_together(text, name):
    assert labeled(text) == [(name, 0.85)]


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("어제 김민수님께서 방문하셨습니다.", "김민수"),
        ("김민수씨에게 연락했습니다.", "김민수"),
    ],
)
def test_spacy_person_strips_honorific_and_particle(korean_analyzer, text, name):
    assert [n for n, _ in found(korean_analyzer, text)] == [name]
