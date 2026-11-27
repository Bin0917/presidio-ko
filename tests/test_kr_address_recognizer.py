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
            "서울특별시 강남구 테헤란로 152 역삼빌딩 1203호",
            0.6,
        ),
        (
            "수령지: 경기도 성남시 분당구 판교역로 235 에이치스퀘어 N동 5층",
            "경기도 성남시 분당구 판교역로 235 에이치스퀘어 N동 5층",
            0.6,
        ),
        ("서울 서초구 서초대로 398 플래티넘타워 10층", "서울 서초구 서초대로 398", 0.6),
        ("대전광역시 유성구 대학로 99", "대전광역시 유성구 대학로 99", 0.6),
        (
            "서울 영등포구 영등포로3길 12, 101동 1001호",
            "서울 영등포구 영등포로3길 12, 101동 1001호",
            0.6,
        ),
        ("주소: 분당구 판교역로 235 입니다", "분당구 판교역로 235", 0.6),
        (
            "배송지 성남시 분당구 판교역로 235, A동 301호",
            "성남시 분당구 판교역로 235, A동 301호",
            0.6,
        ),
        (
            "부산광역시 해운대구 우동 1408-3 센텀파크 101동 802호",
            "부산광역시 해운대구 우동 1408-3 센텀파크 101동 802호",
            0.5,
        ),
        ("제주 제주시 연동 123번지", "제주 제주시 연동 123번지", 0.5),
        (
            "서울 강남구 테헤란로 1275번길 38-10 입니다",
            "서울 강남구 테헤란로 1275번길 38-10",
            0.6,
        ),
        (
            "서울 강남구 테헤란로 152, 101-1203 호",
            "서울 강남구 테헤란로 152, 101-1203",
            0.6,
        ),
        (
            "서울 강남구 테헤란로 152 에이동 1203호",
            "서울 강남구 테헤란로 152 에이동 1203호",
            0.6,
        ),
        ("서울 강남구 테헤란로 152 역삼빌딩 10층", "서울 강남구 테헤란로 152", 0.6),
        ("경기도 양평군 양평읍 양평로 100", "경기도 양평군 양평읍 양평로 100", 0.6),
        (
            "주소: 전라남도 순천시 해룡면 상삼리 123-4",
            "전라남도 순천시 해룡면 상삼리 123-4",
            0.5,
        ),
        (
            "제주특별자치도 제주시 애월읍 애월로 1",
            "제주특별자치도 제주시 애월읍 애월로 1",
            0.6,
        ),
        ("세종시 조치원읍 세종로 2511", "세종시 조치원읍 세종로 2511", 0.6),
        (
            "서울 마포구 월드컵북로 396 지하1층 입니다",
            "서울 마포구 월드컵북로 396 지하1층",
            0.6,
        ),
        (
            "서울 강남구 테헤란로 152 래미안 퍼스티지 101동 1203호",
            "서울 강남구 테헤란로 152 래미안 퍼스티지 101동 1203호",
            0.6,
        ),
        (
            "서울특별시 노원구 상계동 1234 주공아파트 7단지 701동 1102호",
            "서울특별시 노원구 상계동 1234 주공아파트 7단지 701동 1102호",
            0.5,
        ),
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
        "다시 처음으로 1번 문제를 풀어보세요.",
        "이번 연구 결과로 3명이 합격했다.",
        "요구 사항으로 5개를 정리했다.",
        "우리 가구 배송으로 2일 걸려요",
        "그는 다시 집으로 10시에 돌아왔다.",
        "연구원으로 5년 근무했다.",
        "성남시 분당구 판교역로 235",  # 시도도 주소 라벨도 없음
    ],
)
def test_ignores_non_addresses(text):
    assert found(text) == []


def test_address_label_allows_a_missing_province():
    text = "주소: 분당구 판교역로 235"
    assert found(text) == [("분당구 판교역로 235", 0.6)]


def test_analyzed_address_is_masked_after_the_building_number(korean_analyzer):
    text = "배송지는 서울 영등포구 영등포로3길 12, 101동 1001호 입니다"
    results = korean_analyzer.analyze(text=text, language="ko")
    masked = AnonymizerEngine().anonymize(text, results, korean_operators()).text
    assert masked == "배송지는 서울 영등포구 영등포로3길 **, ***동 ****호 입니다"


def test_street_name_without_a_building_number_is_not_cut_in_half():
    assert found("제주 서귀포시 중문관광로 72번길 방향으로 우회하세요.") == []
