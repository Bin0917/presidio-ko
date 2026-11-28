import copy

from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer


class KoreanContextAwareEnhancer(LemmaContextAwareEnhancer):
    def enhance_using_context(
        self, text, raw_results, nlp_artifacts, recognizers, context=None
    ):
        tokens = nlp_artifacts.tokens if nlp_artifacts is not None else None
        if tokens and tokens.lang_ == "ko":
            nlp_artifacts = copy.copy(nlp_artifacts)
            nlp_artifacts.lemmas = [token.text for token in tokens]
            nlp_artifacts.keywords = {
                token.text.lower()
                for token in tokens
                if not (token.is_stop or token.is_punct)
            }
        return super().enhance_using_context(
            text, raw_results, nlp_artifacts, recognizers, context
        )
