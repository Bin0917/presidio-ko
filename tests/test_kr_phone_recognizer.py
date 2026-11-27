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
        # 한글은 정규식에서 \w라서 "5678로" 사이에 \b가 없다. 숫자 lookaround로만 잡힌다
        ("010-1234-5678로 연락주세요", "010-1234-5678"),
        ("010-1234-5678이에요", "010-1234-5678"),
        ("번호는010-1234-5678입니다", "010-1234-5678"),
        ("02-123-4567으로 전화 주세요", "02-123-4567"),
        ("HP010-1234-5678", "010-1234-5678"),  # 영문 약어 바로 뒤
        ("TEL02-123-4567", "02-123-4567"),
        ("연락처 010-1234-5678.2번으로", "010-1234-5678"),  # 띄어쓰기 빠진 마침표 뒤
        ("+82 010-1234-5678", "+82 010-1234-5678"),  # +82 뒤에 0을 남긴 경우
        # 문서·명함에서 흔한 표기: 괄호 지역번호, 대시 앞뒤 공백, 050X 안심번호,
        # 국제 형식의 (0)·괄호, 유니코드 빼기 기호(U+2212, OCR)
        ("대표 (02) 123-4567 입니다", "(02) 123-4567"),
        ("연락처 (010) 1234-5678", "(010) 1234-5678"),
        ("Tel.(031)123-4567", "(031)123-4567"),
        ("Tel. 02)123-4567", "02)123-4567"),
        ("Tel. (02)-123-4567", "(02)-123-4567"),  # 괄호 뒤 대시
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
        "010–1234–5678",  # en dash (PDF·OCR 추출문)
        "031‐123‐4567",  # 유니코드 하이픈 U+2010
        "010.1234.5678",  # 점 구분
        "031.123.4567",
        "+82 10-1234-5678",  # 국제 형식
        "+82-10-1234-5678",
        "+821012345678",
        "+8201012345678",
        "+82 2-123-4567",
        "010-12345678",  # 구분자 한 곳만
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
        "89-031-123-4567",  # 더 긴 하이픈 번호의 뒷부분
        "문서번호 12-010-1234-5678",
        "주문ID ORD01012345678",  # 영숫자 ID 속의 010 (구분자 없는 형식)
        "010\n1234\n5678",  # 줄마다 따로 적힌 숫자(표의 열 등)
        "02\n123\n4567",
        "대표번호 1588-1234",  # 기업 대표번호는 개인 연락처가 아니다
        "080-123-4567",  # 수신자부담
        "(2024) 123-4567",  # 괄호 안이 지역번호가 아님
        "0509-123-4567",  # 050X 범위 밖
        "2024-02) 1234-5678",  # 더 긴 하이픈 번호의 꼬리
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


# 전각 숫자(PDF·일본어 입력기 등)도 같은 번호로 잡고, 계좌로 오인하지 않는다
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
