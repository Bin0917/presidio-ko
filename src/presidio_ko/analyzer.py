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

from ._common import END, START
from .korean_context_enhancer import KoreanContextAwareEnhancer
from .kr_driver_license_recognizer import KrDriverLicenseRecognizer
from .kr_phone_recognizer import KrPhoneRecognizer

# 업스트림 PhoneRecognizer는 KR_PHONE과 같은 번호를 PHONE_NUMBER로 한 번 더 보고하고,
# SpacyRecognizer는 PERSON을 KrPersonRecognizer와 따로 낸다
_REPLACED = ["PhoneRecognizer", "SpacyRecognizer"]
_RRN_CONTEXT = KrRrnRecognizer.CONTEXT + [
    "주민등록번호",
    "주민번호",
    "신분증",
    "본인인증",
]
# 업스트림 카드 패턴은 `\b`로 시작해서 "010-1234-5678 010-2345-6789"의 가운데
# "1234-5678 010-2345"처럼 더 긴 번호 안에서 Luhn을 통과하는 16자리도 잡는다
_CARD_PATTERNS = [
    Pattern(p.name, START + p.regex + END, p.score)
    for p in CreditCardRecognizer.PATTERNS
]


class _CardRecognizer(CreditCardRecognizer):
    """
    전화번호를 가로지르는 카드 후보를 버린다. "010 1234 5678 010 2345 6789"의
    "1234 5678 010 2345"는 공백 구분이라 경계 검사를 통과한다. 카드 경계에서 공백
    뒤 숫자를 막으면 공백으로 이어 쓴 카드 두 장도 놓친다.
    """

    _PHONE = KrPhoneRecognizer()

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        phones = self._PHONE.analyze(text, ["KR_PHONE"])
        return [
            card
            for card in super().analyze(text, entities, nlp_artifacts, regex_flags)
            if not any(
                p.start < card.start < p.end < card.end
                or card.start < p.start < card.end < p.end
                for p in phones
            )
        ]


def create_korean_analyzer(
    model_name: str = "ko_core_news_sm", nlp_engine: NlpEngine | None = None
) -> AnalyzerEngine:
    """한국 인식기와 한국어 컨텍스트 강화기가 켜진 AnalyzerEngine."""
    from . import KOREAN_RECOGNIZERS

    if nlp_engine is None:
        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "ko", "model_name": model_name}],
                # LC·OG는 실측에서 오탐이 많아 PS(사람)만 쓴다
                "ner_model_configuration": {
                    "model_to_presidio_entity_mapping": {"PS": "PERSON"},
                    "labels_to_ignore": ["LC", "OG", "DT", "QT", "TI"],
                },
            }
        ).create_engine()

    registry = RecognizerRegistry(supported_languages=["ko"])
    # 다른 언어 인식기를 건너뛸 때마다 경고가 열 줄 넘게 찍힌다
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
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=KoreanContextAwareEnhancer(),
    )
