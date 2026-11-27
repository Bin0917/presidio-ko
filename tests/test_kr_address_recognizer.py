import pytest
from presidio_anonymizer import AnonymizerEngine

from presidio_ko import KrAddressRecognizer, korean_operators

recognizer = KrAddressRecognizer()


def found(text):
    return [
        (text[r.start : r.end], r.score)
        for r in recognizer.analyze(text, ["KR_ADDRESS"])
    ]


@pytest.mark.parametrize(
    ("text", "address", "score"),
    [
        (
            "서울특별시 강남구 테헤란로 152 역삼빌딩 1203호",
            "서울특별시 강남구 테헤란로 152",
            0.6,
        ),
        (
            "수령지: 경기도 성남시 분당구 판교역로 235 에이치스퀘어 N동 5층",
            "경기도 성남시 분당구 판교역로 235",
            0.6,
        ),
        ("서울 서초구 서초대로 398 플래티넘타워 10층", "서울 서초구 서초대로 398", 0.6),
        ("대전광역시 유성구 대학로 99", "대전광역시 유성구 대학로 99", 0.6),
        (
            "서울 영등포구 영등포로3길 12, 101동 1001호",
            "서울 영등포구 영등포로3길 12, 101동 1001호",
            0.6,
        ),
        ("분당구 판교역로 235 입니다", "분당구 판교역로 235", 0.6),
        (
            "부산광역시 해운대구 우동 1408-3 센텀파크 101동 802호",
            "부산광역시 해운대구 우동 1408-3",
            0.5,
        ),
        ("제주 제주시 연동 123번지", "제주 제주시 연동 123번지", 0.5),
    ],
)
def test_matches_road_and_lot_addresses(text, address, score):
    assert found(text) == [(address, score)]


@pytest.mark.parametrize(
    "text",
    [
        "서울 강남구에서 만나요",  # 번호 없음
        "서울 12",
        "우동 1408-3 센텀파크",  # 시도·시군구 없는 지번
        "2024년 3월 12일 회의",
        "테헤란로 152",  # 시군구 없음
    ],
)
def test_ignores_non_addresses(text):
    assert found(text) == []


def test_analyzed_address_is_masked_after_the_building_number(korean_analyzer):
    text = "배송지는 서울 영등포구 영등포로3길 12, 101동 1001호 입니다"
    results = korean_analyzer.analyze(text=text, language="ko")
    masked = AnonymizerEngine().anonymize(text, results, korean_operators()).text
    assert masked == "배송지는 서울 영등포구 영등포로3길 **, ***동 ****호 입니다"
