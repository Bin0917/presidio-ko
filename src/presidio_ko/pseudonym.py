import re

from presidio_analyzer import RecognizerResult

from ._common import ENTITY_LABELS, drop_overlaps

_PLACEHOLDER = re.compile(r"\[[^\[\]]+\]")


class Pseudonymizer:
    def __init__(self) -> None:
        self.mapping: dict[str, str] = {}
        self._placeholders: dict[tuple[str, str], str] = {}
        self._reserved: set[str] = set()
        self._numbers: dict[str, int] = {}

    def pseudonymize(self, text: str, results: list[RecognizerResult]) -> str:
        self._reserved.update(_PLACEHOLDER.findall(text))
        out, pos = [], 0
        for r in drop_overlaps(results):
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
            number = self._numbers.get(entity, 0) + 1
            placeholder = f"[{label}{number}]"
            while placeholder in self._reserved or placeholder in self.mapping:
                number += 1
                placeholder = f"[{label}{number}]"
            self._numbers[entity] = number
            self._placeholders[entity, original] = placeholder
            self.mapping[placeholder] = original
        return self._placeholders[entity, original]
