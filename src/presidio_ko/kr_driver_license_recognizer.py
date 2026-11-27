import re

from presidio_analyzer import Pattern
from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrDriverLicenseRecognizer as UpstreamKrDriverLicenseRecognizer,
)

from ._common import END, START

_LABEL = re.compile(
    r"(?:면허(?:번호)?|driver|license)[은는]?\s{0,3}[:：]?\s{0,3}$", re.I
)


class KrDriverLicenseRecognizer(UpstreamKrDriverLicenseRecognizer):
    PATTERNS = [
        Pattern(
            "Driver License (very weak)",
            START + r"\d{2}([- ]?)\d{2}\1\d{6}\1\d{2}" + END,
            0.05,
        )
    ]

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        results = super().analyze(text, entities, nlp_artifacts, regex_flags)
        return [
            r
            for r in results
            if not text[r.start : r.end].isdigit()
            or _LABEL.search(text[max(0, r.start - 20) : r.start])
        ]
