import time

import pytest

from presidio_ko import (
    KrAddressRecognizer,
    KrBankAccountRecognizer,
    KrHealthInsuranceRecognizer,
    KrPersonRecognizer,
    KrPhoneRecognizer,
    KrVehiclePlateRecognizer,
    create_korean_analyzer,
)

N = 50_000
HOSTILE = {
    "hangul": "가" * N,
    "hangul_space": "가 " * (N // 2),
    "sigungu": "가시 " * (N // 3),
    "sigungu_nospace": "가구" * (N // 2),
    "eupmyeon": "가면 " * (N // 3),
    "sido_eupmyeon": "서울 " + "가읍" * (N // 2),
    "sejong_eupmyeon": "세종 " + "가읍" * (N // 2),
    "sejong_eupmyeon_space": "세종시 " + "가면 " * (N // 3),
    "road_without_number": "서울 강남구 " + "가로" * (N // 2),
    "ro_space": "로 " * (N // 2),
    "detail": "서울 강남구 테헤란로 1" + ", 1동" * (N // 4) + "x",
    "detail_space": "서울 강남구 테헤란로 1" + " 1동" * (N // 3) + "1",
    "comma_unit_dashes": "서울 강남구 테헤란로 1, 1-1" + "-1" * (N // 2),
    "comma_unit_digits": "서울 강남구 테헤란로 1, 1-" + "1" * N,
    "building_words": "서울 강남구 테헤란로 1" + " 가1" * (N // 3) + "x",
    "building_long_word": "서울 강남구 테헤란로 1 " + "가" * N + "서",
    "building_particles": "서울 강남구 테헤란로 1" + " 가서" * (N // 3) + " 1호",
    "building_digits": "서울 강남구 테헤란로 1 " + "1 " * (N // 2) + "x",
    "digits": "1" * N,
    "digits_dash": "1-" * (N // 2),
    "digits_space": "1 " * (N // 2),
    "spaces": " " * N,
    "account_label_spaces": "계좌" + " " * N + "x",
    "account_label_digits": "계좌 " + "123 " * (N // 4),
    "account_label_repeat": "계좌" * (N // 2),
    "depositor": "예금주 " + "가" * N,
    "insurance_label_spaces": "건강보험증번호" + " " * N,
    "insurance_label_repeat": "건강보험증번호 " * (N // 8),
    "plate": "1가 " * (N // 3),
    "seoul": "서울 " * (N // 3),
    "paren": "서울 강남구 테헤란로 1" + "(" * N,
    "bank_prefix_spaces": "메모" + " " * N + "끝 국민 123456-78-901234",
    "bank_prefix_repeat": "국민 " * (N // 3) + "1",
    "person_label_spaces": "성명" + " " * N + "x",
    "person_label_repeat": "성명 " * (N // 3),
    "person_name_label_repeat": "대표 이사 주문자명 " * (N // 10),
    "person_label_colons": "성명" + ":" * N,
}
RECOGNIZERS = [
    KrAddressRecognizer(),
    KrBankAccountRecognizer(),
    KrHealthInsuranceRecognizer(),
    KrPersonRecognizer(),
    KrPhoneRecognizer(),
    KrVehiclePlateRecognizer(),
    *[
        r
        for r in create_korean_analyzer().registry.recognizers
        if r.name == "CreditCardRecognizer"
    ],
]


@pytest.mark.parametrize("recognizer", RECOGNIZERS, ids=lambda r: type(r).__name__)
@pytest.mark.parametrize("text", HOSTILE.values(), ids=HOSTILE.keys())
def test_hostile_input_is_analyzed_quickly(recognizer, text):
    start = time.perf_counter()
    recognizer.analyze(text, recognizer.supported_entities)
    assert time.perf_counter() - start < 1
