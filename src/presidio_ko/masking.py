import bisect
import re
from collections.abc import Callable

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from ._common import FULL_WIDTH, drop_overlaps


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


def korean_mask(
    text: str,
    results: list[RecognizerResult],
    operators: dict[str, OperatorConfig] | None = None,
) -> str:
    operators = korean_operators() if operators is None else operators
    kept = drop_overlaps(results)
    result = _ENGINE.anonymize(text, kept, operators, merge_entities_with_spaces=False)
    return _mask_contained(text, results, kept, operators, result)


def _mask_contained(text, results, kept, operators, result) -> str:
    starts = [k.start for k in kept]
    items = sorted(result.items, key=lambda item: item.start)
    out = list(result.text)
    for r in results:
        i = bisect.bisect_right(starts, r.start) - 1
        if i < 0 or r.end > kept[i].end or kept[i].entity_type == r.entity_type:
            continue
        k, item = kept[i], items[i]
        operator = operators.get(r.entity_type)
        if operator is None or operator.operator_name != "custom":
            continue
        original = text[r.start : r.end]
        masked = operator.params["lambda"](original)
        if len(masked) != len(original) or item.end - item.start != k.end - k.start:
            continue
        offset = item.start + r.start - k.start
        for j, (before, after) in enumerate(zip(original, masked, strict=True)):
            if before != after:
                out[offset + j] = after
    return "".join(out)
