import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_ko import KOREAN_RECOGNIZERS, KoreanContextAwareEnhancer


@pytest.fixture(scope="session")
def nlp_engine():
    """한국어 spaCy NLP 엔진. ko_core_news_sm이 없으면 Presidio가 내려받는다."""
    return NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "ko", "model_name": "ko_core_news_sm"}],
        }
    ).create_engine()


@pytest.fixture(scope="session")
def analyzer(nlp_engine):
    """README와 같은 구성의 한국어 AnalyzerEngine."""
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=KoreanContextAwareEnhancer(),
    )
    for recognizer in KOREAN_RECOGNIZERS:
        analyzer.registry.add_recognizer(recognizer)
    return analyzer
