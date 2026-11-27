import pytest
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from presidio_ko import korean_mask, korean_operators


def mask(entity, value, operators=None):
    result = AnonymizerEngine().anonymize(
        value,
        [RecognizerResult(entity, 0, len(value), 0.9)],
        operators or korean_operators(),
    )
    return result.text


@pytest.mark.parametrize(
    ("entity", "value", "masked"),
    [
        ("PERSON", "홍길동", "홍*동"),
        ("PERSON", "남궁민수", "남*민*"),
        ("PERSON", "홍길", "홍*"),
        ("KR_PHONE", "010-1234-5678", "010-1234-****"),
        ("KR_PHONE", "+82 10-1234-5678", "+82 10-1234-****"),
        ("KR_PHONE", "02-555-1234", "02-555-****"),
        ("KR_RRN", "900101-1234567", "900101-1******"),
        ("KR_FRN", "900101-5234567", "900101-5******"),
        ("KR_BANK_ACCOUNT", "110-123-456789", "110-***-****89"),
        ("KR_BANK_ACCOUNT", "123456-78-901234", "123456-**-****34"),
        ("KR_BANK_ACCOUNT", "3333041234567", "333********67"),
        ("EMAIL_ADDRESS", "nguyen@example.com", "ng****@example.com"),
        ("CREDIT_CARD", "4111-1111-1111-1111", "4111-11**-****-1111"),
        ("KR_VEHICLE_PLATE", "12가 3456", "12가 **56"),
        ("KR_ADDRESS", "서울 영등포구 영등포로3길 12", "서울 영등포구 영등포로3길 **"),
        (
            "KR_ADDRESS",
            "서울 영등포구 영등포로3길 12, 101동 1001호",
            "서울 영등포구 영등포로3길 **, ***동 ****호",
        ),
        ("KR_ADDRESS", "부산 해운대구 우동 1408-3", "부산 해운대구 우동 ****-*"),
        ("KR_ADDRESS", "서울 강남구 테헤란로 152", "서울 강남구 테헤란로 ***"),
        ("KR_ADDRESS", "서울 강남구 테헤란로152", "서울 강남구 테헤란로***"),
        ("KR_ADDRESS", "서울 영등포구 영등포로3길 12", "서울 영등포구 영등포로3길 **"),
        (
            "KR_ADDRESS",
            "서울 강남구 테헤란로 1275번길 38-10",
            "서울 강남구 테헤란로 1275번길 **-**",
        ),
        ("KR_ADDRESS", "서울 중구 을지로2가 50", "서울 중구 을지로2가 **"),
        (
            "KR_ADDRESS",
            "서울 강남구 테헤란로 152 에이동 1203호",
            "서울 강남구 테헤란로 *** **동 ****호",
        ),
        (
            "KR_ADDRESS",
            "성남시 분당구 판교역로 235, A동 301호",
            "성남시 분당구 판교역로 ***, *동 ***호",
        ),
        ("KR_BRN", "123-45-67890", "<KR_BRN>"),
    ],
)
def test_korean_masking_rules(entity, value, masked):
    assert mask(entity, value) == masked


def test_user_can_override_a_rule():
    operators = korean_operators() | {"KR_PHONE": OperatorConfig("replace")}
    assert mask("KR_PHONE", "010-1234-5678", operators) == "<KR_PHONE>"


def test_korean_mask_masks_neighbours_separately(korean_analyzer):
    # AnonymizerEngine은 공백으로 이웃한 같은 종류를 하나로 합쳐 뒤 4자리만 가린다
    text = "연락처 010-1234-5678 010-2345-6789 이메일 abcd@x.com efgh@y.com"
    results = korean_analyzer.analyze(text=text, language="ko")
    assert korean_mask(text, results) == (
        "연락처 010-1234-**** 010-2345-**** 이메일 ab****@x.com ef****@y.com"
    )


def test_korean_mask_keeps_the_higher_scored_of_overlapping_results():
    text = "번호 110-123-456789"
    results = [
        RecognizerResult("KR_BANK_ACCOUNT", 3, 17, 0.75),
        RecognizerResult("KR_PHONE", 7, 17, 0.4),
    ]
    assert korean_mask(text, results) == "번호 110-***-****89"


def test_korean_mask_takes_custom_operators():
    results = [RecognizerResult("KR_PHONE", 0, 13, 0.9)]
    operators = korean_operators() | {"KR_PHONE": OperatorConfig("replace")}
    assert korean_mask("010-1234-5678", results, operators) == "<KR_PHONE>"
