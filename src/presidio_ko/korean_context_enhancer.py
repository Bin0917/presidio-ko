import copy

from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer


class KoreanContextAwareEnhancer(LemmaContextAwareEnhancer):
    """
    컨텍스트 단어를 lemma 대신 토큰 원문과 비교하는 LemmaContextAwareEnhancer.

    한국어 spaCy 모델(ko_core_news_*)의 lemma는 형태소를 "+"로 잇고 분절 위치도
    불규칙해서("연락처가" → "연+락처+가", "은행계좌" → "+은+행+계+좌") 기본 강화기로는
    한국어 컨텍스트 단어가 대부분 매칭되지 않는다. 토큰 원문("연락처가")에는 "연락처"가
    그대로 들어 있으므로 lemma 자리에 원문을 넣고, 윈도·매칭 방식·점수 계산은 기본
    강화기를 그대로 쓴다. 생성자 인자도 LemmaContextAwareEnhancer와 같다.

    사용: AnalyzerEngine(..., context_aware_enhancer=KoreanContextAwareEnhancer())
    """

    def enhance_using_context(
        self, text, raw_results, nlp_artifacts, recognizers, context=None
    ):
        if nlp_artifacts is not None and nlp_artifacts.tokens:
            tokens = nlp_artifacts.tokens
            nlp_artifacts = copy.copy(nlp_artifacts)
            nlp_artifacts.lemmas = [token.text for token in tokens]
            nlp_artifacts.keywords = [
                token.text.lower()
                for token in tokens
                if not (token.is_stop or token.is_punct)
            ]
        return super().enhance_using_context(
            text, raw_results, nlp_artifacts, recognizers, context
        )
