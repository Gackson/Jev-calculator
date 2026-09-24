# jev-olympics

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · **한국어**

Let Jev do math, chat, and draw things—in a probabilistic way.

[경기장 입장](https://jev-olympics.vercel.app/)

종목은 세 개. 메달은 없습니다. 실수마다 상세한 사고 보고서가 제공됩니다.

TypeSafe의 Jev 모델로 만든 작은 놀이터입니다. 완성된 답을 요구하는 대신, 매번 하나씩 선택하며 계산하고 대화하고 그림을 그리게 합니다. 목적은 재미입니다. 실용적인 가치가 생긴다면 의도하지 않은 부작용입니다.

## 경기 종목

- **Calculator:** Choice로 일의 자리부터 숫자를 고르거나, Noul의 동등·대소 판단으로 정수를 찾습니다. 옆에서 실제 계산도 수행하므로 실망의 크기까지 측정할 수 있습니다.
- **Chat:** 영어 답변을 한 글자 또는 한 단어씩 만듭니다. 단어 모드에는 자주 쓰는 단어 249개, `. , ? !`, `NEWLINE`, `END`까지 총 255개 선택지가 있습니다. 단어 사이 공백은 자동으로 추가됩니다.
- **Canvas:** 4×4~14×14 흑백 격자에 픽셀 순차 스캔, 좌표 선택, 볼펜 이동으로 그림을 그립니다. 결과가 설명과 닮았는지도 실험의 일부입니다.
- **Notes:** 모든 판단에 지시, 배경 정보, 격려를 추가합니다. 가능한 선택지 안에서 내장 지시보다 우선합니다.

## 사고 현장 살펴보기

숫자, 글자, 단어, 그리기 판단을 클릭하면 확률, confidence(제공되는 경우), 모델, 소요 시간과 토큰 수를 확인할 수 있습니다. 기본적으로 접혀 있는 **전체 입력 보기**를 펼치면 인증 정보를 제외한 해당 단계의 실제 JSON을 볼 수 있습니다.

Jev의 선택은 그대로 남깁니다. 정답지를 보고 몰래 답을 고치지 않습니다. Calculator는 처음 틀린 판단을 표시하고, Chat과 Canvas는 미완성 현장을 보존합니다.

UI와 README는 같은 6개 언어를 지원합니다. 언어를 바꿔도 모델 지시나 출력은 번역하지 않습니다. 대화, 그림, Notes는 페이지 메모리에만 저장되며 새로고침하면 사라집니다.

## 경기 규칙

- **Calculator:** 정수, 산술 연산자, 괄호를 지원합니다. 정확한 유리수 계산으로 기준값을 구하고, 비교에는 소수부를 0 방향으로 버린 정수를 사용합니다. Choice는 최대 24자리와 마지막 종료 확인을 수행합니다. Noul은 범위를 넓힌 뒤 무작위 값이나 중간값으로 탐색합니다. Choice의 문맥에 이전 예측을 포함할지 선택할 수 있습니다.
- **Chat:** 각 단계에 현재 메시지, 지금까지의 답변, 최대 세 차례의 이전 대화와 Notes를 전달합니다. 단어 모드는 이전 선택도 전달합니다. 글자 모드는 연속 공백 두 개 또는 같은 글자 다섯 개에서 멈추고, 단어 모드는 같은 선택이 다섯 번 연속되면 멈춥니다. 제한은 64 / 128 / 256글자 또는 문장 부호와 제어 표시를 포함한 32 / 64 / 128회의 단어 모드 판단입니다. 반복이나 제한에 따른 중지는 미완료로 표시하며 `END`로 위장하지 않습니다.
- **Canvas:** 열거 모드는 픽셀을 순서대로 방문하고, 몬테카를로는 좌표나 `END`를 선택합니다. 볼펜은 시작점, 방향, 펜 들기, `END`를 고릅니다. 경계, 반복 검사, 단계 제한으로 실험에 끝이 있도록 합니다.
- **Notes:** 실행 시작 시 고정되어 각 판단에 그대로 전송됩니다. 도중에 수정할 수 없습니다. Notes가 예측을 개선한다고 보장하지는 않습니다.

## 로컬 실행

Python 3.9 이상이 필요하며 TypeSafe 추론에는 추가 Python 의존성이 없습니다. 환경 변수 또는 프로젝트 루트의 `.env`에 `TYPESAFE_API_KEY`를 설정합니다.

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

<http://127.0.0.1:8765>를 엽니다. `--port 8766`으로 포트를, `--model jev-latest`로 모델을 바꿀 수 있습니다. 기본 모델은 `jev-1.13.0`입니다. 서버는 localhost에서만 수신합니다. 설정을 바꾸면 재시작하고, 실제 인증 정보는 Git에 넣지 마세요.

선택 사항으로 로컬 **Laya** 추론도 지원합니다. 설치, 배포, 설정에 관한 자세한 내용은 [영문 개발 가이드](development.md)를 참고하세요.

## 개발

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

테스트는 모델 응답을 모의하며, HTTP 통합 테스트는 루프백 포트를 사용합니다. CI는 Python 3.9, 3.12와 프런트엔드 JavaScript 문법을 검사합니다. 실험이 작동하는지는 검증하지만, Jev에게 상식이 생겼는지는 검증하지 않습니다.

| 디렉터리 | 내용 |
| --- | --- |
| `calculator_ui/` | UI와 번역 |
| `api/` | Vercel 함수 진입점 |
| `tests/` | 단위 테스트와 HTTP 통합 테스트 |
| `docs/` | 번역된 README와 개발 가이드 |

참고: [TypeSafe 빠른 시작](https://docs.typesafe.ai/introduction/quickstart), [Choice](https://docs.typesafe.ai/primitives/choice), [HTTP API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence).
