import pytest


def entities(analyzer, text):
    results = analyzer.analyze(text=text, language="ko")
    return {(r.entity_type, text[r.start : r.end]) for r in results}


@pytest.mark.parametrize(
    "text",
    [
        "주문번호 123456789012",
        "송장번호 112233445566",
        "상품코드 210000000001",
        "택배 112233445566 도착",
    ],
)
def test_unseparated_12_digits_without_a_license_label_are_not_a_license(
    korean_analyzer, text
):
    kinds = {kind for kind, _ in entities(korean_analyzer, text)}
    assert "KR_DRIVER_LICENSE" not in kinds


@pytest.mark.parametrize(
    "text",
    [
        "운전면허 112233445566",
        "운전면허번호: 112233445566",
        "면허번호는 112233445566",
        "driver license 112233445566",
        "운전면허 11-17-123456-21",
        "면허 11 17 123456 21",
    ],
)
def test_license_with_a_label_or_separators_is_detected(korean_analyzer, text):
    kinds = {kind for kind, _ in entities(korean_analyzer, text)}
    assert "KR_DRIVER_LICENSE" in kinds


def test_account_and_insurance_numbers_win_over_license(korean_analyzer):
    account = entities(korean_analyzer, "계좌번호 110123456789")
    insurance = entities(korean_analyzer, "건강보험증번호 112233445566")
    assert ("KR_BANK_ACCOUNT", "110123456789") in account
    assert ("KR_HEALTH_INSURANCE", "112233445566") in insurance
    assert "KR_DRIVER_LICENSE" not in {kind for kind, _ in account | insurance}


@pytest.mark.parametrize(
    "text",
    [
        "운전면허 11-17-123456-21-9",
        "번호 1111 123456-78",
        "4111-1111-1111-1111 123456-78-901234",
        "운전면허 9-11-17-123456-21",
    ],
)
def test_part_of_a_longer_or_mixed_number_is_not_a_license(korean_analyzer, text):
    kinds = {kind for kind, _ in entities(korean_analyzer, text)}
    assert "KR_DRIVER_LICENSE" not in kinds
