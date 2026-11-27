import logging

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngine, NlpEngineProvider
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer
from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrBrnRecognizer,
    KrFrnRecognizer,
    KrPassportRecognizer,
    KrRrnRecognizer,
)

from .korean_context_enhancer import KoreanContextAwareEnhancer
from .kr_driver_license_recognizer import KrDriverLicenseRecognizer

# 업스트림 PhoneRecognizer는 KR_PHONE과 같은 번호를 PHONE_NUMBER로 한 번 더 보고하고,
# SpacyRecognizer는 PERSON을 KrPersonRecognizer와 따로 낸다
_REPLACED = ["PhoneRecognizer", "SpacyRecognizer"]


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
        KrRrnRecognizer(),
        KrFrnRecognizer(),
        KrBrnRecognizer(),
        KrPassportRecognizer(supported_language="ko"),
        KrDriverLicenseRecognizer(),
        CreditCardRecognizer(supported_language="ko"),
    ]
    for recognizer in upstream + KOREAN_RECOGNIZERS:
        registry.add_recognizer(recognizer)
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=KoreanContextAwareEnhancer(),
    )
