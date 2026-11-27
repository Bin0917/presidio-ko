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
    ],
)
def test_label_gives_high_score(text, name):
    assert labeled(text) == [(name, 0.85)]


@pytest.mark.parametrize(
    "text",
    [
        "성명: 가나다",  # 성씨가 아님
        "성명: 홍",  # 1글자
        "임차인 임대인",  # 필드 라벨
        "이름: 이체일시",
        "성명:\n김민수",  # 줄이 바뀌면 값이 아님
        "주문번호 송장번호 이체일시 사원명 서명",
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
