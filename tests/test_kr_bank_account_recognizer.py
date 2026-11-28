import pytest

from presidio_ko import KrBankAccountRecognizer

recognizer = KrBankAccountRecognizer()


def analyze(text):
    return recognizer.analyze(text, ["KR_BANK_ACCOUNT"])


def found(text):
    return [text[r.start : r.end] for r in analyze(text)]


def score(analyzer, text):
    results = analyzer.analyze(text=text, language="ko", entities=["KR_BANK_ACCOUNT"])
    assert len(results) == 1
    return results[0].score


@pytest.mark.parametrize(
    "account",
    [
        "123-45-678901",
        "110-123-456789",
        "1002-123-456789",
        "123456-78-901234",
        "123-456789-01234",
        "3333-01-1234567",
        "1000-1234-5678",
        "301-1234-5678-91",
        "351-1234-5678-91",
        "123-1234-5678-901",
        "123-456789-01-234",
        "123-45-678901-2",
    ],
)
def test_matches_bank_account_formats(account):
    assert found(f"번호 {account} 입니다") == [account]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("110-123-456789로 입금해 주세요", "110-123-456789"),
        ("계좌는110-123-456789입니다", "110-123-456789"),
        ("신한-110-123-456789", "110-123-456789"),
        ("KB-123456-78-901234", "123456-78-901234"),
        ("110–123–456789", "110–123–456789"),
        ("계좌 110−123−456789", "110−123−456789"),
        ("계좌+110-123-456789", "110-123-456789"),
    ],
)
def test_matches_account_in_surrounding_text(text, expected):
    assert found(text) == [expected]


@pytest.mark.parametrize("account", ["123-45-6789-012", "123-456789-012"])
def test_unlisted_format_is_kept_with_lower_score(account):
    [unlisted] = analyze(account)
    [known] = analyze("110-123-456789")
    assert 0 < unlisted.score < known.score


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-15",
        "2024-01-15-1030",
        "2024-1-5-1030",
        "123-45-67890",
        "010-1234-5678",
        "031-123-4567",
        "02-1234-5678",
        "018-123-4567",
        "080-123-4567",
        "0504-1234-5678",
        "900101-1234567",
        "1234-5678-9012-3456",
        "123-45-6789",
        "123456789012",
        "상품코드 SKU110-123-456789",
        "010-123-45678",
        "010-12345-678",
        "011-1234-567",
        "(02) 123-4567",
        "연락처 +8210-1234-5678",
        "+82010-1234-5678",
        "٠١٠-١٢٣٤-٥٦٧٨",
    ],
)
def test_ignores_non_account_numbers(text):
    assert found(text) == []


def test_valid_format_keeps_low_score():
    [result] = analyze("110-123-456789")
    assert 0.4 <= result.score <= 0.6


@pytest.mark.parametrize(
    "text",
    [
        "급여계좌는 110-123-456789",
        "은행계좌 110-123-456789",
        "입금계좌: 110-123-456789",
        "계좌번호는 110-123-456789 입니다",
        "bank account 110-123-456789",
    ],
)
def test_context_word_raises_score(analyzer, text):
    assert score(analyzer, text) > score(analyzer, "110-123-456789")


def test_empty_context_list_disables_context():
    assert KrBankAccountRecognizer(context=[]).context == []


@pytest.mark.parametrize(
    "text, expected",
    [
        ("급여계좌: 110 123 456789 (신한은행)", "110 123 456789"),
        ("환불 계좌번호 3333041234567 입니다", "3333041234567"),
        ("계좌는 1002123456789입니다", "1002123456789"),
        ("카카오뱅크 3333041234567", "3333041234567"),
        ("신한은행 110 123 456789", "110 123 456789"),
        ("예금주 홍길동 1002123456789", "1002123456789"),
        ("입금계좌：123456 78 901234", "123456 78 901234"),
    ],
)
def test_matches_unhyphenated_account_after_label(text, expected):
    assert found(text) == [expected]


@pytest.mark.parametrize(
    "text",
    [
        "주문번호 1234567890",
        "계좌 01012345678",
        "계좌 010 1234 5678",
        "계좌 안내 문서번호 12345678901",
        "계좌 123456789",
        "계좌 123456789012345",
    ],
)
def test_ignores_unhyphenated_numbers_without_account_label(text):
    assert found(text) == []


def test_bank_name_alone_is_enough_for_context(korean_analyzer):
    text = "국민 123456-78-901234"
    [result] = korean_analyzer.analyze(
        text=text, language="ko", entities=["KR_BANK_ACCOUNT"]
    )
    assert result.score >= 0.5


def test_common_word_does_not_boost_a_document_number(korean_analyzer):
    text = "우리는 주문번호 2024-123-456789 를 확인했다"
    [result] = korean_analyzer.analyze(
        text=text, language="ko", entities=["KR_BANK_ACCOUNT"]
    )
    assert result.score < 0.5
