import re
from bisect import bisect_left, bisect_right
from collections.abc import Callable

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from ._common import FULL_WIDTH, check_results, drop_overlaps


def _mask_digits(text: str, keep: Callable[[int, int], bool]) -> str:
    total = sum(c.isdigit() for c in text)
    out, i = [], 0
    for c in text:
        if c.isdigit():
            out.append(c if keep(i, total) else "*")
            i += 1
        else:
            out.append(c)
    return "".join(out)


def mask_person(name: str) -> str:
    return "".join(c if i in (0, 2) else "*" for i, c in enumerate(name))


def mask_phone(number: str) -> str:
    return _mask_digits(number, lambda i, n: i < n - 4)


def mask_resident_number(number: str) -> str:
    return _mask_digits(number, lambda i, n: i < 7)


def mask_bank_account(account: str) -> str:
    separator = re.search(r"\D", account)
    first = separator.start() if separator else 3
    return _mask_digits(account, lambda i, n: i < first or i >= n - 2)


_ADDRESS_NUMBER = re.compile(
    r"[로길동리가](?:\s?\d+(?:번길|길|가))?(?=\s?(?:산\s?)?\d)"
)
_UNIT_NAME = re.compile(r"[A-Za-z]+(?=동)|(?<![가-힣])(?:에이|비|씨|디)(?=동)")


def mask_address(address: str) -> str:
    start = _ADDRESS_NUMBER.search(address)
    if not start:
        return address
    tail = _UNIT_NAME.sub(lambda m: "*" * len(m.group()), address[start.end() :])
    return address[: start.end()] + re.sub(r"\d", "*", tail)


def mask_email(email: str) -> str:
    local = email[: len(email.translate(FULL_WIDTH).partition("@")[0])]
    return local[: 2 if len(local) > 2 else 1] + "****" + email[len(local) :]


def mask_credit_card(number: str) -> str:
    return _mask_digits(number, lambda i, n: i < 6 or i >= n - 4)


def mask_vehicle_plate(plate: str) -> str:
    return _mask_digits(plate, lambda i, n: not n - 4 <= i < n - 2)


def mask_all(value: str) -> str:
    return "".join("*" if c.isalnum() else c for c in value)


_RULES = {
    "KR_BRN": mask_all,
    "KR_PASSPORT": mask_all,
    "KR_DRIVER_LICENSE": mask_all,
    "KR_HEALTH_INSURANCE": mask_all,
    "PERSON": mask_person,
    "KR_PHONE": mask_phone,
    "KR_RRN": mask_resident_number,
    "KR_FRN": mask_resident_number,
    "KR_BANK_ACCOUNT": mask_bank_account,
    "KR_ADDRESS": mask_address,
    "EMAIL_ADDRESS": mask_email,
    "CREDIT_CARD": mask_credit_card,
    "KR_VEHICLE_PLATE": mask_vehicle_plate,
}


def korean_operators() -> dict[str, OperatorConfig]:
    operators = {
        entity: OperatorConfig("custom", {"lambda": rule})
        for entity, rule in _RULES.items()
    }
    operators["DEFAULT"] = OperatorConfig("replace")
    return operators


_ENGINE = AnonymizerEngine()
_HIDING = {"replace", "redact", "hash", "encrypt"}


def korean_mask(
    text: str,
    results: list[RecognizerResult],
    operators: dict[str, OperatorConfig] | None = None,
) -> str:
    operators = korean_operators() if operators is None else operators
    check_results(text, results)
    kept = drop_overlaps(results)
    starts = [k.start for k in kept]
    ends = [k.end for k in kept]
    near = [[] for _ in kept]
    for r in results:
        for i in range(bisect_right(ends, r.start), bisect_left(starts, r.end)):
            near[i].append(r)
    out, pos = [], 0
    for k, rs in zip(kept, near, strict=True):
        out += [text[pos : k.start], _mask_with_inner(text, k, rs, operators)]
        pos = k.end
    return "".join(out) + text[pos:]


def _mask_with_inner(text, k, results, operators) -> str:
    value = text[k.start : k.end]
    outer = _apply(k.entity_type, value, operators)
    others = [
        r
        for r in results
        if (r.entity_type in _RULES or r.entity_type == k.entity_type)
        and (r.entity_type, r.start, r.end) != (k.entity_type, k.start, k.end)
    ]
    if not others:
        return outer
    if len(outer) != len(value):
        return outer if _hides(k.entity_type, operators) else mask_all(value)
    chars, replaced = list(outer), []
    for r in others:
        original = text[r.start : r.end]
        masked = _apply(r.entity_type, original, operators)
        inside = k.start <= r.start and r.end <= k.end
        if len(masked) != len(original):
            if inside and _hides(r.entity_type, operators):
                replaced.append(
                    RecognizerResult(
                        r.entity_type, r.start - k.start, r.end - k.start, r.score
                    )
                )
                continue
            masked = mask_all(original)
        for i in range(max(r.start, k.start), min(r.end, k.end)):
            if masked[i - r.start] != text[i]:
                chars[i - k.start] = masked[i - r.start]
    for r in reversed(drop_overlaps(replaced)):
        chars[r.start : r.end] = _apply(
            r.entity_type, value[r.start : r.end], operators
        )
    return "".join(chars)


def _apply(entity: str, value: str, operators: dict[str, OperatorConfig]) -> str:
    result = RecognizerResult(entity, 0, len(value), 1.0)
    return _ENGINE.anonymize(value, [result], operators).text


def _hides(entity: str, operators: dict[str, OperatorConfig]) -> bool:
    operator = operators.get(entity, operators.get("DEFAULT"))
    return operator is None or operator.operator_name in _HIDING
