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
        "123-45-678901",  # 3-2-6 신한(구)·SC제일·대구
        "110-123-456789",  # 3-3-6 신한·케이뱅크·신협·제주
        "1002-123-456789",  # 4-3-6 우리·광주
        "123456-78-901234",  # 6-2-6 KB국민·우체국
        "123-456789-01234",  # 3-6-5 하나
        "3333-01-1234567",  # 4-2-7 카카오뱅크
        "1000-1234-5678",  # 4-4-4 토스뱅크·수협
        "301-1234-5678-91",  # 3-4-4-2 NH농협·부산
        "351-1234-5678-91",  # 3-4-4-2 NH농협(351)
        "123-1234-5678-901",  # 3-4-4-3 KDB산업
        "123-456789-01-234",  # 3-6-2-3 IBK기업
        "123-45-678901-2",  # 3-2-6-1 대구
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
        ("110–123–456789", "110–123–456789"),  # en dash (PDF·OCR 추출문)
        ("계좌 110−123−456789", "110−123−456789"),  # 빼기 기호(U+2212)
        ("계좌+110-123-456789", "110-123-456789"),  # 국가번호가 아닌 + 뒤
    ],
)
def test_matches_account_in_surrounding_text(text, expected):
    assert found(text) == [expected]


# 형식표 밖의 모양도 실제 계좌일 수 있으므로 버리지 않고 더 낮은 점수로 남긴다
@pytest.mark.parametrize("account", ["123-45-6789-012", "123-456789-012"])
def test_unlisted_format_is_kept_with_lower_score(account):
    [unlisted] = analyze(account)
    [known] = analyze("110-123-456789")
    assert 0 < unlisted.score < known.score


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-15",  # 날짜
        "2024-01-15-1030",  # 날짜+시각
        "2024-1-5-1030",  # 한 자리 월·일
        "123-45-67890",  # 사업자등록번호
        "010-1234-5678",  # 휴대폰
        "031-123-4567",  # 유선전화
        "02-1234-5678",  # 서울 유선전화
        "018-123-4567",  # 휴대폰 018
        "080-123-4567",  # 수신자부담 전화
        "0504-1234-5678",  # 050X 안심번호
        "900101-1234567",  # 주민등록번호
        "1234-5678-9012-3456",  # 카드번호
        "123-45-6789",  # 10자리 미만
        "123456789012",  # 구분자 없는 숫자열
        "상품코드 SKU110-123-456789",  # 영숫자 코드
        "010-123-45678",  # 자릿수를 잘못 끊은 휴대폰
        "010-12345-678",
        "011-1234-567",
        "(02) 123-4567",
        "연락처 +8210-1234-5678",  # 국제 형식 전화번호의 일부
        "+82010-1234-5678",
        "٠١٠-١٢٣٤-٥٦٧٨",  # 전각 이외의 유니코드 숫자
    ],
)
def test_ignores_non_account_numbers(text):
    assert found(text) == []


def test_valid_format_keeps_low_score():
    # 체크섬 검증이 불가능하므로 형식이 맞아도 확신도를 낮게(0.4~0.6) 유지해야 한다
    [result] = analyze("110-123-456789")
    assert 0.4 <= result.score <= 0.6


# 아래는 실제 한국어 NLP 파이프라인(AnalyzerEngine + ko_core_news_sm) 통합 테스트
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
        "주문번호 1234567890",  # 라벨 없음
        "계좌 01012345678",  # 휴대폰
        "계좌 010 1234 5678",
        "계좌 안내 문서번호 12345678901",  # 라벨이 바로 앞이 아님
        "계좌 123456789",  # 10자리 미만
        "계좌 123456789012345",  # 14자리 초과
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
