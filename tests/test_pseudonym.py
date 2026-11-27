import time

from presidio_analyzer import RecognizerResult

from presidio_ko import Pseudonymizer


def pseudonymize(korean_analyzer, pseudonymizer, text):
    results = korean_analyzer.analyze(text=text, language="ko")
    return pseudonymizer.pseudonymize(text, results)


def test_same_value_gets_the_same_placeholder(korean_analyzer):
    pseudonymizer = Pseudonymizer()
    text = "예금주 김민수, 받는 분 이영희, 예금주 김민수 연락처 010-1234-5678"
    out = pseudonymize(korean_analyzer, pseudonymizer, text)
    assert out == "예금주 [이름1], 받는 분 [이름2], 예금주 [이름1] 연락처 [전화번호1]"
    assert pseudonymizer.mapping == {
        "[이름1]": "김민수",
        "[이름2]": "이영희",
        "[전화번호1]": "010-1234-5678",
    }


def test_numbering_continues_across_calls(korean_analyzer):
    pseudonymizer = Pseudonymizer()
    pseudonymize(korean_analyzer, pseudonymizer, "예금주 김민수")
    out = pseudonymize(korean_analyzer, pseudonymizer, "예금주 이영희, 예금주 김민수")
    assert out == "예금주 [이름2], 예금주 [이름1]"


def test_restore_puts_originals_back_and_leaves_other_brackets(korean_analyzer):
    pseudonymizer = Pseudonymizer()
    pseudonymize(korean_analyzer, pseudonymizer, "예금주 김민수 010-1234-5678")
    reply = "[이름1]님, [전화번호1]로 [참고1] 안내드립니다. [이름2]는 모릅니다"
    assert pseudonymizer.restore(reply) == (
        "김민수님, 010-1234-5678로 [참고1] 안내드립니다. [이름2]는 모릅니다"
    )


def test_unlabeled_entity_uses_its_own_name():
    pseudonymizer = Pseudonymizer()
    text = "문의 help@example.com"
    out = pseudonymizer.pseudonymize(
        text, [RecognizerResult("EMAIL_ADDRESS", 3, len(text), 0.9)]
    )
    assert out == "문의 [이메일1]"
    out = pseudonymizer.pseudonymize("A", [RecognizerResult("CRYPTO", 0, 1, 0.9)])
    assert out == "[CRYPTO1]"


def test_partial_overlap_keeps_the_loser_remainder():
    text = "홍길동010"
    results = [
        RecognizerResult("KR_PHONE", 3, 6, 0.5),
        RecognizerResult("PERSON", 0, 4, 0.9),
    ]
    pseudonymizer = Pseudonymizer()
    out = pseudonymizer.pseudonymize(text, results)
    assert out == "[이름1][전화번호1]"
    assert pseudonymizer.restore(out) == text


def test_same_entity_overlaps_merge_into_one(korean_analyzer):
    text = "서울 중구 을지로2가 50"
    pseudonymizer = Pseudonymizer()
    out = pseudonymize(korean_analyzer, pseudonymizer, text)
    assert out == "[주소1]"
    assert pseudonymizer.restore(out) == text


def test_outer_result_wins_over_a_contained_one():
    text = "서울 강남구 테헤란로 152 받는 분 김민수 101호"
    start = text.index("김민수")
    results = [
        RecognizerResult("KR_ADDRESS", 0, len(text), 0.6),
        RecognizerResult("PERSON", start, start + 3, 0.85),
    ]
    assert Pseudonymizer().pseudonymize(text, results) == "[주소1]"


def test_no_digit_escapes_crossing_results():
    text = "010 1234 5678 010 2345 6789"
    results = [
        RecognizerResult("KR_PHONE", 0, 13, 0.85),
        RecognizerResult("CREDIT_CARD", 4, 22, 1.0),
        RecognizerResult("KR_PHONE", 14, 27, 0.85),
    ]
    pseudonymizer = Pseudonymizer()
    out = pseudonymizer.pseudonymize(text, results)
    assert out == "[전화번호1][카드번호1][전화번호2]"
    assert pseudonymizer.restore(out) == text


def test_many_results_are_resolved_quickly():
    text = "010-1234-5678\n" * 20_000
    results = [
        RecognizerResult("KR_PHONE", i * 14, i * 14 + 13, 0.5) for i in range(20_000)
    ]
    start = time.perf_counter()
    Pseudonymizer().pseudonymize(text, results)
    assert time.perf_counter() - start < 2


def test_numbers_skip_placeholders_already_in_the_text():
    text = "답장 양식은 [이름1]님 안녕하세요 입니다. 고객 김민수"
    start = text.index("김민수")
    pseudonymizer = Pseudonymizer()
    masked = pseudonymizer.pseudonymize(
        text, [RecognizerResult("PERSON", start, start + 3, 0.85)]
    )
    assert masked.endswith("[이름2]")
    assert pseudonymizer.restore(masked) == text


def test_numbers_skip_placeholders_seen_in_earlier_messages():
    pseudonymizer = Pseudonymizer()
    pseudonymizer.pseudonymize("[이름1]", [])
    masked = pseudonymizer.pseudonymize(
        "김민수", [RecognizerResult("PERSON", 0, 3, 0.85)]
    )
    assert masked == "[이름2]"
