import re

from presidio_analyzer import RecognizerResult

from ._common import ENTITY_LABELS

_PLACEHOLDER = re.compile(r"\[[^\[\]]+\]")


class Pseudonymizer:
    """
    개인정보를 "[이름1]" 같은 자리표시자로 바꿔 LLM에 보내고, 응답에서 되돌린다.

    같은 원문은 같은 자리표시자를 받고, 번호는 여러 번 호출해도 이어진다.
    한 대화에는 한 인스턴스를 쓴다. AnonymizerEngine은 이웃한 같은 종류 결과를
    하나로 합쳐서("김민수 이영희") 되돌릴 수 없으므로 쓰지 않는다.
    """

    def __init__(self) -> None:
        self.mapping: dict[str, str] = {}
        self._placeholders: dict[tuple[str, str], str] = {}

    def pseudonymize(self, text: str, results: list[RecognizerResult]) -> str:
        kept: list[RecognizerResult] = []
        for r in sorted(results, key=lambda r: (-r.score, r.start - r.end, r.start)):
            if all(r.end <= k.start or k.end <= r.start for k in kept):
                kept.append(r)
        out, pos = [], 0
        for r in sorted(kept, key=lambda r: r.start):
            out.append(text[pos : r.start])
            out.append(self._placeholder(r.entity_type, text[r.start : r.end]))
            pos = r.end
        out.append(text[pos:])
        return "".join(out)

    def restore(self, text: str) -> str:
        return _PLACEHOLDER.sub(lambda m: self.mapping.get(m.group(), m.group()), text)

    def _placeholder(self, entity: str, original: str) -> str:
        if (entity, original) not in self._placeholders:
            label = ENTITY_LABELS.get(entity, entity)
            count = sum(k[0] == entity for k in self._placeholders) + 1
            placeholder = f"[{label}{count}]"
            self._placeholders[entity, original] = placeholder
            self.mapping[placeholder] = original
        return self._placeholders[entity, original]
