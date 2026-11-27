import pytest
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

import presidio_ko
from presidio_ko import korean_mask
from presidio_ko.masking import korean_operators


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
        (
            "KR_ADDRESS",
            "서울 노원구 상계동 1234 주공아파트 7단지 701동 1102호",
            "서울 노원구 상계동 **** 주공아파트 *단지 ***동 ****호",
        ),
        ("KR_BRN", "123-45-67890", "***-**-*****"),
        ("KR_PASSPORT", "M123A4567", "*********"),
        ("KR_DRIVER_LICENSE", "11-17-123456-21", "**-**-******-**"),
        ("KR_HEALTH_INSURANCE", "1-2345678901", "*-**********"),
        ("URL", "example.com", "<URL>"),
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


def test_korean_mask_hides_what_either_nested_rule_hides():
    # 바깥 계좌 규칙은 끝 2자리를, 안쪽 전화 규칙은 끝 4자리를 가린다
    text = "번호 110-123-456789"
    results = [
        RecognizerResult("KR_BANK_ACCOUNT", 3, 17, 0.75),
        RecognizerResult("KR_PHONE", 7, 17, 0.4),
    ]
    assert korean_mask(text, results) == "번호 110-***-******"


def test_korean_mask_merges_overlapping_results_of_one_entity(korean_analyzer):
    # 주소 결과가 "…을지로2"(0.6)와 "…을지로2가 50"(0.5) 둘로 나온다
    text = "서울 중구 을지로2가 50"
    results = korean_analyzer.analyze(text=text, language="ko")
    assert korean_mask(text, results) == "서울 중구 을지로2가 **"


def test_korean_mask_masks_the_remainder_of_a_partial_loser():
    results = [
        RecognizerResult("PERSON", 0, 4, 0.9),
        RecognizerResult("KR_PHONE", 3, 6, 0.5),
    ]
    assert korean_mask("홍길동010", results) == "홍*동***"


def test_korean_mask_masks_a_name_inside_an_address():
    # 주소 규칙은 숫자만 가리므로 주소에 묻힌 이름은 이름 규칙으로 가린다
    text = "서울 강남구 테헤란로 152 받는 분 김민수 101호"
    start = text.index("김민수")
    results = [
        RecognizerResult("KR_ADDRESS", 0, len(text), 0.6),
        RecognizerResult("PERSON", start, start + 3, 0.85),
    ]
    assert korean_mask(text, results) == "서울 강남구 테헤란로 *** 받는 분 김*수 ***호"


def test_name_after_an_address_is_masked_as_a_name(korean_analyzer):
    text = "서울 강남구 테헤란로 152 받는 분 김민수 101호"
    results = korean_analyzer.analyze(text=text, language="ko")
    assert korean_mask(text, results) == "서울 강남구 테헤란로 *** 받는 분 김*수 101호"


def test_korean_mask_takes_custom_operators():
    results = [RecognizerResult("KR_PHONE", 0, 13, 0.9)]
    operators = korean_operators() | {"KR_PHONE": OperatorConfig("replace")}
    assert korean_mask("010-1234-5678", results, operators) == "<KR_PHONE>"


def test_korean_mask_keeps_an_empty_operator_dict():
    results = [RecognizerResult("KR_PHONE", 0, 13, 0.9)]
    assert korean_mask("010-1234-5678", results, {}) == "<KR_PHONE>"


def test_operators_are_not_exported_at_the_top_level():
    # 기본 AnonymizerEngine.anonymize에 넘기면 공백으로 이웃한 같은 종류가 합쳐져 샌다
    assert "korean_operators" not in presidio_ko.__all__
    assert not hasattr(presidio_ko, "korean_operators")
