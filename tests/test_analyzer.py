import logging

import pytest

from presidio_ko import create_korean_analyzer


def found(analyzer, text, **kwargs):
    results = analyzer.analyze(text=text, language="ko", **kwargs)
    return {(r.entity_type, text[r.start : r.end]) for r in results}


def test_phone_is_reported_once_as_kr_phone(korean_analyzer):
    text = "연락처는 010-1234-5678 입니다"
    assert found(korean_analyzer, text) == {("KR_PHONE", "010-1234-5678")}


def test_detects_card_passport_and_license(korean_analyzer):
    text = "카드 4111-1111-1111-1111 여권번호 M123A4567 운전면허 11-17-123456-21"
    assert found(korean_analyzer, text) >= {
        ("CREDIT_CARD", "4111-1111-1111-1111"),
        ("KR_PASSPORT", "M123A4567"),
        ("KR_DRIVER_LICENSE", "11-17-123456-21"),
    }


@pytest.mark.parametrize(
    "text",
    ["연락처 010-1234-5678 010-2345-6789", "연락처 010 1234 5678 010 2345 6789"],
)
def test_two_phone_numbers_are_not_a_card_number(korean_analyzer, text):
    assert found(korean_analyzer, text) == {
        ("KR_PHONE", text[4:17]),
        ("KR_PHONE", text[18:]),
    }


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("4111111111111111", "5500000000000004"),
        ("4111 1111 1111 1111", "5500 0000 0000 0004"),
    ],
)
def test_cards_next_to_each_other_are_both_found(korean_analyzer, first, second):
    cards = found(korean_analyzer, f"카드 {first} {second}")
    assert {v for e, v in cards if e == "CREDIT_CARD"} == {first, second}


def test_detects_rrn_and_bank_account(korean_analyzer):
    text = "주민등록번호는 900101-1234567 계좌는 110-123-456789"
    assert found(korean_analyzer, text) >= {
        ("KR_RRN", "900101-1234567"),
        ("KR_BANK_ACCOUNT", "110-123-456789"),
    }


def test_creating_the_analyzer_logs_no_warnings(caplog):
    create_korean_analyzer()
    assert not [r for r in caplog.records if r.levelname == "WARNING"]


def test_creating_the_analyzer_leaves_the_logger_level_alone():
    logger = logging.getLogger("presidio-analyzer")
    before = logger.getEffectiveLevel()
    create_korean_analyzer()
    create_korean_analyzer()
    assert logger.isEnabledFor(logging.WARNING)
    assert logger.getEffectiveLevel() == before


@pytest.mark.parametrize("label", ["주민번호", "주민등록번호", "신분증", "본인인증"])
def test_korean_rrn_labels_raise_the_score(korean_analyzer, label):
    text = f"{label} 900101-1234567"
    (result,) = [
        r
        for r in korean_analyzer.analyze(text=text, language="ko")
        if r.entity_type == "KR_RRN"
    ]
    assert result.score >= 0.85
