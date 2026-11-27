import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_ko import (
    KOREAN_RECOGNIZERS,
    KoreanContextAwareEnhancer,
    create_korean_analyzer,
)


@pytest.fixture(scope="session")
def nlp_engine():
    return NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "ko", "model_name": "ko_core_news_sm"}],
        }
    ).create_engine()


@pytest.fixture(scope="session")
def analyzer(nlp_engine):
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=KoreanContextAwareEnhancer(),
    )
    for recognizer in KOREAN_RECOGNIZERS:
        analyzer.registry.add_recognizer(recognizer)
    return analyzer


@pytest.fixture(scope="session")
def korean_analyzer():
    return create_korean_analyzer()
