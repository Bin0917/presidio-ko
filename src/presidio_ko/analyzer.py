import logging

from presidio_analyzer import AnalyzerEngine, Pattern, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngine, NlpEngineProvider
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer
from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrBrnRecognizer,
    KrFrnRecognizer,
    KrPassportRecognizer,
    KrRrnRecognizer,
)

from ._common import END, FULL_WIDTH, START
from .korean_context_enhancer import KoreanContextAwareEnhancer
from .kr_driver_license_recognizer import KrDriverLicenseRecognizer
from .kr_phone_recognizer import KrPhoneRecognizer

_REPLACED = ["PhoneRecognizer", "SpacyRecognizer"]
_RRN_CONTEXT = KrRrnRecognizer.CONTEXT + [
    "주민등록번호",
    "주민번호",
    "신분증",
    "본인인증",
]
_CARD_PATTERNS = [
    Pattern(p.name, START + p.regex + END, p.score)
    for p in CreditCardRecognizer.PATTERNS
]


class _CardRecognizer(CreditCardRecognizer):
    _PHONE = KrPhoneRecognizer()

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        cards = super().analyze(text, entities, nlp_artifacts, regex_flags)
        phones = self._PHONE.analyze(text, ["KR_PHONE"])
        if not phones:
            return cards
        blanked = list(text)
        for p in phones:
            blanked[p.start : p.end] = "x" * (p.end - p.start)
        found = super().analyze("".join(blanked), entities, nlp_artifacts, regex_flags)
        covered = {i for r in found + phones for i in range(r.start, r.end)}
        return found + [
            card
            for card in cards
            if any(
                text[i].isdigit() and i not in covered
                for i in range(card.start, card.end)
            )
        ]


class _KoreanAnalyzerEngine(AnalyzerEngine):
    def analyze(self, text, *args, **kwargs):
        return super().analyze(text.translate(FULL_WIDTH), *args, **kwargs)


def create_korean_analyzer(
    model_name: str = "ko_core_news_sm", nlp_engine: NlpEngine | None = None
) -> AnalyzerEngine:
    from . import KOREAN_RECOGNIZERS

    if nlp_engine is None:
        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "ko", "model_name": model_name}],
                "ner_model_configuration": {
                    "model_to_presidio_entity_mapping": {"PS": "PERSON"},
                    "labels_to_ignore": ["LC", "OG", "DT", "QT", "TI"],
                },
            }
        ).create_engine()

    registry = RecognizerRegistry(supported_languages=["ko"])
    logger = logging.getLogger("presidio-analyzer")
    level = logger.level
    logger.setLevel(logging.ERROR)
    try:
        registry.load_predefined_recognizers(languages=["ko"], nlp_engine=nlp_engine)
    finally:
        logger.setLevel(level)
    for name in _REPLACED:
        registry.remove_recognizer(name, "ko")
    upstream = [
        KrRrnRecognizer(context=_RRN_CONTEXT),
        KrFrnRecognizer(),
        KrBrnRecognizer(),
        KrPassportRecognizer(supported_language="ko"),
        KrDriverLicenseRecognizer(),
        _CardRecognizer(
            patterns=_CARD_PATTERNS,
            supported_language="ko",
            name="CreditCardRecognizer",
        ),
    ]
    for recognizer in upstream + KOREAN_RECOGNIZERS:
        registry.add_recognizer(recognizer)
    return _KoreanAnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=KoreanContextAwareEnhancer(),
    )
