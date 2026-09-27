from presidio_analyzer import PatternRecognizer, RecognizerResult


class SurfaceContextRecognizer(PatternRecognizer):
    """
    컨텍스트 단어를 lemma가 아닌 원문 어절에서 찾는 PatternRecognizer.

    Presidio 기본 LemmaContextAwareEnhancer는 컨텍스트 단어를 lemma와 비교한다. 그런데
    한국어 spaCy 모델(ko_core_news_*)의 lemma는 형태소를 "+"로 잇고 분절 위치도 불규칙해서
    ("연락처가" → "연+락처+가", "은행계좌" → "+은+행+계+좌") 한국어 컨텍스트 단어가 대부분
    매칭되지 않는다.

    그래서 매치 앞 5어절(기본 강화기의 context_prefix_count와 같음)의 원문에서 컨텍스트
    단어를 부분 문자열로 찾고, 점수도 기본 강화기와 똑같이 +0.35(최소 0.4, 최대 1.0) 올린다.
    여기서 못 찾은 결과는 표시하지 않으므로 기본 강화기가 이어서 한 번 더 확인한다.
    """

    def enhance_using_context(
        self,
        text,
        raw_recognizer_results,
        other_raw_recognizer_results,
        nlp_artifacts,
        context=None,
    ):
        for result in raw_recognizer_results:
            preceding = " ".join(text[: result.start].rsplit(maxsplit=5)[-5:]).lower()
            word = next((w for w in self.context if w.lower() in preceding), None)
            if word is None:
                continue
            result.score = min(max(result.score + 0.35, 0.4), 1.0)
            result.analysis_explanation.set_supportive_context_word(word)
            result.analysis_explanation.set_improved_score(result.score)
            # 기본 강화기가 같은 결과를 두 번 올리지 않도록 표시
            result.recognition_metadata[
                RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY
            ] = True
        return raw_recognizer_results
