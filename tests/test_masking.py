import pytest
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from presidio_ko import korean_operators


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
        ("KR_BRN", "123-45-67890", "<KR_BRN>"),
    ],
)
def test_korean_masking_rules(entity, value, masked):
    assert mask(entity, value) == masked


def test_user_can_override_a_rule():
    operators = korean_operators() | {"KR_PHONE": OperatorConfig("replace")}
    assert mask("KR_PHONE", "010-1234-5678", operators) == "<KR_PHONE>"
