# presidio-ko

[Microsoft Presidio](https://github.com/microsoft/presidio)에 **한국 전화번호(`KR_PHONE`)** 와
**은행 계좌번호(`KR_BANK_ACCOUNT`)** recognizer, 그리고 한국어 문장에서 컨텍스트 단어가 제대로
매칭되게 하는 **`KoreanContextAwareEnhancer`** 를 더하는 패키지입니다.

주민등록번호·외국인등록번호 같은 한국형 recognizer는 Presidio 업스트림에 체크섬 검증까지 이미
들어 있으므로 다시 만들지 않고 그대로 가져다 씁니다. 이 패키지는 업스트림에 **없거나 한국어에서
동작하지 않는 부분만** 채웁니다.

## 업스트림에 이미 있는 것 vs 이 패키지가 채우는 것

presidio-analyzer 2.2.364 기준입니다.

| 구분 | 제공 | 검증 | 비고 |
|---|---|---|---|
| `KR_RRN` 주민등록번호 | Presidio `KrRrnRecognizer` | 체크섬(mod 11), 지역코드 | 컨텍스트가 영어뿐 → [#2212](https://github.com/microsoft/presidio/issues/2212) |
| `KR_FRN` 외국인등록번호 | Presidio `KrFrnRecognizer` | 체크섬 | |
| `KR_BRN` 사업자등록번호 | Presidio `KrBrnRecognizer` | 체크섬 | |
| `KR_PASSPORT` 여권번호 | Presidio `KrPassportRecognizer` | 형식 | 기본 `supported_language`가 `"kr"`이라 `language="ko"` 분석에서 빠짐. `KrPassportRecognizer(supported_language="ko")`로 등록 |
| `KR_DRIVER_LICENSE` 운전면허번호 | Presidio `KrDriverLicenseRecognizer` | 지역코드 | |
| `PHONE_NUMBER` 전화번호(범용) | Presidio `PhoneRecognizer` | libphonenumber | `supported_regions=["KR"]`를 주면 한국 번호도 잡음(`+82` 국제 형식 포함). 기본 컨텍스트는 영어 |
| **`KR_PHONE`** 휴대폰·유선전화 | **이 패키지** `KrPhoneRecognizer` | 형식 | 한국 번호 전용 엔티티, 한국어 컨텍스트 |
| **`KR_BANK_ACCOUNT`** 계좌번호 | **이 패키지** `KrBankAccountRecognizer` | 형식(체크섬 불가) | 업스트림에 해당 recognizer 없음 |
| 컨텍스트 강화 | Presidio `LemmaContextAwareEnhancer` | | 컨텍스트 단어를 lemma와 비교해서 한국어에서는 대부분 실패 |
| **한국어 컨텍스트 강화** | **이 패키지** `KoreanContextAwareEnhancer` | | 토큰 원문과 비교. 업스트림 한국형 recognizer에도 적용 |

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

- 이 패키지의 두 recognizer만 등록하려면 `presidio_ko.KOREAN_RECOGNIZERS`를 쓰면 됩니다.
- `context_aware_enhancer`를 빼면 `연락처는`이 매칭되지 않아 `KR_PHONE`이 0.5에 머뭅니다
  ([한국어 컨텍스트 강화](#한국어-컨텍스트-강화) 참고). 경고 없이 조용히 약해지므로 꼭
  넣으세요. 이미 만든 엔진이라면 `analyzer.context_aware_enhancer = KoreanContextAwareEnhancer()`
  한 줄로 바꿀 수 있습니다.
- `AnalyzerEngine()`을 인자 없이 쓰면 영어 spaCy 모델만 `en`으로 올라가서, `language="ko"`로
  분석할 때 NLP 엔진이 `ko` 모델을 찾지 못해 `KeyError: 'ko'`로 실패합니다. 업스트림 한국형
  recognizer도 (여권을 빼면) 기본 언어가 `ko`이므로 위처럼 한국어 NLP 엔진을 넘겨야 합니다.

## 한국어 컨텍스트 강화

Presidio 기본 컨텍스트 강화기(`LemmaContextAwareEnhancer`)는 컨텍스트 단어를 원문이 아니라
lemma와 비교합니다. 그런데 한국어 spaCy 모델(`ko_core_news_*`)의 lemma는 형태소를 `+`로 잇고
분절 위치도 불규칙합니다.

| 원문 | lemma |
|---|---|
| `연락처가` | `연+락처+가` |
| `전화번호로` | `전+화번+호로` |
| `은행계좌` | `+은+행+계+좌` |
| `주민등록번호는` | `주민등+록번+호는` |

그래서 `연락처`, `전화`, `계좌`, `주민등록번호` 같은 컨텍스트 단어가 대부분 매칭되지 않습니다.
`KoreanContextAwareEnhancer`는 lemma 자리에 토큰 원문을 넣고, 나머지(앞 5단어 윈도, 부분 문자열
매칭, 점수 +0.35·최소 0.4)는 기본 강화기를 그대로 씁니다. 생성자 인자도
`LemmaContextAwareEnhancer`와 같아서 계수와 윈도를 똑같이 조정할 수 있습니다. 엔진 단위
설정이므로 업스트림 한국형 recognizer에도 적용되고, spaCy 문서 언어가 `ko`일 때만 바꾸므로
다국어 엔진의 다른 언어 문서는 기본 강화기와 똑같이 동작합니다. `ko_core_news_sm` 3.8.0으로 잰
결과입니다.

| 문장 | 엔티티 | 기본 강화기 | `KoreanContextAwareEnhancer` |
|---|---|---|---|
| `연락처가 010-1234-5678입니다` | `KR_PHONE` | 0.5 | 0.85 |
| `전화번호로 010-1234-5678` | `KR_PHONE` | 0.5 | 0.85 |
| `은행계좌 110-123-456789` | `KR_BANK_ACCOUNT` | 0.4 | 0.75 |
| `급여계좌는 110-123-456789` | `KR_BANK_ACCOUNT` | 0.4 | 0.75 |
| `외국인등록번호는 900101-5234567` | `KR_FRN` (업스트림) | 0.5 | 0.85 |

윈도는 기본 강화기와 같이 문장이나 줄 경계를 가리지 않고 앞 5단어를 봅니다. 그래서 라벨과 값을
줄을 나눠 쓴 양식(`계좌번호` 다음 줄에 `110-123-456789`)도 강화되지만, 앞 문장에 나온 단어로도
점수가 오릅니다(`계좌 개설 안내입니다.` 다음 줄의 `주문번호 2024-123-456789`가 0.75).

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

**단어 추가만으로는 부족합니다.** 제안된 네 단어를 `CONTEXT`에 넣어도 기본 강화기는 lemma와
비교하기 때문에 다섯 문장 중 두 문장에서만 점수가 오릅니다. `KoreanContextAwareEnhancer`를 함께
쓰면 다섯 문장 모두 오릅니다.

| 문장 | 첫 어절의 lemma | 기본 강화기 | `KoreanContextAwareEnhancer` |
|---|---|---|---|
| `주민등록번호: 900101-1234567` | `주민등록번호` | 0.85 | 0.85 |
| `주민등록번호는 900101-1234567` | `주민등+록번+호는` | 0.5 | 0.85 |
| `주민번호 900101-1234567` | `주민번+호` | 0.5 | 0.85 |
| `신분증 번호 900101-1234567` | `신분+증` | 0.5 | 0.85 |
| `본인인증 900101-1234567` | `본인인증` | 0.85 | 0.85 |

#2212가 반영되기 전에는 단어를 직접 넘겨서 등록하면 됩니다. 위 표처럼 기본 강화기로는 대부분
발동하지 않으므로 `KoreanContextAwareEnhancer`를 쓰는 엔진에 등록해야 합니다.

```python
KrRrnRecognizer(context=KrRrnRecognizer.CONTEXT + ["주민등록번호", "주민번호", "신분증", "본인인증"])
```

## 인식 범위와 한계

### KR_PHONE

| 종류 | 형식 | 점수 (컨텍스트 있으면) |
|---|---|---|
| 휴대폰 | `010/011/016/017/018/019` + 3~4자리 + 4자리. 구분자 생략 가능 | 0.5 (0.85) |
| 유선 | `02`, `031~033`, `041~044`, `051~055`, `061~064`, `070` + 3~4자리 + 4자리. 구분자 필수 | 0.4 (0.75) |

- 컨텍스트 단어: `전화`, `연락처`, `휴대폰`, `핸드폰`, `phone`, `mobile`
- 앞자리 `0` 대신 국제 형식 `+82`도 잡습니다(`+82 10-1234-5678`, `+821012345678`,
  `0`을 남겨 쓴 `+82 010-1234-5678`).
- 구분자는 공백, 점, 그리고 하이픈과 en dash 같은 유니코드 대시(`\p{Pd}`)입니다. PDF·OCR
  추출문에 섞여 나오는 대시도 잡습니다.
- 경계는 `\b` 대신 lookaround를 씁니다. 한글도 정규식에서 단어 문자(`\w`)라
  `010-1234-5678로`처럼 조사가 붙으면 `8`과 `로` 사이에 `\b`가 성립하지 않기 때문입니다.
  대신 앞에 숫자가 붙거나 뒤에 대시·숫자가 이어지는 경우(`031-123-4567-89` 같은 더 긴
  번호)는 잡지 않습니다. 앞에 영문자가 바로 붙은 경우는 구분자 없는 번호만 제외합니다
  (`ORD01012345678`은 ID로 보고, `HP010-1234-5678`은 잡습니다).
- 구분자 없는 유선번호(`0212345678`)는 다른 숫자열과 구분하기 어려워 잡지 않습니다.
- 잡지 않는 것: 괄호 지역번호 `(02) 123-4567`, `050X` 안심번호, `080`, `15XX` 대표번호.

### KR_BANK_ACCOUNT

대시로 이어진 3~4개 숫자 그룹을 찾아 두 단계로 점수를 줍니다.

| 단계 | 조건 | 점수 (컨텍스트 있으면) |
|---|---|---|
| 형식표 일치 | 그룹별 자릿수가 아래 은행별 표기 형식과 같음 | 0.4 (0.75) |
| 그 밖 | 형식표에 없지만 계좌일 수 있는 모양 (예: `123-45-6789-012`, 씨티·구 외환 3-6-3) | 0.1 (0.45) |

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
바꿨거나 출처가 틀렸을 수 있어서, 형식표에 없는 모양도 버리지 않고 "그 밖" 단계로 남깁니다.

계좌번호일 수 없는 모양은 `validate_result`가 제외합니다.

- 10~14자리가 아닌 것: 날짜 `2024-01-15`, 카드번호 `1234-5678-9012-3456`
- 날짜로 시작하는 것(19xx·20xx년, 1~12월, 1~31일): `2024-01-15-1030`, `2024-1-5-1030`
- 사업자등록번호 모양(3-2-5): `123-45-67890`
- 0으로 시작하는 전화번호 모양: `010-1234-5678`, `031-123-4567`, 안심번호 `0504-1234-5678`

`신한-110-123-456789`처럼 은행명 뒤에 하이픈으로 붙여 쓴 경우는 잡고, 앞에 숫자·영문자가 바로
붙은 코드(`SKU110-123-456789`)나 더 긴 번호의 일부는 잡지 않습니다. 구분자는 전화번호와 같이
유니코드 대시를 허용합니다.

#### 오탐 가능성

계좌번호는 은행마다 체크섬 규칙이 다르고 공개돼 있지 않아서 **형식만 보고 판단합니다.**

- 형식표와 맞아도 점수는 **0.4**로 낮게 둡니다. `validate_result`가 `True`를 돌려주면 Presidio가
  점수를 1.0으로 올리기 때문에 `None`을 돌려줍니다. 주변에 `계좌`, `계좌번호`, `은행`, `입금`,
  `account`, `bank`가 있을 때만 점수가 오릅니다.
- 같은 모양의 다른 번호는 계좌로 오탐됩니다. 예를 들어 `주문번호 2024-123-456789`(4-3-6)는
  `KR_BANK_ACCOUNT` 0.4로 잡힙니다. "그 밖" 단계(0.1)는 대시로 이은 10~14자리 숫자열이면 대부분
  걸리므로 문서번호·상품번호 오탐이 더 많습니다.
- 잡지 못하는 것: 하이픈 없는 계좌번호(`123456789012`, 일반 숫자열과 구분 불가), 공백 구분,
  10자리 미만의 짧은 계좌.

`score_threshold=0.5`로 분석하면 컨텍스트 없는 형식표 일치(0.4)와 "그 밖" 단계(최대 0.45)는
걸러지고, 형식표 일치에 컨텍스트가 붙은 것(0.75)만 남습니다. 다만 컨텍스트 윈도가 문장 경계를
넘기 때문에 앞 문장에 `계좌`나 `은행`이 있으면 오탐도 0.75가 될 수 있습니다. 마스킹처럼 놓치는
쪽이 더 위험한 용도라면 기본값(0)을 권합니다.

## 테스트

```bash
pip install -e ".[test]"
pytest
```

- `ko_core_news_sm`이 없으면 Presidio가 첫 실행 때 자동으로 내려받습니다(네트워크 필요).
- 단위 테스트 외에 실제 `AnalyzerEngine` + `ko_core_news_sm`으로 컨텍스트 강화를 확인하는 통합
  테스트가 있습니다(`tests/test_korean_context_enhancer.py`는 업스트림 recognizer와 #2212 제안
  단어까지 확인). 이 README의 사용 예시도 그대로 실행해 위 출력과 같은지 확인합니다
  (`tests/test_readme.py`).

## 라이선스

MIT
