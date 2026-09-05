# 오늘의 AI 소식 10 — 매일 수집·알림 운영 (2026-09-06)

## 무엇이 매일 돌아가나
- 06:30 KST에 GitHub Actions(`.github/workflows/collect.yml`)가 `scripts/fetch-ai-daily.py`를 돌려 `ai-daily.json`을 갱신한다. 홈페이지 「AI 소식」 구역 맨 위 「오늘의 AI 소식 10」이 이 파일을 GitHub에서 직접 읽으므로 **배포가 필요 없다**.
- 출처 층. 1층 공식 발표 = OpenAI 뉴스 RSS · 구글 AI/제미나이/딥마인드/개발자 블로그 RSS · 앤트로픽 뉴스 페이지(RSS가 없어 새 글 주소를 읽음). 2층 = AI타임스 RSS · 긱뉴스. 고르는 순서는 층 → 플랫폼 관련 낱말(에이전트·프롬프트·교육·도구 기능) → 최신. 출처당 최대 4건, 14일 보관.
- 영문 제목·요약은 DeepL 무료(키 없으면 MyMemory 무료)로 옮기고 원제를 함께 둔다. 요약은 출처의 설명문만 옮기고 지어내지 않는다.
- 같은 날 이어서 `scripts/notify-daily.py`가 **텔레그램·이메일**로 같은 10건을 보낸다. 비밀값이 없는 통로는 건너뛴다.

## 비용
- GitHub Actions: 공개 저장소라 무료. DeepL 무료 한도 월 50만 자(하루 10건 제목·요약이면 월 2만 자 안팎). 텔레그램 봇 API 무료. Gmail SMTP 무료(하루 발송 한도 안). 넷리파이 크레딧은 쓰지 않는다(데이터만 바뀜).
- 홈페이지 화면에 새 구역을 처음 올릴 때만 프로덕션 배포 1회(15크레딧)가 든다. 다른 변경과 모아서 한다(박사님 지시 2026-09-06).

## 알림을 켜는 법 (박사님이 직접 — 비밀값은 AI가 다루지 않는다)
GitHub 저장소 aceyun88/snb-aceyun88 → Settings → Secrets and variables → Actions → New repository secret.

| 이름 | 값 | 어디서 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 | 텔레그램에서 @BotFather에게 `/newbot` → 이름 정하기 → 토큰 복사 |
| `TELEGRAM_CHAT_ID` | 받을 채팅 ID | 만든 봇에게 아무 말을 한 번 보낸 뒤 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates` 를 열어 `"chat":{"id":숫자}` 의 숫자 |
| `GMAIL_USER` | 보내는 Gmail 주소 | 예: aceyun88@gmail.com |
| `GMAIL_APP_PASSWORD` | Gmail **앱 비밀번호** 16자리 | Google 계정 → 보안 → 2단계 인증 켬 → 앱 비밀번호 만들기. 계정 비밀번호를 넣지 않는다 |
| `MAIL_TO` | 받는 주소(쉼표로 여러 명) | 비우면 GMAIL_USER로 보냄. 강사진에게 보낼 때 여기에 추가 |

넷 다 없어도 수집·홈페이지 표시는 그대로 된다. 텔레그램만 켜려면 위 두 개만 넣으면 된다.

## 강의안 조언(④)은 여기 없다
텔레그램·메일·홈페이지에 가는 것은 사실(①무엇이 바뀌었나 ②이전과 다른 점 ③무료·유료·개발자 영향)까지다. **④ 강의자료 수정 필요성**은 판단이라 Claude 세션이 쓰고, 비공개 저장소 snb-k-bridge `docs/03-analysis/tech-radar/`에만 남긴다(CLAUDE.md 3-6 기술 레이더 규칙). 강사진과 나눌 때는 그 파일을 구글 문서로 옮겨 공유 권한으로 관리한다.

## 손으로 돌려 보기
```bash
python scripts/fetch-ai-daily.py
python scripts/notify-daily.py   # 환경변수 TELEGRAM_BOT_TOKEN 등을 넣었을 때만 보냄
```
GitHub 화면 Actions → collect-daily → Run workflow 로도 즉시 실행할 수 있다.
