import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_ko import KrPhoneRecognizer


@pytest.fixture(scope="session")
def analyzer():
    """README와 같은 한국어 AnalyzerEngine. ko_core_news_sm이 없으면 Presidio가 내려받는다."""
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "ko", "model_name": "ko_core_news_sm"}],
        }
    ).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["ko"])
    analyzer.registry.add_recognizer(KrPhoneRecognizer())
    return analyzer
