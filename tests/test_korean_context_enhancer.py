import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrFrnRecognizer,
    KrRrnRecognizer,
)

from presidio_ko import KoreanContextAwareEnhancer

# Presidio 이슈 #2212에서 KrRrnRecognizer에 추가하자고 제안한 단어
PROPOSED_RRN_CONTEXT = KrRrnRecognizer.CONTEXT + [
    "주민등록번호",
    "주민번호",
    "신분증",
    "본인인증",
]


def build_analyzer(nlp_engine, enhancer):
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["ko"],
        context_aware_enhancer=enhancer,
    )
    analyzer.registry.add_recognizer(KrFrnRecognizer())
    analyzer.registry.add_recognizer(KrRrnRecognizer(context=PROPOSED_RRN_CONTEXT))
    return analyzer


def score(analyzer, text, entity):
    [result] = analyzer.analyze(text=text, language="ko", entities=[entity])
    return result.score


# 업스트림 recognizer도 lemma 분절("주민등+록번+호는")로 놓치던 컨텍스트가 붙어야 한다
@pytest.mark.parametrize(
    "text, bare, entity",
    [
        ("외국인등록번호는 900101-5234567", "900101-5234567", "KR_FRN"),
        ("주민등록번호는 900101-1234567", "900101-1234567", "KR_RRN"),
        ("주민번호 900101-1234567", "900101-1234567", "KR_RRN"),
        ("신분증 번호 900101-1234567", "900101-1234567", "KR_RRN"),
    ],
)
def test_boosts_upstream_korean_recognizers(nlp_engine, text, bare, entity):
    analyzer = build_analyzer(nlp_engine, KoreanContextAwareEnhancer())
    assert score(analyzer, text, entity) > score(analyzer, bare, entity)


def test_does_not_modify_callers_nlp_artifacts(nlp_engine):
    text = "주민등록번호는 900101-1234567"
    artifacts = nlp_engine.process_text(text, "ko")
    lemmas, keywords = list(artifacts.lemmas), list(artifacts.keywords)

    build_analyzer(nlp_engine, KoreanContextAwareEnhancer()).analyze(
        text=text, language="ko", nlp_artifacts=artifacts
    )

    assert (artifacts.lemmas, artifacts.keywords) == (lemmas, keywords)


def test_uses_configured_similarity_factor(nlp_engine):
    enhancer = KoreanContextAwareEnhancer(context_similarity_factor=0.1)
    analyzer = build_analyzer(nlp_engine, enhancer)
    text = "외국인등록번호는 900101-5234567"
    # 기본 점수 0.5 + 설정한 0.1 (하드코딩된 0.35가 아님)
    assert score(analyzer, text, "KR_FRN") == pytest.approx(0.6)
