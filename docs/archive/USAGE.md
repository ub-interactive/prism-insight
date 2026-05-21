# Usage

PRISM Archive는 **`archive_api` FastAPI 서버**와 **`archive_query` CLI**로 운영합니다.

> 과거 대화형 `/insight` 예시는 제거되었습니다. 동일한 기능은 HTTP `/insight_agent`·`/query`와 `archive_query.py` CLI로 제공됩니다.

---

## 1. HTTP API (양 서버 또는 직접 호출)

archive_api.py가 노출하는 6개 엔드포인트.

### 인증

기본은 Bearer 토큰 (`ARCHIVE_API_KEY`). `/health`만 무인증.

```bash
KEY=$ARCHIVE_API_KEY    # .env에서 로드
```

### `GET /health`

서버 상태 확인. 인증 없음.

```bash
curl http://127.0.0.1:8765/health
# {"status":"ok","archive_db":true,"archive_db_size_mb":1018.53}
```

### `GET /stats`

리포트 통계. 응답의 `reports_by_market`에는 DB에 실제로 저장된 시장 값별 건수가 포함됩니다(과거에 적재된 `kr` 행이 있으면 표시될 수 있음). **인제스트·검색·쿼리 API는 US 전용**입니다.

```bash
curl -H "Authorization: Bearer $KEY" http://127.0.0.1:8765/stats
```

### `GET /search?keyword=&market=&limit=`

FTS5 키워드 검색 (LLM 합성 없음).

```bash
curl -H "Authorization: Bearer $KEY" \
  "http://127.0.0.1:8765/search?keyword=semiconductor&market=us&limit=10"
```

### `POST /query` (단순 자연어 질문)

기존 단일 LLM 합성 경로. `/insight_agent`보다 가벼움.

```bash
curl -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  http://127.0.0.1:8765/query \
  -d '{"question":"하락장 반도체 30일 수익률은?","market":"us"}'
```

### `POST /insight_agent` ⭐ (메인 엔드포인트)

5계층 retrieval + Claude function calling + 자동 저장.

```bash
curl -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  http://127.0.0.1:8765/insight_agent \
  -d '{
    "question": "NVDA 장기투자 적합한가?",
    "user_id": 12345,
    "chat_id": -100200300,
    "daily_limit": 20,
    "previous_insight_id": null
  }'
```

응답:
```json
{
  "answer": "...",
  "key_takeaways": ["...", "..."],
  "tickers_mentioned": ["NVDA"],
  "tools_used": ["yahoo_finance_get_quote"],
  "evidence_count": 3,
  "insight_id": 7,
  "remaining_quota": 19,
  "model_used": "claude-sonnet-4-6"
}
```

**파라미터**:
- `daily_limit` (default 20): 사용자당 일일 한도. `0` = 무제한 (권장 X).
- `previous_insight_id`: 멀티턴 체인 추적용. 클라이언트 세션 또는 프런트엔드가 연속 질문에 넣습니다.

### `POST /feedback` ⭐ (자가개선 신호)

사용자 👍/👎 신호 기록.

```bash
curl -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  http://127.0.0.1:8765/feedback \
  -d '{"insight_id":7, "user_id":12345, "score":-1, "reason":"수익률 잘못 인용"}'
```

응답:
```json
{"ok": true, "insight_id": 7, "new_confidence": -0.2}
```

`score`는 `+1` / `-1` / `0`(중립). 같은 (insight_id, user_id) 재투표 시 덮어씀.

---

## 2. CLI (`archive_query.py`)

DB가 있는 머신에서 직접 실행하는 도구.

### `--stats` — 아카이브 기본 통계

```bash
python archive_query.py --stats
```

```
=== PRISM 아카이브 통계 ===
  US    167건  2025-09-29 ~ 2026-03-31
  enriched:          968건
  cached insights:     0건
```

### `--insight-stats` ⭐ — 누적 인사이트 + 비용

```bash
python archive_query.py --insight-stats
```

```
=== /insight 통계 ===
  총 인사이트:     7
  고유 사용자:     4
  주간 요약:       0

  도구 사용 분포:
    yahoo_finance_get_quote  5회
    archive_search_insights    1회

  최근 7일 비용:
    2026-04-22  in=0  out=0  emb=0  perp=0  fc=0
```

### `--search "키워드"` — FTS5 검색

```bash
python archive_query.py --search "semiconductor" --market us --limit 10
```

### `--list` — 리포트 목록

```bash
python archive_query.py --list --ticker AAPL --date-from 2026-01-01
```

### 자연어 질문 (LLM 합성)

```bash
python archive_query.py "하락장에서 분석된 테크 종목 30일 수익률은?" --market us
```

`--skip-cache`로 캐시 무시, `--model gpt-5.4-mini` 로 모델 지정 가능.

### `--json` — 모든 출력 JSON 형식

```bash
python archive_query.py --insight-stats --json
```

---

## 3. 백그라운드 잡

`auto_insight.py`의 cron 옵션:

```bash
# 일일 인사이트 (매일 새벽 2시 권장)
python -m cores.archive.auto_insight --type daily --market us

# 주간 압축 + 시맨틱 fact 증류 (매주 월 새벽 3시 권장)
python -m cores.archive.auto_insight --type all --narrative

# 수동: 특정 주 압축
python -m cores.archive.auto_insight --type compress --week-start 2026-04-14 --week-end 2026-04-20

# 수동: 30일치 인사이트로부터 fact 증류
python -m cores.archive.auto_insight --type distill --distill-window 30
```

`--type all`은 daily + leaderboard + stoploss + phase + weekly + 압축 + fact 증류를 모두 실행. 주간 cron 1번이면 자가개선 루프가 자동으로 돌아갑니다.

### 신규 리포트 인제스트

```bash
# dry-run으로 파싱 검증
python -m cores.archive.ingest --dir reports/ --market us --dry-run

# 실제 인제스트 (SEASON2_START=2025-09-29 이후만 통과)
python -m cores.archive.ingest --dir reports/ --market us
```

매일 분석 파이프라인이 자동 호출하므로 일반적으론 수동 실행 불필요.

### 장기 가격 백필

```bash
# return_30d / return_90d / return_365d / MDD 등 enrichment 채우기
python update_current_prices.py --concurrency 2
```

새벽(01~05시) 권장 — 분석 파이프라인과 시간대 분리.

---

## 4. 자주 쓰는 패턴

### 회고 분석 (백테스트 풍)

```
/insight 손절 발동 후 회복한 종목 비율은?
/insight 하락장에서 +50% 오른 종목 공통점
/insight MDD 10% 이내 + 30% 수익 종목 특징
```

### 종목 의사결정 보조

```
/insight NVDA 장기투자 적합한가?
/insight MU vs AMD, 어느 쪽 변동성이 낮았나?
```

### 메타 분석

`/insight_agent` 본문 예시:

```
반도체 winner 패턴은?
시장 국면별 가장 안정적인 섹터는?
```

### 후속 질문 (동일 세션)

`previous_insight_id` 와 함께 다시 `/insight_agent` 를 호출해 좁혀갑니다:

```
1차 질문 → 응답 id=42
후속: "방금 결과 중 PER 15 이하만 남겨줘" + previous_insight_id=42
```

---

## 5. 한계 — 이 시스템이 잘 못 하는 것

- ❌ **단기 예측** ("내일 오를까?") — 시스템 설계 영역 외
- ❌ **실시간 호가** — Yahoo Finance 등 MCP는 종가/일봉 기준
- ❌ **개인화 메모리** — 모든 사용자가 공용 풀 공유 (의도된 설계, 추후 user_id 격리 옵션 검토)
- ❌ **가짜 답변 무조건 차단** — Claude 환각 가능성 존재. **👎 피드백으로 점진적 학습** 필요
- ❌ **outcome 검증 자동화 없음** — 인사이트의 사후 정확도는 사람이 평가해야 (`/insight 6개월 전 인사이트가 맞았는지` 같은 메타 질문은 가능)

---

## 6. 다음 단계

- 운영자: [DEPLOYMENT.md](DEPLOYMENT.md)
- 내부 동작 이해: [ARCHITECTURE.md](ARCHITECTURE.md)
