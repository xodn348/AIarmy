# Claude Session Key 사용 가이드

AIarmy를 Claude Pro/Team 구독($20-100/월)으로 사용하는 방법입니다.

## 왜 Session Key를 사용하나요?

| 항목 | API Key (공식) | Session Key (구독) |
|------|---------------|-------------------|
| 비용 | Pay-as-you-go (사용량 기반) | 고정 월정액 |
| 요금 | Sonnet: $3/1M input tokens | 이미 결제 중 |
| 제한 | 토큰 기반 | 메시지 수 기반 (Pro: 제한 있음, Max: 무제한) |
| 추천 대상 | 가끔 사용 | 이미 구독 중인 사용자 |

**결론**: 이미 Claude Pro/Team 구독 중이면 session key 사용이 합리적입니다.

---

## 1. Session Key 얻기

### 방법 1: Chrome/Firefox (권장)

1. **claude.ai 로그인**
   - https://claude.ai/chats 접속
   - Claude Pro/Team 계정으로 로그인

2. **개발자 도구 열기**
   - Windows/Linux: `F12` 또는 `Ctrl+Shift+I`
   - Mac: `Cmd+Option+I`

3. **쿠키 찾기**
   - **Chrome**: Application → Storage → Cookies → https://claude.ai
   - **Firefox**: Storage → Cookies → https://claude.ai

4. **sessionKey 복사**
   - `sessionKey` 항목 찾기
   - **Value** 컬럼 전체 복사 (예: `sk-ant-sid01-AbCd...`)
   
   ![Session Key Screenshot](https://i.imgur.com/example.png)

### 방법 2: curl 명령어로 확인

```bash
# Chrome/Firefox에서 쿠키 먼저 복사 후
curl -H "Cookie: sessionKey=YOUR_SESSION_KEY" \
     https://claude.ai/api/organizations

# 성공하면 organization 정보 반환:
# [{"uuid":"org-xxx","name":"Personal",...}]
```

---

## 2. AIarmy 설정

### `.env` 파일 편집

```bash
cd /Users/jnnj92/AIarmy
cp .env.example .env
nano .env  # 또는 코드 에디터로 열기
```

### 설정 내용

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Auth Mode: session_key 선택
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTH_MODE=session_key

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Session Key (claude.ai 쿠키에서 복사)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLAUDE_SESSION_KEY=sk-ant-sid01-여기에_복사한_키_붙여넣기

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 나머지는 기본값 사용 (필요하면 수정)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMANDER_MODEL=claude-opus-4-5
SPECIALIST_MODEL=claude-sonnet-4-5
MAX_TOKENS_PER_RUN=8000
MAX_TOKENS_PER_SESSION=100000
```

---

## 3. 실행

```bash
cd /Users/jnnj92/AIarmy
airarmy
```

### 첫 실행 시 나타나는 것

```
  █████╗ ██╗ █████╗ ██████╗ ███╗   ███╗██╗   ██╗
 ██╔══██╗██║██╔══██╗██╔══██╗████╗ ████║╚██╗ ██╔╝
 ███████║██║███████║██████╔╝██╔████╔██║ ╚████╔╝
 ██╔══██║██║██╔══██║██╔══██╗██║╚██╔╝██║  ╚██╔╝
 ██║  ██║██║██║  ██║██║  ██║██║ ╚═╝ ██║   ██║
 ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝   ╚═╝

Session: session-abc12345

You> hello
```

---

## 4. 문제 해결

### ❌ "Session key expired or invalid"

**원인**: Session key가 만료됨 (보통 30일 후)

**해결**:
1. claude.ai에서 다시 로그인
2. 새 session key 복사
3. `.env` 파일의 `CLAUDE_SESSION_KEY` 업데이트
4. AIarmy 재실행

---

### ❌ "Rate limit exceeded. Resets at ..."

**원인**: Claude Pro 메시지 제한 도달

**해결**:
- Pro 플랜: 제한 해제까지 대기 (표시된 시간)
- 또는 Claude Team/Max 플랜으로 업그레이드

**Max 플랜 ($100/월)**은 사실상 무제한입니다.

---

### ❌ "No organizations found"

**원인**: Session key가 잘못 복사됨

**해결**:
1. `sessionKey=` 부분은 **제외**하고 값만 복사
2. 공백이나 줄바꿈 없는지 확인
3. 쿠키 전체를 복사했다면 `sessionKey=sk-ant-sid01-...` 부분만 추출

---

### ⚠️ "Cloudflare challenge" 또는 연결 실패

**원인**: curl-cffi 브라우저 impersonation 실패

**해결**:
```bash
pip install --upgrade curl-cffi
```

일반적으로 자동으로 처리되지만, 계속 실패하면:
- 실제 브라우저(Chrome/Firefox)에서 claude.ai 접속 후 세션 확인
- VPN 사용 중이면 비활성화 후 재시도

---

## 5. Session Key vs API Key 전환

### Session Key → API Key로 전환

```bash
# .env 파일 수정
AUTH_MODE=api_key
ANTHROPIC_API_KEY=sk-ant-api03-...  # console.anthropic.com에서 발급
```

### API Key → Session Key로 전환

```bash
# .env 파일 수정
AUTH_MODE=session_key
CLAUDE_SESSION_KEY=sk-ant-sid01-...  # claude.ai 쿠키
```

재실행만 하면 됩니다. 코드 변경 불필요.

---

## 6. 보안 주의사항

### ⚠️ Session Key는 비밀번호입니다!

- ❌ GitHub에 커밋하지 마세요 (`.env`는 `.gitignore`에 포함됨)
- ❌ 다른 사람과 공유하지 마세요
- ❌ 공개 저장소에 올리지 마세요

### 🔒 안전하게 보관하기

```bash
# .env 파일 권한 제한 (Unix/Mac)
chmod 600 /Users/jnnj92/AIarmy/.env

# 다른 사용자가 읽을 수 없도록
```

### 🔄 정기적으로 갱신하기

Session key는 만료되므로:
- 30일마다 자동 로그아웃됨
- 새 키 발급 후 `.env` 업데이트

---

## 7. 비용 비교 (실제 사용 예시)

### 시나리오: 하루 50개 작업, 각 8K 토큰

| 플랜 | 월 비용 | 조건 |
|------|---------|------|
| API Key | ~$180 | Sonnet 기준 (50 작업 × 30일 × 8K 토큰) |
| Claude Pro | $20 | 메시지 제한 있음 (초과 시 대기) |
| Claude Team | $30/인 | 더 높은 제한 |
| Claude Max | $100 | 사실상 무제한 |

**결론**: 
- 가끔 사용 → API Key
- 이미 구독 중 → Session Key (무료로 AIarmy 사용)
- 매일 많이 사용 → Max 플랜 ($100/월) + Session Key

---

## 8. 기술 세부사항

### 내부 동작 방식

```python
# AIarmy가 session key로 하는 일:

1. Organization ID 조회
   GET https://claude.ai/api/organizations
   Headers: Cookie: sessionKey=...

2. 대화 생성
   POST https://claude.ai/api/organizations/{org_id}/chat_conversations

3. 메시지 전송
   POST .../chat_conversations/{chat_id}/completion
   Body: {"prompt": "...", "timezone": "America/Chicago"}

4. 스트리밍 응답 파싱
   Response: Server-Sent Events (SSE)
   data: {"completion": "Hello there"}
```

### curl-cffi를 사용하는 이유

Cloudflare 차단을 우회하기 위해 실제 브라우저처럼 보이게 합니다:
- `impersonate="chrome110"` — Chrome 브라우저로 위장
- TLS 핑거프린트 일치
- 일반 `requests` 라이브러리는 차단됨

---

## 9. FAQ

### Q: Session key는 얼마나 자주 만료되나요?
A: 보통 30일. 만료되면 재로그인 후 새 키 복사.

### Q: Pro 플랜으로 하루에 몇 개까지 사용 가능한가요?
A: Anthropic이 공개하지 않음. Rate limit 메시지에 `resets_at` 표시됨.

### Q: API Key와 Session Key를 동시에 사용할 수 있나요?
A: 아니요. `.env`의 `AUTH_MODE`로 하나만 선택.

### Q: Session key가 노출되면 어떻게 되나요?
A: 다른 사람이 당신의 Claude 계정으로 메시지 사용 가능. 즉시 claude.ai에서 로그아웃 → 재로그인 → 새 키 발급.

### Q: 비공식 API라 차단될 수 있나요?
A: 가능성은 있지만, 2026년 2월 기준 정상 작동 중. Anthropic이 차단하면 API Key로 전환하면 됩니다.

---

**도움이 필요하면**: GitHub Issues에 질문 남기기
**보안 이슈**: 절대 session key를 공개하지 마세요!
