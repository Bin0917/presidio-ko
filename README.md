# presidio-ko

[Microsoft Presidio](https://github.com/microsoft/presidio)에 **한국 전화번호(`KR_PHONE`)** 와
**은행 계좌번호(`KR_BANK_ACCOUNT`)** recognizer를 더하는 패키지입니다.

주민등록번호·외국인등록번호 같은 한국형 recognizer는 Presidio 업스트림에 체크섬 검증까지 이미
들어 있으므로 다시 만들지 않고 그대로 가져다 씁니다. 이 패키지는 업스트림에 **없는 두 가지만**
채웁니다.

## 업스트림에 이미 있는 것 vs 이 패키지가 채우는 것

presidio-analyzer 2.2.364 기준입니다.

| 엔티티 | 제공 | 검증 | 비고 |
|---|---|---|---|
| `KR_RRN` 주민등록번호 | Presidio `KrRrnRecognizer` | 체크섬(mod 11), 지역코드 | 컨텍스트가 영어뿐 → [#2212](https://github.com/microsoft/presidio/issues/2212) |
| `KR_FRN` 외국인등록번호 | Presidio `KrFrnRecognizer` | 체크섬 | |
| `KR_BRN` 사업자등록번호 | Presidio `KrBrnRecognizer` | 체크섬 | |
| `KR_PASSPORT` 여권번호 | Presidio `KrPassportRecognizer` | 형식 | 기본 `supported_language`가 `"kr"`이라 `language="ko"` 분석에서 빠짐. `KrPassportRecognizer(supported_language="ko")`로 등록 |
| `KR_DRIVER_LICENSE` 운전면허번호 | Presidio `KrDriverLicenseRecognizer` | 지역코드 | |
| `PHONE_NUMBER` 전화번호(범용) | Presidio `PhoneRecognizer` | libphonenumber | `supported_regions=["KR"]`를 주면 한국 번호도 잡음(`+82` 국제 형식 포함). 기본 컨텍스트는 영어 |
| **`KR_PHONE`** 휴대폰·유선전화 | **이 패키지** `KrPhoneRecognizer` | 형식 | 한국 번호 전용 엔티티, 한국어 컨텍스트 |
| **`KR_BANK_ACCOUNT`** 계좌번호 | **이 패키지** `KrBankAccountRecognizer` | 형식(체크섬 불가) | 업스트림에 해당 recognizer 없음 |

한국 번호를 `PHONE_NUMBER`로만 잡아도 된다면 업스트림
`PhoneRecognizer(supported_regions=["KR"], supported_language="ko")`로 충분합니다.
`KrPhoneRecognizer`는 한국 번호를 별도 엔티티로 다루고 한국어 컨텍스트로 점수를 올리고 싶을 때
씁니다.

## 설치

```bash
pip install -e .
python -m spacy download ko_core_news_sm
```

PyPI에는 아직 올리지 않았으므로 이 저장소를 받아 설치합니다. `ko_core_news_sm`은 한국어 문장을
분석하는 spaCy 모델입니다.

## 사용 예시

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers.country_specific.korea import (
    KrRrnRecognizer, KrFrnRecognizer, KrBrnRecognizer,
)
from presidio_ko import (
    KoreanContextAwareEnhancer, KrPhoneRecognizer, KrBankAccountRecognizer,
)

# 기본 AnalyzerEngine()은 영어 모델만 올리므로 한국어 NLP 엔진을 넘겨서 만든다
nlp_engine = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "ko", "model_name": "ko_core_news_sm"}],
}).create_engine()
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["ko"],
    context_aware_enhancer=KoreanContextAwareEnhancer(),  # 한국어 컨텍스트 매칭
)
for r in [KrRrnRecognizer(), KrFrnRecognizer(), KrBrnRecognizer(),
          KrPhoneRecognizer(), KrBankAccountRecognizer()]:
    analyzer.registry.add_recognizer(r)

text = "제 연락처는 010-1234-5678이고 계좌는 123-456-789012 이에요"
results = analyzer.analyze(text=text, language="ko")
for r in results:
    print(r.entity_type, text[r.start:r.end], round(r.score, 2))
```

출력:

```
KR_PHONE 010-1234-5678 0.85
KR_BANK_ACCOUNT 123-456-789012 0.75
```

이 패키지의 두 recognizer만 등록하려면 `presidio_ko.KOREAN_RECOGNIZERS`를 쓰면 됩니다.

`AnalyzerEngine()`을 인자 없이 쓰면 영어 spaCy 모델만 `en`으로 올라가서, `language="ko"`로
분석할 때 NLP 엔진이 `ko` 모델을 찾지 못해 `KeyError: 'ko'`로 실패합니다. 업스트림 한국형
recognizer도 기본 언어가 `ko`이므로 위처럼 한국어 NLP 엔진을 넘겨야 합니다.

## Presidio 이슈 #2212

[microsoft/presidio#2212](https://github.com/microsoft/presidio/issues/2212): 한국어 문서에서
`KR_RRN` 컨텍스트 강화가 발동하지 않는 문제입니다.

`KrRrnRecognizer.CONTEXT`에는 영어 단어만 있습니다.

```
["Korean RRN", "Korean Resident Registration Number",
 "Resident Registration Number", "RRN", "rrn", "rrn#"]
```

같은 파일의 `KrFrnRecognizer`는 `외국인등록번호`, `외국인번호`를 갖고 있는데 주민등록번호만 빠져
있어서, "주민등록번호: 900101-1234567" 같은 한국어 문서에서 컨텍스트로 점수가 오르지 않습니다.
이슈는 `주민등록번호`, `주민번호`, `신분증`, `본인인증` 추가를 제안하고, 이를 반영한 PR
[#2213](https://github.com/microsoft/presidio/pull/2213),
[#2258](https://github.com/microsoft/presidio/pull/2258)이 열려 있습니다(2026-09-28 기준 미병합).

**단어 추가만으로는 부족합니다.** Presidio 기본 컨텍스트 강화기(`LemmaContextAwareEnhancer`)는
컨텍스트 단어를 원문이 아니라 lemma와 비교하는데, 한국어 spaCy 모델의 lemma는 형태소를 `+`로 잇고
분절 위치도 불규칙합니다. 제안된 네 단어를 `CONTEXT`에 넣고 `ko_core_news_sm` 3.8.0으로 돌려 본
결과입니다.

| 문장 | 첫 어절의 lemma | 점수 |
|---|---|---|
| `주민등록번호: 900101-1234567` | `주민등록번호` | 0.85 (강화됨) |
| `주민등록번호는 900101-1234567` | `주민등+록번+호는` | 0.5 (강화 안 됨) |
| `주민번호 900101-1234567` | `주민번+호` | 0.5 (강화 안 됨) |
| `신분증 번호 900101-1234567` | `신분+증` | 0.5 (강화 안 됨) |
| `본인인증 900101-1234567` | `본인인증` | 0.85 (강화됨) |

## 한국어 컨텍스트 강화 방식

위와 같은 lemma 분절 때문에 `연락처가` → `연+락처+가`, `전화번호로` → `전+화번+호로`,
`은행계좌` → `+은+행+계+좌`가 되어, 기본 강화기로는 `연락처`, `전화`, `계좌` 같은 단어가 대부분
매칭되지 않습니다.

그래서 두 recognizer는 Presidio가 recognizer별 확장점으로 제공하는 `enhance_using_context`를
오버라이드해서, 매치 **앞 5어절의 원문**에서 컨텍스트 단어를 부분 문자열로 찾습니다. 점수 규칙은
기본 강화기와 같습니다(+0.35, 최소 0.4, 최대 1.0). 여기서 못 찾은 결과는 기본 강화기가 이어서
확인하고, 이미 올린 결과는 두 번 올리지 않습니다.

매치 뒤쪽 단어는 보지 않습니다(Presidio 기본값과 같음). `110-123-456789 (신한은행)`처럼 뒤에만
단서가 있으면 점수가 오르지 않습니다.

## 인식 범위와 한계

### KR_PHONE

| 종류 | 형식 | 점수 (컨텍스트 있으면) |
|---|---|---|
| 휴대폰 | `010/011/016/017/018/019` + 3~4자리 + 4자리. 구분자(`-`, 공백) 생략 가능 | 0.5 (0.85) |
| 유선 | `02`, `031~033`, `041~044`, `051~055`, `061~064`, `070` + 3~4자리 + 4자리. 구분자 필수 | 0.4 (0.75) |

- 컨텍스트 단어: `전화`, `연락처`, `휴대폰`, `핸드폰`, `phone`, `mobile`
- 경계는 `\b` 대신 숫자 lookaround(`(?<!\d)`, `(?!\d)`)를 씁니다. 한글도 정규식에서 단어
  문자(`\w`)라 `010-1234-5678로`처럼 조사가 붙으면 `8`과 `로` 사이에 `\b`가 성립하지 않기
  때문입니다.
- 구분자 없는 유선번호(`0212345678`)는 다른 숫자열과 구분하기 어려워 잡지 않습니다.
- 잡지 않는 것: `+82` 국제 형식, 괄호 지역번호 `(02) 123-4567`, 점 구분 `010.1234.5678`,
  `050X` 안심번호, `080`, `15XX` 대표번호. 국제 형식이 필요하면 업스트림
  `PhoneRecognizer(supported_regions=["KR"])`를 함께 쓰세요.

### KR_BANK_ACCOUNT

하이픈으로 이어진 숫자 그룹을 찾은 뒤, 그룹별 자릿수가 아래 은행별 표기 형식과 맞는 것만
남깁니다(`validate_result`).

| 형식 | 은행 |
|---|---|
| 3-2-6 | 신한(구), SC제일, 대구 |
| 3-3-6 | 신한, 케이뱅크, 신협, 제주 |
| 4-3-6 | 우리, 광주 |
| 6-2-6 | KB국민, 우체국 |
| 3-6-5 | 하나 |
| 4-2-7 | 카카오뱅크 |
| 4-4-4 | 토스뱅크, 수협 |
| 3-4-4-2 | NH농협, 부산 |
| 3-4-4-3 | KDB산업 |
| 3-6-2-3 | IBK기업 |
| 3-2-6-1 | 대구 |

형식 출처: [ddable 은행별 계좌번호 자릿수](https://ddable.com/bank-account-number/),
[나무위키 계좌번호](https://namu.wiki/w/%EA%B3%84%EC%A2%8C%EB%B2%88%ED%98%B8). 은행이 형식을
바꿨거나 출처가 틀렸을 수 있습니다.

3그룹 형식은 모두 마지막 그룹이 4자리 이상이라 날짜(`2024-01-15`, 4-2-2)와 겹치지 않고,
사업자등록번호(3-2-5), 전화번호(3-4-4 등), 카드번호(4-4-4-4)도 목록에 없는 모양이라 걸러집니다.

#### 오탐 가능성

계좌번호는 은행마다 체크섬 규칙이 다르고 공개돼 있지 않아서 **형식만 보고 판단합니다.**

- 형식이 맞아도 점수는 **0.4**로 낮게 둡니다. `validate_result`가 `True`를 돌려주면 Presidio가
  점수를 1.0으로 올리기 때문에 `None`을 돌려줍니다. 주변에 `계좌`, `계좌번호`, `은행`, `입금`,
  `account`, `bank`가 있을 때만 0.75로 오릅니다.
- 같은 모양의 다른 번호는 계좌로 오탐됩니다. 예를 들어 `주문번호 2024-123-456789`(4-3-6)와
  안심번호 `0504-1234-5678`(4-4-4)은 둘 다 `KR_BANK_ACCOUNT` 0.4로 잡힙니다.
- 잡지 못하는 것: 하이픈 없는 계좌번호(`123456789012`, 일반 숫자열과 구분 불가), 공백 구분,
  목록에 없는 형식(씨티·구 외환 3-6-3 등).

`score_threshold=0.5`로 분석하면 컨텍스트 없는 형식 일치(0.4)는 걸러지고 `계좌` 같은 단어가
붙은 것(0.75)만 남습니다. 마스킹처럼 놓치는 쪽이 더 위험한 용도라면 기본값(0)을 권합니다.

## 테스트

```bash
pip install -e ".[test]"
pytest
```

- `ko_core_news_sm`이 없으면 Presidio가 첫 실행 때 자동으로 내려받습니다(네트워크 필요).
- 단위 테스트 외에 실제 `AnalyzerEngine` + `ko_core_news_sm`으로 컨텍스트 강화를 확인하는 통합
  테스트가 있고, 이 README의 사용 예시도 그대로 실행해 위 출력과 같은지 확인합니다
  (`tests/test_readme.py`).
