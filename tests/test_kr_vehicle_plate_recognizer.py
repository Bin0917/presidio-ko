import pytest

from presidio_ko import KrVehiclePlateRecognizer

recognizer = KrVehiclePlateRecognizer()


def found(text):
    return [
        text[r.start : r.end] for r in recognizer.analyze(text, ["KR_VEHICLE_PLATE"])
    ]


@pytest.mark.parametrize(
    "plate",
    [
        "12가 3456",
        "12가3456",
        "서울12가3456",
        "서울 12가 3456",
        "123가4567",
        "경기 123다 4567",
    ],
)
def test_matches_plates(plate):
    assert found(f"차량 {plate} 주차") == [plate]


@pytest.mark.parametrize(
    "text",
    [
        "101호 1234",  # 호수 뒤 번호는 번호판이 아니다
        "12가 34567",  # 뒤에 숫자가 더 이어짐
        "112가 3456-7",
        "1234가 5678",  # 앞 숫자가 4자리
        "12라 345",
        "12일 3456",  # 용도문자가 아님
        "10가 5000원이면 싸다",  # 가격
    ],
)
def test_ignores_non_plates(text):
    assert found(text) == []


def test_context_raises_score(korean_analyzer):
    text = "차량번호 12가 3456"
    [result] = korean_analyzer.analyze(
        text=text, language="ko", entities=["KR_VEHICLE_PLATE"]
    )
    assert result.score > 0.5
