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


def test_detects_rrn_and_bank_account(korean_analyzer):
    text = "주민등록번호는 900101-1234567 계좌는 110-123-456789"
    assert found(korean_analyzer, text) >= {
        ("KR_RRN", "900101-1234567"),
        ("KR_BANK_ACCOUNT", "110-123-456789"),
    }
