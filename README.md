# presidio-ko

[![test](https://github.com/Bin0917/presidio-ko/actions/workflows/test.yml/badge.svg)](https://github.com/Bin0917/presidio-ko/actions/workflows/test.yml)

[Microsoft Presidio](https://github.com/microsoft/presidio)로 한국어 문서의 개인정보를 찾고,
한국식으로 가리고, LLM에 보낼 때는 되돌릴 수 있게 바꾸는 패키지입니다. 함수 한 번으로 한국어
분석기를 만들고(`create_korean_analyzer`), 개인정보위 권고 방식의 부분 마스킹(`korean_mask`)과
되돌릴 수 있는 가명 치환(`Pseudonymizer`)을 씁니다.

*English:* Korean PII detection, Korean-style partial masking, and reversible pseudonymization
for LLM prompts on top of Microsoft Presidio.

## 설치

```bash
pip install presidio-ko
python -m spacy download ko_core_news_sm
```

`ko_core_news_sm`은 한국어 문장을 분석하는 spaCy 모델입니다. 개발용으로는 저장소를 받아
`pip install -e ".[test]"`로 설치합니다.

## 빠른 시작

```python
from presidio_ko import Pseudonymizer, create_korean_analyzer, korean_mask

analyzer = create_korean_analyzer()
text = "예금주 김민수, 연락처 010-1234-5678, 서울 영등포구 영등포로3길 12, 101동 1001호"
results = analyzer.analyze(text=text, language="ko")

# 한국식 부분 마스킹
print(korean_mask(text, results))

# 되돌릴 수 있는 가명 치환: LLM에는 자리표시자만 보내고 응답에서 원문을 복원한다
pseudonymizer = Pseudonymizer()
prompt = pseudonymizer.pseudonymize(text, results)
print(prompt)
print(pseudonymizer.restore("[이름1]님께 [전화번호1]로 연락드리겠습니다."))
```

출력:

```
예금주 김*수, 연락처 010-1234-****, 서울 영등포구 영등포로3길 **, ***동 ****호
예금주 [이름1], 연락처 [전화번호1], [주소1]
김민수님께 010-1234-5678로 연락드리겠습니다.
```

- `create_korean_analyzer(model_name="ko_core_news_sm", nlp_engine=None)`은 한국어 spaCy 엔진,
  아래 표의 인식기, `KoreanContextAwareEnhancer`를 모두 켠 `AnalyzerEngine`을 돌려줍니다.
  업스트림 `PhoneRecognizer`와 `SpacyRecognizer`는 같은 번호·사람을 `PHONE_NUMBER`와
  `PERSON`으로 한 번 더 보고하므로 뺍니다.
- `Pseudonymizer`는 한 대화에 하나를 씁니다. 같은 원문은 같은 자리표시자를 받고 번호는 호출을
  넘어 이어집니다. `restore`는 자신이 발급한 자리표시자만 바꾸고 LLM이 만든 다른 `[..]`는 그대로
  둡니다. 자리표시자의 한국어 이름은 `presidio_ko.ENTITY_LABELS`에 있습니다.

## 탐지하는 개인정보

| 엔티티 | 설명 | 출처 | 비고 |
|---|---|---|---|
| `PERSON` | 이름 | **이 패키지** `KrPersonRecognizer` | 성명·예금주 같은 라벨 뒤 0.85, spaCy 인물 0.6. 성씨 표와 양식 라벨 차단어로 거름 |
| `KR_ADDRESS` | 주소 | **이 패키지** `KrAddressRecognizer` | 시도(또는 `주소`·`배송지` 같은 라벨) + 시군구·읍면 + 도로명·건물번호나 지번, 뒤따르는 동·호. 건물명은 동·호가 이어질 때만 포함 |
| `KR_PHONE` | 휴대폰·유선전화 | **이 패키지** `KrPhoneRecognizer` | `+82` 국제 형식 포함 |
| `KR_BANK_ACCOUNT` | 계좌번호 | **이 패키지** `KrBankAccountRecognizer` | 은행명·라벨 컨텍스트, 구분자 없는 번호는 라벨 뒤만 |
| `KR_VEHICLE_PLATE` | 차량번호 | **이 패키지** `KrVehiclePlateRecognizer` | `12가 3456`, `서울12가3456` |
| `KR_HEALTH_INSURANCE` | 건강보험증번호 | **이 패키지** `KrHealthInsuranceRecognizer` | 공개 표준이 없어 `건강보험증번호` 같은 라벨 뒤 숫자만 |
| `KR_RRN` `KR_FRN` `KR_BRN` | 주민·외국인·사업자등록번호 | Presidio 업스트림 | 체크섬 검증 |
| `KR_PASSPORT` `KR_DRIVER_LICENSE` | 여권·운전면허번호 | Presidio 업스트림 | 구분자가 없거나 섞인 12자리 면허번호는 `운전면허` 같은 라벨 뒤만 |
| `CREDIT_CARD` `EMAIL_ADDRESS` 등 | 카드·이메일 등 | Presidio 업스트림 | `ko`로 등록 |

## 한국식 마스킹

`korean_mask(text, results)`는 분석 결과를 아래 규칙으로 가린 문자열을 돌려줍니다.
개인정보보호위원회 권고와 ISMS-P 관행대로 구분자(대시·공백·점)는 두고 글자·숫자만 `*`로 바꿉니다.
결과가 겹치면 같은 종류는 하나로 합치고, 한 결과가 다른 종류를 품으면 바깥 결과를 남기되 안쪽
결과의 규칙이 가리는 글자도 가립니다. 일부만 겹치면 점수가 높은 쪽을 남기고 진 쪽의 나머지
조각도 진 쪽 규칙으로 가립니다. 탐지된 글자는 규칙이 표시하는 부분 말고는 드러나지 않습니다.
겹치는 결과에 `replace`처럼 길이가 바뀌는 operator를 쓰면 자리표시자가 잘리거나
(`<PERSON>AIL_ADDRESS>`) 다른 결과의 `*`와 섞일 수 있습니다. 이때도 가린 글자는 드러나지 않습니다.

`AnonymizerEngine.anonymize`에 규칙을 직접 넘기지 말고 `korean_mask`를 쓰세요. 엔진은 기본값으로
공백을 사이에 둔 같은 종류를 하나로 합쳐서 `010-1234-5678 010-2345-6789`의 뒤 4자리만 가리고 앞
번호를 그대로 두며, 겹치는 결과도 정리하지 않습니다.

| 엔티티 | 규칙 | 예 |
|---|---|---|
| `PERSON` | 첫째·셋째 글자만 표시 | 홍길동 → 홍\*동, 남궁민수 → 남\*민\* |
| `KR_PHONE` | 마지막 4자리 | 010-1234-5678 → 010-1234-\*\*\*\* |
| `KR_RRN` `KR_FRN` | 생년월일과 성별 1자리만 | 900101-1234567 → 900101-1\*\*\*\*\*\* |
| `KR_BANK_ACCOUNT` | 첫 묶음과 마지막 2자리만 | 110-123-456789 → 110-\*\*\*-\*\*\*\*89 |
| `KR_ADDRESS` | 도로명·지번 뒤 모든 숫자와 `A동` 같은 동 이름 | 영등포로3길 12, 101동 → 영등포로3길 \*\*, \*\*\*동 |
| `EMAIL_ADDRESS` | 앞 2자만 | nguyen@example.com → ng\*\*\*\*@example.com |
| `CREDIT_CARD` | 앞 6자리와 뒤 4자리 | 4111-1111-1111-1111 → 4111-11\*\*-\*\*\*\*-1111 |
| `KR_VEHICLE_PLATE` | 마지막 4자리 중 앞 2자리 | 12가 3456 → 12가 \*\*56 |
| `KR_BRN` `KR_PASSPORT` `KR_DRIVER_LICENSE` `KR_HEALTH_INSURANCE` | 구분자만 남기고 모두 | 11-17-123456-21 → \*\*-\*\*-\*\*\*\*\*\*-\*\* |
| 그 밖 | `<ENTITY>`로 치환 | `<URL>` |

주소는 상세 시작점을 인식기가 알려주지 않으므로 마스킹이 도로명·지번 뒤 첫 번호를 다시 찾아
숫자만 가립니다(`동`·`호` 같은 단위 글자는 남습니다). 규칙을 바꾸려면 딕셔너리를 덮어씁니다.

```python
from presidio_anonymizer.entities import OperatorConfig

from presidio_ko.masking import korean_operators

operators = korean_operators() | {"KR_PHONE": OperatorConfig("replace")}
masked = korean_mask(text, results, operators)
```

## 한계

- **이름**: 영문 로마자 이름(`Nguyen Van An`)은 잡지 않습니다. 한국어 이름도 성씨 표에
  없는 성이나 라벨·spaCy 단서가 없는 문맥(명함의 `과장 정재현`, 호칭만 붙은 `이영희씨`,
  `대표 노승현`·`작성자 이도현`처럼 뒤에 `정보`·`전화` 같은 일반어도 흔한 라벨, 머리글 행에만
  `이름`이 있는 표나 라벨 다음 줄에 쓴 이름)에서는
  놓칠 수 있습니다. `ko_core_news_sm`의 인물 인식이 약해서입니다. 네 글자는 복성(`남궁민수`)만
  이름으로 보고, `김치찌개`처럼 성씨로 시작하는 두 글자 일반어는 일부(`김밥`, `김치`, `조회`)만
  거릅니다.
- **주소**: 시도나 `주소`·`배송지` 같은 라벨이 앞에 없으면 잡지 않습니다(`처음으로 1번` 같은 오탐을 막기 위해서입니다). 동·호가 이어지지 않는 건물명은 범위에 넣지 않습니다.
- **계좌번호**: 체크섬이 없어 형식만 봅니다. `6123-4567-8901` 같은 송장번호는 낮은 점수(0.1~0.4)로
  잡힐 수 있습니다. `score_threshold=0.5`로 거르는 방법은 [KR_BANK_ACCOUNT](#kr_bank_account)에
  있습니다.
- **차량번호**: `호` 용도문자(렌터카)는 호수(`101호 1234`)와 구별할 수 없어 뺍니다. 바로 뒤에 `원`이 붙으면 가격(`10가 5000원`)으로 보고 뺍니다.
- **건강보험증번호**: 라벨이 없으면 잡지 않습니다.
- **카드번호**: 업스트림 패턴의 `\b` 경계를 더 긴 번호의 일부를 막는 경계로 바꿨습니다. 그래서
  뒤에 대시로 숫자 묶음이 더 붙은 `4111-1111-1111-1111-2222`는 잡지 않습니다. 전화번호가 있으면
  전화번호를 모두 지운 사본에서 카드를 한 번 더 찾습니다. 그래서 전화번호에 걸친 카드
  후보(`010 1234 5678 010 2345 6789`의 가운데 16자리)는 버리고 `02 1234 5678 4854 2143 0443 2442`의
  카드는 잡습니다. 다시 찾은
  카드나 전화번호가 덮지 못한 숫자가 남는 후보(`010 4111 1111 1111 1111`)는 카드로 남깁니다.
- **이메일**: 업스트림 인식기는 앞에 글자와 `/`가 붙은 이메일(`주문/kim99@corp.co.kr`)을 놓치고
  도메인만 `URL`로 냅니다. `/`가 맨 앞이거나 공백 뒤면 잡습니다.
- **업스트림이 같이 내는 엔티티**: `URL`(이메일 도메인), `DATE_TIME` 등은 그대로 나옵니다.
  필요 없으면 `analyze(entities=[...])`로 고르세요.

## 업스트림에 이미 있는 것 vs 이 패키지가 채우는 것

presidio-analyzer 2.2.366 기준입니다. 2.2.364 이상에서 동작합니다.

| 구분 | 제공 | 검증 | 비고 |
|---|---|---|---|
| `KR_RRN` 주민등록번호 | Presidio `KrRrnRecognizer` | 체크섬(mod 11), 지역코드 | 컨텍스트가 영어뿐 → [#2212](https://github.com/microsoft/presidio/issues/2212) |
| `KR_FRN` 외국인등록번호 | Presidio `KrFrnRecognizer` | 체크섬 | |
| `KR_BRN` 사업자등록번호 | Presidio `KrBrnRecognizer` | 체크섬 | |
| `KR_PASSPORT` 여권번호 | Presidio `KrPassportRecognizer` | 형식 | 2.2.364는 기본 `supported_language`가 `"kr"`이라 `language="ko"` 분석에서 빠짐. 2.2.365에서 수정([#2170](https://github.com/microsoft/presidio/pull/2170)). `create_korean_analyzer`는 `"ko"`로 등록 |
| `KR_DRIVER_LICENSE` 운전면허번호 | Presidio `KrDriverLicenseRecognizer` | 지역코드 | |
| `PHONE_NUMBER` 전화번호(범용) | Presidio `PhoneRecognizer` | libphonenumber | `KR_PHONE`과 같은 번호를 이중 보고해서 `create_korean_analyzer`는 뺍니다 |
| **`KR_PHONE`** 휴대폰·유선전화 | **이 패키지** `KrPhoneRecognizer` | 형식 | 한국 번호 전용 엔티티, 한국어 컨텍스트 |
| **`KR_BANK_ACCOUNT`** 계좌번호 | **이 패키지** `KrBankAccountRecognizer` | 형식(체크섬 불가) | 업스트림 릴리스에는 없음. [#2215](https://github.com/microsoft/presidio/pull/2215) PR 진행 중 |
| 컨텍스트 강화 | Presidio `LemmaContextAwareEnhancer` | | 컨텍스트 단어를 lemma와 비교해서 한국어에서는 대부분 실패 |
| **한국어 컨텍스트 강화** | **이 패키지** `KoreanContextAwareEnhancer` | | 토큰 원문과 비교. 업스트림 한국형 recognizer에도 적용 |

## 직접 조립하기

`create_korean_analyzer`를 쓰지 않고 엔진을 직접 만들 수도 있습니다. 기본 `AnalyzerEngine()`은
영어 모델만 올리므로 `language="ko"`로 분석하면 `KeyError: 'ko'`로 실패합니다. 한국어 NLP 엔진을
넘기고, `presidio_ko.KOREAN_RECOGNIZERS`를 등록하세요.

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_ko import KOREAN_RECOGNIZERS, KoreanContextAwareEnhancer

nlp_engine = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "ko", "model_name": "ko_core_news_sm"}],
}).create_engine()
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["ko"],
    context_aware_enhancer=KoreanContextAwareEnhancer(),
)
for recognizer in KOREAN_RECOGNIZERS:
    analyzer.registry.add_recognizer(recognizer)
```

`context_aware_enhancer`를 빼면 `연락처는` 같은 컨텍스트 단어가 매칭되지 않아 점수가 올라가지
않습니다. 경고 없이 조용히 약해지므로 꼭 넣으세요.

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
[#2258](https://github.com/microsoft/presidio/pull/2258)이 열려 있습니다(2026-11-26 기준 미병합).
lemma 분절이라는 근본 원인은 별도 이슈
[#2216](https://github.com/microsoft/presidio/issues/2216)에서 논의 중입니다.

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
| 유선·안심번호 | `02`, `031~033`, `041~044`, `051~055`, `061~064`, `070`, `0502~0508` + 3~4자리 + 4자리. 구분자 필수 | 0.4 (0.75) |

- 컨텍스트 단어: `전화`, `연락처`, `휴대폰`, `핸드폰`, `팩스`, `안심번호`, `phone`, `mobile`,
  `tel`, `hp`, `fax`(대소문자 무관, 명함의 `Tel.`, `HP`도 해당)
- 컨텍스트 단어는 부분 문자열로 비교합니다(Presidio 기본 강화기와 같음). 그래서 `Intel`,
  `hotel` 옆의 번호도 점수가 오릅니다. 번호 모양이 맞을 때만 점수를 올리므로 새 오탐은 생기지 않습니다.
- 괄호 지역번호도 잡습니다: `(02) 123-4567`, `(010) 1234-5678`, `Tel. 02)123-4567`, `(02)-123-4567`.
- 앞자리 `0` 대신 국제 형식 `+82`도 잡습니다(`+82 10-1234-5678`, `+821012345678`,
  `0`을 남겨 쓴 `+82 010-1234-5678`, `+82 (0)10-1234-5678`, `(+82) 10-1234-5678`).
- 구분자는 가로 공백, 점, 가운뎃점(`·`, `ㆍ`, `・`), 그리고 하이픈과 en dash 같은 유니코드 대시(`\p{Pd}`)와 빼기
  기호(U+2212)입니다. PDF·OCR 추출문에 섞여 나오는 대시도 잡고, 대시 앞뒤의 공백도
  허용합니다(`010 - 1234 - 5678`). 줄바꿈은 구분자로 보지 않습니다. 표의 열처럼 줄마다
  따로 적힌 숫자를 하나의 번호로 잇지 않기 위해서입니다.
- 경계는 `\b` 대신 lookaround를 씁니다. 한글도 정규식에서 단어 문자(`\w`)라
  `010-1234-5678로`처럼 조사가 붙으면 `8`과 `로` 사이에 `\b`가 성립하지 않기 때문입니다.
  대신 앞에 숫자나 "숫자+대시"가 붙거나 뒤에 대시·숫자가 이어지는 경우(`89-031-123-4567`,
  `031-123-4567-89` 같은 더 긴 번호)는 잡지 않습니다. 앞에 영문자가 바로 붙은 경우는 구분자
  없는 번호만 제외합니다
  (`ORD01012345678`은 ID로 보고, `HP010-1234-5678`은 잡습니다).
- 구분자 없는 유선번호(`0212345678`)는 다른 숫자열과 구분하기 어려워 잡지 않습니다.
- 전각 숫자(`０１０-１２３４-５６７８`)와 전각 `＋`도 같은 번호로 잡습니다.
  `create_korean_analyzer()`는 분석 전에 전각 블록(U+FF01~U+FF5E) 전체를 반각으로 1:1
  바꾸므로 주민번호, 카드, 여권(`Ｍ１２３Ａ４５６７`), 면허, 이메일도 전각으로 적힌 그대로
  원문 위치에서 잡힙니다.
- 잡지 않는 것: `080` 수신자부담, `15XX`·`16XX`·`18XX` 대표번호. 개인 연락처가 아닌 기업
  번호라서 잡으면 오탐만 늘어납니다.

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

계좌번호일 수 없는 모양은 `validate_result`가 제외합니다(구분자 없는 번호는 `0`으로 시작하면 휴대폰으로 봅니다).

- 10~14자리가 아닌 것: 날짜 `2024-01-15`, 카드번호 `1234-5678-9012-3456`
- 날짜로 시작하는 것(19xx·20xx년, 1~12월, 1~31일): `2024-01-15-1030`, `2024-1-5-1030`
- 사업자등록번호 모양(3-2-5): `123-45-67890`
- 0으로 시작하는 전화번호 모양: `010-1234-5678`, `031-123-4567`, 안심번호 `0504-1234-5678`
- 휴대폰 앞자리로 시작하는 10~11자리 3그룹(자릿수를 잘못 끊은 휴대폰): `010-123-45678`

`신한-110-123-456789`처럼 은행명 뒤에 하이픈으로 붙여 쓴 경우는 잡고, 앞에 숫자·영문자가 바로
붙은 코드(`SKU110-123-456789`), `+82` 국제 전화번호의 일부(`+8210-1234-5678`), 더 긴
번호의 일부는 잡지 않습니다. 구분자는 전화번호와 같이 유니코드 대시와 빼기 기호(U+2212)를
허용합니다.

#### 오탐 가능성

계좌번호는 은행마다 체크섬 규칙이 다르고 공개돼 있지 않아서 **형식만 보고 판단합니다.**

- 형식표와 맞아도 점수는 **0.4**로 낮게 둡니다. `validate_result`가 `True`를 돌려주면 Presidio가
  점수를 1.0으로 올리기 때문에 `None`을 돌려줍니다. 주변에 `계좌`, `계좌번호`, `은행`, `입금`,
  `account`, `bank`가 있을 때만 점수가 오릅니다.
- 같은 모양의 다른 번호는 계좌로 오탐됩니다. 예를 들어 `주문번호 2024-123-456789`(4-3-6)는
  `KR_BANK_ACCOUNT` 0.4로 잡힙니다. "그 밖" 단계(0.1)는 대시로 이은 10~14자리 숫자열이면 대부분
  걸리므로 문서번호·상품번호 오탐이 더 많습니다.
- 하이픈 없는 계좌번호(`123456789012`)와 공백으로 나눈 번호(`110 123 456789`)는 `계좌`,
  `계좌번호`, `은행`, `뱅크`, `예금주 이름` 바로 뒤에서만 잡습니다(0.4). 일반 숫자열과 구분할 수
  없어서입니다. 10자리 미만의 짧은 계좌는 잡지 못합니다.
- 컨텍스트에는 은행명(`카카오뱅크`, `농협`, `우체국` 등)과 `예금주`, `송금`, `이체`, `환불`도
  넣었습니다. `우리`, `하나`처럼 일상어와 겹치는 약칭(`국민`, `신한`, `기업`, `산업`, `토스`
  포함)은 컨텍스트 단어로 두면 `우리는 주문번호 2024-123-456789`까지 0.75로 올라서, 은행별
  형식에 맞는 번호 바로 앞에 올 때만 받습니다(`국민 123456-78-901234`는 0.6).

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
- 단위 테스트 외에 실제 `AnalyzerEngine` + `ko_core_news_sm`으로 컨텍스트 강화와 `create_korean_analyzer`를
  확인하는 통합 테스트가 있습니다. 이 README의 빠른 시작도 그대로 실행해 위 출력과 같은지 확인합니다
  (`tests/test_readme.py`).

## 라이선스

MIT
