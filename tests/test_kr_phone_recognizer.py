import pytest

from presidio_ko import KrPhoneRecognizer

recognizer = KrPhoneRecognizer()


def found(text):
    return [text[r.start : r.end] for r in recognizer.analyze(text, ["KR_PHONE"])]


def score(analyzer, text):
    results = analyzer.analyze(text=text, language="ko", entities=["KR_PHONE"])
    assert len(results) == 1
    return results[0].score


@pytest.mark.parametrize(
    "text, expected",
    [
        ("010-1234-5678로 연락주세요", "010-1234-5678"),
        ("010-1234-5678이에요", "010-1234-5678"),
        ("번호는010-1234-5678입니다", "010-1234-5678"),
        ("02-123-4567으로 전화 주세요", "02-123-4567"),
        ("HP010-1234-5678", "010-1234-5678"),
        ("TEL02-123-4567", "02-123-4567"),
        ("연락처 010-1234-5678.2번으로", "010-1234-5678"),
        ("+82 010-1234-5678", "+82 010-1234-5678"),
        ("대표 (02) 123-4567 입니다", "(02) 123-4567"),
        ("연락처 (010) 1234-5678", "(010) 1234-5678"),
        ("Tel.(031)123-4567", "(031)123-4567"),
        ("Tel. 02)123-4567", "02)123-4567"),
        ("Tel. (02)-123-4567", "(02)-123-4567"),
        ("연락처 (010) - 1234-5678", "(010) - 1234-5678"),
        ("번호 010 - 1234 - 5678 입니다", "010 - 1234 - 5678"),
        ("안심번호 0505-123-4567", "0505-123-4567"),
        ("안심번호 0504-1234-5678", "0504-1234-5678"),
        ("+82 (0)10-1234-5678", "+82 (0)10-1234-5678"),
        ("(+82) 10-1234-5678", "(+82) 10-1234-5678"),
        ("번호 010−1234−5678 입니다", "010−1234−5678"),
    ],
)
def test_matches_number_in_text(text, expected):
    assert found(text) == [expected]


@pytest.mark.parametrize(
    "number",
    [
        "010-1234-5678",
        "010 1234 5678",
        "01012345678",
        "011-123-4567",
        "019-1234-5678",
        "02-123-4567",
        "02-1234-5678",
        "031-123-4567",
        "064-1234-5678",
        "070-1234-5678",
        "010–1234–5678",
        "031‐123‐4567",
        "010.1234.5678",
        "031.123.4567",
        "+82 10-1234-5678",
        "+82-10-1234-5678",
        "+821012345678",
        "+8201012345678",
        "+82 2-123-4567",
        "010-12345678",
    ],
)
def test_matches_mobile_and_landline_formats(number):
    assert found(f"번호 {number} 입니다") == [number]


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-15",
        "123-45-67890",
        "123-456-789012",
        "0212345678",
        "주문번호 20240115010123456789",
        "010-1234-56789",
        "031-123-4567-89",
        "89-031-123-4567",
        "문서번호 12-010-1234-5678",
        "주문ID ORD01012345678",
        "010\n1234\n5678",
        "02\n123\n4567",
        "대표번호 1588-1234",
        "080-123-4567",
        "(2024) 123-4567",
        "0509-123-4567",
        "2024-02) 1234-5678",
    ],
)
def test_ignores_non_phone_numbers(text):
    assert found(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "제 연락처는 010-1234-5678이고",
        "연락처가 010-1234-5678입니다",
        "전화번호로 010-1234-5678 연락주세요",
        "휴대폰번호 010-1234-5678",
        "핸드폰: 010-1234-5678",
        "mobile 010-1234-5678",
        "Tel. 010-1234-5678",
        "HP 010-1234-5678",
        "Fax 010-1234-5678",
        "팩스 010-1234-5678",
        "휴대전화 010-1234-5678",
        "안심번호 010-1234-5678",
    ],
)
def test_context_word_raises_score(analyzer, text):
    assert score(analyzer, text) > score(analyzer, "010-1234-5678")


def test_unrelated_words_do_not_raise_score(analyzer):
    assert score(analyzer, "주문 010-1234-5678") == score(analyzer, "010-1234-5678")


def test_context_word_far_before_number_is_ignored(analyzer):
    text = "전화 예약 확인 메일 발송 완료 고객 번호 목록 정리 010-1234-5678"
    assert score(analyzer, text) == score(analyzer, "010-1234-5678")


def test_empty_context_list_disables_context():
    assert KrPhoneRecognizer(context=[]).context == []


@pytest.mark.parametrize(
    "text, expected",
    [
        ("연락처 ０１０-１２３４-５６７８로", "０１０-１２３４-５６７８"),
        ("＋８２ １０－１２３４－５６７８", "＋８２ １０－１２３４－５６７８"),
    ],
)
def test_matches_full_width_digits(analyzer, text, expected):
    results = analyzer.analyze(
        text=text, language="ko", entities=["KR_PHONE", "KR_BANK_ACCOUNT"]
    )
    assert [(r.entity_type, text[r.start : r.end]) for r in results] == [
        ("KR_PHONE", expected)
    ]


@pytest.mark.parametrize(
    "number", ["010·1234·5678", "010ㆍ1234ㆍ5678", "02·123·4567", "010 · 1234 · 5678"]
)
def test_middle_dot_separates_groups(number):
    assert found(f"연락처 {number}로") == [number]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1·2·3차 회의", []),
        ("2024·11·28", []),
        ("010-1234-5678·010-2345-6789", ["010-1234-5678", "010-2345-6789"]),
    ],
)
def test_middle_dot_between_items_does_not_join_them(text, expected):
    assert found(text) == expected
