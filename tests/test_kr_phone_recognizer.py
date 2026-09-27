import pytest

from presidio_ko import KrPhoneRecognizer

recognizer = KrPhoneRecognizer()


def found(text):
    return [text[r.start : r.end] for r in recognizer.analyze(text, ["KR_PHONE"])]


def score(analyzer, text):
    results = analyzer.analyze(text=text, language="ko", entities=["KR_PHONE"])
    assert len(results) == 1
    return results[0].score


# 한글은 정규식에서 \w라서 "5678로" 사이에 \b가 없다. 숫자 lookaround로만 잡힌다.
@pytest.mark.parametrize(
    "text, expected",
    [
        ("010-1234-5678로 연락주세요", "010-1234-5678"),
        ("010-1234-5678이에요", "010-1234-5678"),
        ("번호는010-1234-5678입니다", "010-1234-5678"),
        ("02-123-4567으로 전화 주세요", "02-123-4567"),
    ],
)
def test_matches_number_with_attached_particle(text, expected):
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
        "010–1234–5678",  # en dash (PDF·OCR 추출문)
        "031‐123‐4567",  # 유니코드 하이픈 U+2010
    ],
)
def test_matches_mobile_and_landline_formats(number):
    assert found(f"번호 {number} 입니다") == [number]


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-15",  # 날짜
        "123-45-67890",  # 사업자등록번호
        "123-456-789012",  # 계좌번호
        "0212345678",  # 구분자 없는 지역번호 모양 숫자열
        "주문번호 20240115010123456789",  # 긴 숫자열 속의 010
        "010-1234-56789",  # 자릿수 초과
        "031-123-4567-89",  # 더 긴 하이픈 번호의 앞부분
        "주문ID ORD01012345678",  # 영숫자 ID 속의 010
    ],
)
def test_ignores_non_phone_numbers(text):
    assert found(text) == []


# 아래는 실제 한국어 NLP 파이프라인(AnalyzerEngine + ko_core_news_sm) 통합 테스트
@pytest.mark.parametrize(
    "text",
    [
        "제 연락처는 010-1234-5678이고",
        "연락처가 010-1234-5678입니다",
        "전화번호로 010-1234-5678 연락주세요",
        "휴대폰번호 010-1234-5678",
        "핸드폰: 010-1234-5678",
        "mobile 010-1234-5678",
    ],
)
def test_context_word_raises_score(analyzer, text):
    assert score(analyzer, text) > score(analyzer, "010-1234-5678")


def test_unrelated_words_do_not_raise_score(analyzer):
    assert score(analyzer, "주문 010-1234-5678") == score(analyzer, "010-1234-5678")


def test_context_word_far_before_number_is_ignored(analyzer):
    text = "전화 예약 확인 메일 발송 완료 고객 번호 목록 정리 010-1234-5678"
    assert score(analyzer, text) == score(analyzer, "010-1234-5678")
