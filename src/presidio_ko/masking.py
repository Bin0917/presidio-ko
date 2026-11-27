"""개인정보위 고객센터 권고와 ISMS-P 관행을 따른 한국식 부분 마스킹.

구분자는 그대로 두고 글자·숫자만 `*`로 바꾼다. 각 규칙은 str -> str 순수 함수다.
"""

import bisect
import re
from collections.abc import Callable

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from ._common import drop_overlaps


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


# 도로명(로·길)이나 지번(동·리·가) 끝 바로 뒤에 번호가 온다.
# "3길", "152번길", "2가"는 이름의 일부다
_ADDRESS_NUMBER = re.compile(
    r"[로길동리가](?:\s?\d+(?:번길|길|가))?(?=\s?(?:산\s?)?\d)"
)
_UNIT_NAME = re.compile(r"[A-Za-z]+(?=동)|(?<![가-힣])(?:에이|비|씨|디)(?=동)")


def mask_address(address: str) -> str:
    """도로명·지번 뒤 숫자와 동 이름(A동, 에이동)을 가린다. 번호가 없으면 둔다."""
    start = _ADDRESS_NUMBER.search(address)
    if not start:
        return address
    tail = _UNIT_NAME.sub(lambda m: "*" * len(m.group()), address[start.end() :])
    return address[: start.end()] + re.sub(r"\d", "*", tail)


def mask_email(email: str) -> str:
    local, at, domain = email.partition("@")
    return local[: 2 if len(local) > 2 else 1] + "****" + at + domain


def mask_credit_card(number: str) -> str:
    return _mask_digits(number, lambda i, n: i < 6 or i >= n - 4)


def mask_vehicle_plate(plate: str) -> str:
    return _mask_digits(plate, lambda i, n: not n - 4 <= i < n - 2)


def mask_all(value: str) -> str:
    """부분 표시 관행이 없는 식별번호는 구분자만 남기고 모두 가린다."""
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
    """AnonymizerEngine.anonymize(operators=...)에 넘기는 한국식 마스킹 설정."""
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
    """
    분석 결과를 한국식으로 가린 문자열을 돌려준다.

    AnonymizerEngine.anonymize는 기본값으로 공백 하나로 이웃한 같은 종류 결과를 합친다.
    "010-1234-5678 010-2345-6789"가 한 번호로 합쳐지면 뒤 4자리만 가려져 앞 번호가
    그대로 보이므로 합치지 않는다. 겹치는 결과는 엔진이 글자를 겹쳐 쓰므로
    drop_overlaps로 먼저 정리한다.
    """
    operators = operators or korean_operators()
    kept = drop_overlaps(results)
    result = _ENGINE.anonymize(text, kept, operators, merge_entities_with_spaces=False)
    return _mask_contained(text, results, kept, operators, result)


def _mask_contained(text, results, kept, operators, result) -> str:
    """
    다른 종류 결과 안에 묻혀 빠진 결과가 가리는 글자를 출력에서도 가린다.

    주소 규칙은 숫자만 가리므로 주소 범위에 들어간 이름이 그대로 보인다.
    바깥과 안쪽 규칙이 모두 길이를 지키는 custom 규칙일 때 두 규칙의 가림을 합친다.
    """
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
