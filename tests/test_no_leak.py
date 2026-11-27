import random
import re

import pytest

from presidio_ko import Pseudonymizer, korean_mask
from presidio_ko.masking import _RULES

SEPARATORS = [" ", "  ", ", ", ",", "/", "\n", " 및 ", "·"]


def digits(rng, n):
    return "".join(rng.choice("0123456789") for _ in range(n))


def rrn(rng):
    body = f"{rng.randint(70, 99)}{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"
    body += rng.choice("12") + digits(rng, 5)
    weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    check = (11 - sum(int(d) * w for d, w in zip(body, weights, strict=True)) % 11) % 10
    return f"{body[:6]}-{body[6:]}{check}"


def card(rng):
    body = "4" + digits(rng, 14)
    total = 0
    for i, d in enumerate(reversed(body)):
        n = int(d) * (2 if i % 2 == 0 else 1)
        total += n - 9 if n > 9 else n
    number = body + str((10 - total % 10) % 10)
    sep = rng.choice(["-", " ", ""])
    return sep.join(number[i : i + 4] for i in range(0, 16, 4))


def phone(rng):
    sep = rng.choice(["-", " ", ""])
    return f"010{sep}{rng.randint(2000, 9999)}{sep}{digits(rng, 4)}"


def address(rng):
    value = rng.choice(["서울 강남구 테헤란로 ", "서울 중구 을지로2가 "])
    value += str(rng.randint(10, 999))
    if rng.random() < 0.5:
        value += f", {rng.randint(101, 120)}동 {rng.randint(1001, 2504)}호"
    return value


GENERATORS = [
    ("KR_PHONE", "연락처 ", phone),
    ("KR_RRN", "주민번호 ", rrn),
    ("CREDIT_CARD", "카드 ", card),
    (
        "KR_BANK_ACCOUNT",
        "국민은행 ",
        lambda rng: f"{digits(rng, 6)}-{digits(rng, 2)}-{digits(rng, 6)}",
    ),
    ("KR_ADDRESS", "", address),
    ("EMAIL_ADDRESS", "", lambda rng: f"user{digits(rng, 6)}@example.com"),
    (
        "KR_VEHICLE_PLATE",
        "차량 ",
        lambda rng: f"{rng.randint(10, 99)}가 {digits(rng, 4)}",
    ),
    ("PERSON", "성명 ", lambda rng: rng.choice(["김민수", "이영희", "박하은"])),
]


def windows(text):
    return {
        run[i : i + 4]
        for run in re.findall(r"[0-9A-Za-z가-힣*]+", text)
        for i in range(len(run) - 3)
        if "*" not in run[i : i + 4]
    }


def generate(rng):
    parts, values, pos = [], [], 0
    for _ in range(rng.randint(2, 5)):
        entity, label, make = rng.choice(GENERATORS)
        if parts:
            sep = rng.choice(SEPARATORS)
            if entity == "EMAIL_ADDRESS" and sep == "/":
                sep = " / "
            parts.append(sep)
            pos += len(sep)
        value = make(rng)
        if rng.random() < 0.5 and entity != "KR_BANK_ACCOUNT":
            label = ""
        parts.append(label + value)
        values.append((entity, pos + len(label), value))
        pos += len(label) + len(value)
    return "".join(parts), values


def cases(n):
    rng = random.Random(20261127)
    return [generate(rng) for _ in range(n)]


@pytest.mark.parametrize(("text", "values"), cases(500))
def test_no_hidden_run_survives(korean_analyzer, text, values):
    results = korean_analyzer.analyze(text=text, language="ko")
    detected = [
        (entity, value)
        for entity, start, value in values
        if any(r.start < start + len(value) and start < r.end for r in results)
    ]
    shown = windows(text)
    for _, _, value in values:
        shown -= windows(value)
    hidden = set()
    for entity, value in detected:
        visible = windows(_RULES[entity](value))
        shown |= visible
        hidden |= windows(value) - visible

    masked = korean_mask(text, results)
    assert not (windows(masked) & hidden) - shown, masked

    pseudonymizer = Pseudonymizer()
    prompt = pseudonymizer.pseudonymize(text, results)
    assert not windows(prompt) & hidden, prompt
    assert pseudonymizer.restore(prompt) == text
