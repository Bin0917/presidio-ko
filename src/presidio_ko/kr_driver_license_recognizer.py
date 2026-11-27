import re

from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrDriverLicenseRecognizer as UpstreamKrDriverLicenseRecognizer,
)

# 구분자 없는 12자리는 주문·송장 번호와 구별되지 않아 라벨이 바로 앞일 때만 받는다
_LABEL = re.compile(
    r"(?:면허(?:번호)?|driver|license)[은는]?\s{0,3}[:：]?\s{0,3}$", re.I
)


class KrDriverLicenseRecognizer(UpstreamKrDriverLicenseRecognizer):
    """업스트림 운전면허 인식기에서 라벨 없는 구분자 없는 12자리를 뺀다."""

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        results = super().analyze(text, entities, nlp_artifacts, regex_flags)
        return [
            r
            for r in results
            if not text[r.start : r.end].isdigit()
            or _LABEL.search(text[max(0, r.start - 20) : r.start])
        ]
