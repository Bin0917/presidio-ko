"""개인정보위 고객센터 권고와 ISMS-P 관행을 따른 한국식 부분 마스킹.

구분자는 그대로 두고 글자·숫자만 `*`로 바꾼다. 각 규칙은 str -> str 순수 함수다.
"""

import re
from collections.abc import Callable

from presidio_anonymizer.entities import OperatorConfig


def _mask_digits(text: str, keep: Callable[[int, int], bool]) -> str:
    """숫자 중 keep(번째, 전체 개수)가 False인 것만 *로 바꾼다."""
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


def mask_address(address: str) -> str:
    """도로명·지번 뒤 첫 번호부터 숫자를 가린다. 번호를 못 찾으면 그대로 둔다."""
    start = re.search(r"(?<=[로길동리가산])\s+(?=\d)", address)
    if not start:
        return address
    return address[: start.end()] + re.sub(r"\d", "*", address[start.end() :])


def mask_email(email: str) -> str:
    local, at, domain = email.partition("@")
    return local[: 2 if len(local) > 2 else 1] + "****" + at + domain


def mask_credit_card(number: str) -> str:
    return _mask_digits(number, lambda i, n: i < 6 or i >= n - 4)


def mask_vehicle_plate(plate: str) -> str:
    return _mask_digits(plate, lambda i, n: not n - 4 <= i < n - 2)


_RULES = {
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
    """AnonymizerEngine.anonymize(operators=...)에 넘기는 한국식 마스킹 설정."""
    operators = {
        entity: OperatorConfig("custom", {"lambda": rule})
        for entity, rule in _RULES.items()
    }
    operators["DEFAULT"] = OperatorConfig("replace")
    return operators
