import copy

from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer


class KoreanContextAwareEnhancer(LemmaContextAwareEnhancer):
    """
    한국어 문서에서 컨텍스트 단어를 lemma 대신 토큰 원문과 비교하는 강화기.

    한국어 spaCy 모델(ko_core_news_*)의 lemma는 형태소를 "+"로 잇고 분절 위치도
    불규칙해서("연락처가" → "연+락처+가", "은행계좌" → "+은+행+계+좌") 기본 강화기로는
    한국어 컨텍스트 단어가 대부분 매칭되지 않는다. 토큰 원문("연락처가")에는 "연락처"가
    그대로 들어 있으므로 lemma 자리에 원문을 넣고, 윈도·매칭 방식·점수 계산은 기본
    강화기를 그대로 쓴다. 생성자 인자도 LemmaContextAwareEnhancer와 같다.

    spaCy 문서 언어가 ko일 때만 바꾸므로, 다국어 엔진의 다른 언어 문서는 기본 강화기와
    똑같이 동작한다.

    기본 강화기가 주변 단어를 nlp_artifacts.lemmas·keywords에서 고른다는 동작에 기댄다
    (presidio-analyzer 2.2.364에서 확인). 업스트림이 이 방식을 바꾸면 tests가 깨진다.

    사용: AnalyzerEngine(..., context_aware_enhancer=KoreanContextAwareEnhancer())
    """

    def enhance_using_context(
        self, text, raw_results, nlp_artifacts, recognizers, context=None
    ):
        tokens = nlp_artifacts.tokens if nlp_artifacts is not None else None
        if tokens and tokens.lang_ == "ko":
            nlp_artifacts = copy.copy(nlp_artifacts)
            nlp_artifacts.lemmas = [token.text for token in tokens]
            # 결과마다 윈도를 훑으며 멤버십을 확인하므로 set으로 둔다
            nlp_artifacts.keywords = {
                token.text.lower()
                for token in tokens
                if not (token.is_stop or token.is_punct)
            }
        return super().enhance_using_context(
            text, raw_results, nlp_artifacts, recognizers, context
        )
