import pytest

from presidio_ko import KrHealthInsuranceRecognizer

recognizer = KrHealthInsuranceRecognizer()


def found(text):
    return [
        (text[r.start : r.end], r.score)
        for r in recognizer.analyze(text, ["KR_HEALTH_INSURANCE"])
    ]


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("건강보험증번호 1-2345678901", "1-2345678901"),
        ("건강보험증 번호: 12345678901", "12345678901"),
        ("건강보험증번호는 1-2345678901입니다", "1-2345678901"),
        ("보험증번호：12-3456789012", "12-3456789012"),
        ("건보 번호 1234567890", "1234567890"),
    ],
)
def test_matches_number_after_label(text, number):
    assert found(text) == [(number, 0.6)]


@pytest.mark.parametrize(
    "text",
    [
        "1-2345678901",
        "등록번호 1-2345678901",
        "건강보험증번호 123456789",
        "건강보험증번호 1-23456789012345",
    ],
)
def test_requires_the_label_and_length(text):
    assert found(text) == []
