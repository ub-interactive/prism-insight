> **Operational note:** Mentions of external chat distribution describe retired infrastructure.
> Use `archive_api.py` endpoints (`/health`, `/query`, `/insight_agent`) from your own HTTPS clients.

---

# PRISM-INSIGHT v2.10.0

발표일: 2026년 4월 22일

## 개요

PRISM-INSIGHT v2.10.0은 **AI 자기개선 아카이브 시스템 구축**과 **Firecrawl 시장 인텔리전스 통합**이 핵심입니다.

과거 분석 리포트를 SQLite+FTS5 아카이브에 적재하고, 자연어 쿼리·자동 인사이트 생성·시맨틱 팩트 증류까지 이어지는 3단계 아카이브 파이프라인을 새로 구축했습니다. InsightAgent는 DPO-lite 피드백(👍/👎)과 의미론적 사실 증류(Mem0/Auto Dream 패턴)를 통해 스스로 개선되는 자기개선 루프를 갖춥니다. 같은 릴리스에 Firecrawl AI 기반 `/signal`, `/theme`, `/ask` 실시간 인텔리전스 흐름이 포함되어 있으며, 현재 문서화된 진입점은 `archive_api.py`와 CLI입니다.

**주요 수치:**
- 총 8개 PR (#254 ~ #262)
- 35개 파일 변경, +10,997 / -247 lines
- 신규 서브모듈: `cores/archive/` (10개 파일)

---

## 주요 변경사항

### 1. 아카이브 인사이트 쿼리 시스템 — 3단계 파이프라인 (PR #262) ⭐ 핵심 기능

과거 분석 데이터를 체계적으로 축적하고 AI로 재질의하는 **3단계 아카이브 파이프라인**을 신규 도입했습니다.

#### Phase 1 — 아카이브 DB + 인제스트

| 항목 | 설명 |
|------|------|
| **`cores/archive/archive_db.py`** | SQLite+FTS5 비동기 CRUD, `unicode61` 토크나이저, `_sanitize_fts_query()`로 NL "NOT/AND" 연산자 주입 방지 |
| **`cores/archive/ingest.py`** | 디렉토리 인제스트, `_TRACKER_CONFIG` 화이트리스트, Season 2 필터(≥2025-09-29), `_db_initialized` 센티넬로 중복 DDL 방지 |
| **`cores/archive/data_enricher.py`** | KR(KIS FHKST03010100) + US(yfinance) 가격 보강, look-ahead bias 방지, market_phase 분류 |
| **`stock_analysis_orchestrator.py`** | KR 아카이브 fire-and-forget 인제스트 훅 추가 |

#### Phase 2 — 자연어 쿼리 엔진

| 항목 | 설명 |
|------|------|
| **`cores/archive/query_engine.py`** | 하이브리드 검색(FTS5 + 구조화 필터), OpenAI LLM 합성, 24시간 인사이트 캐시, `_parse_hints()`로 종목/시장/날짜 추출 |
| **`archive_query.py`** | CLI: `--stats`, `--list`, `--search`, `--json`, 자연어 모드 |
| **보안 강화** | 128-bit 캐시 해시, `--model` 화이트리스트, FTS5 토큰레벨 이스케이프 |

#### Phase 3 — 자동 인사이트 엔진

| 생성기 | 설명 |
|--------|------|
| `daily_digest` | 일일 분석 요약 |
| `performance_leaderboard` | 성과 리더보드 (상위 N개 종목) |
| `stop_loss_analysis` | 손절 발동 패턴 분석 |
| `market_phase_report` | 시장 국면별 성과 리포트 |
| `weekly_summary` | LLM 내러티브 포함 주간 요약 |

```bash
# CLI 사용 예
python -m cores.archive.auto_insight --mode weekly
python -m cores.archive.auto_insight --type distill  # 시맨틱 팩트 증류
python archive_query.py "삼성전자 최근 매수 이유"    # 자연어 쿼리
```

---

### 2. InsightAgent 자기개선 레이어 (Phase A+B) ⭐ AI 자율 학습

#### Phase A — `/insight_agent` InsightAgent 레이어

| 항목 | 설명 |
|------|------|
| **`cores/archive/insight_agent.py`** | `AnthropicAugmentedLLM` 기반 Claude 전환, KST 현재 날짜 강제 주입 |
| **`cores/archive/persistent_insights.py`** | 영속적 인사이트 저장, 결과 기반 컨텍스트 그라운딩 |
| **`cores/archive/insight_prompts.py`** | InsightAgent 시스템 프롬프트 관리 |
| **`POST /insight_agent`** | 아카이브 기반 장기 인사이트 조회(JSON API) |

#### Phase B — DPO-lite 피드백 + 시맨틱 팩트 증류

| 항목 | 설명 |
|------|------|
| **인라인 키보드 👍/👎** | `/insight` 응답에 피드백 버튼 추가 → DPO-lite 학습 신호 수집 |
| **`distill_semantic_facts()`** | 최근 30일 persistent_insights에서 티커별 원자적 사실 2~5개 추출 |
| **`ticker_semantic_facts` 테이블** | `fundamental / momentum / risk / sentiment / thesis` 카테고리 + 신뢰도(0.0~1.0) |
| **자기개선 루프** | 주간 크론(auto_insight --mode weekly)에서 팩트 증류 자동 실행 |

```
InsightAgent 컨텍스트 우선순위:
  1순위: ticker_semantic_facts (시맨틱 팩트)
  2순위: persistent_insights (결과 기반 그라운딩)
  3순위: FTS5 풀텍스트 검색 결과
```

---

### 3. Firecrawl 실시간 인텔리전스 + 주간 브리핑 (PR #256 ~ #261) ⭐ 신규 흐름

Firecrawl AI를 활용한 실시간 시장 인텔리전스와 주간 자동 브리핑을 포함했습니다(구 배포에서는 전용 클라이언트가 노출했으나, 현재는 API·CLI 우선입니다).

#### 신규 명령어

| 명령어 | 설명 | 일일 한도 |
|--------|------|-----------|
| `/signal` | KR 이벤트/뉴스 영향 분석 | 제한 없음 |
| `/us_signal` | US 이벤트/뉴스 영향 분석 | 제한 없음 |
| `/theme` | KR 테마/섹터 건강 진단 | 제한 없음 |
| `/us_theme` | US 테마/섹터 건강 진단 | 제한 없음 |
| `/ask` | 자유형식 AI 투자 리서치 | 3회/일 |

#### 주요 구현 상세

| 항목 | 설명 |
|------|------|
| **`firecrawl_client.py`** | 싱글톤 Firecrawl SDK 클라이언트 모듈 |
| **`weekly_firecrawl_intelligence.py`** | 주간 시장 인텔리전스 자동 생성·발행(운영자 정의 출력 경로) |
| **대화형 팔로우업** | 명령어 응답 후 추가 질문 이어가기 지원 |
| **0 결과 처리** | Firecrawl 검색 결과 없을 시 Claude fallback + 쿼리 단순화 재시도 |
| **비용 최적화** | `/agent` → `/search` + Claude Sonnet 패턴으로 전환 (PR #258, #261) |
| **날짜 형식 개선** | 검색 쿼리에 `YYYY-MM` 형식 사용으로 결과 범위 확장 |

```bash
# 주간 인텔리전스 수동 실행
python weekly_firecrawl_intelligence.py
```

> **참고**: `firecrawl-py>=4.22.0` 의존성 추가. `requirements.txt` 업데이트 후 사용하세요.

---

### 4. 포트폴리오 조정 이력 로그 (PR #254)

목표가·손절가 변경 이력을 DB에 추적하고, 변경 맥락을 매도 결정 에이전트에 자동으로 주입합니다.

| 항목 | 설명 |
|------|------|
| **신규 테이블** | `portfolio_adjustment_log` / `us_portfolio_adjustment_log` (KR/US) |
| **추적 필드** | `old/new_target_price`, `old/new_stop_loss`, `adjustment_reason`, `urgency` |
| **라이프사이클** | 보유 종목 매도 시 조정 이력 자동 삭제 |
| **에이전트 주입** | 매도 결정 에이전트 프롬프트에 최근 조정 이력 컨텍스트 자동 포함 |
| **로깅 강화** | 저널 컨텍스트 주입 포인트에 INFO/WARNING 로그 추가 (KR/US) |

---

### 5. 압축 모델 업그레이드 (PR #255)

`tracking/compression.py`의 L3 압축 모델을 `gpt-5.4-mini` → `gpt-5.4`로 상향 조정했습니다.

> 압축 품질 개선 목적. 비용은 소폭 증가할 수 있습니다.

---

## 신규 파일 목록

| 파일 | 설명 |
|------|------|
| `cores/archive/__init__.py` | 아카이브 서브모듈 마커 |
| `cores/archive/archive_db.py` | SQLite+FTS5 비동기 CRUD |
| `cores/archive/auto_insight.py` | 자동 인사이트 생성 엔진 (5개 생성기) |
| `cores/archive/data_enricher.py` | KR/US 가격 보강 (look-ahead bias 방지) |
| `cores/archive/embedding.py` | 임베딩 유틸리티 |
| `cores/archive/ingest.py` | 리포트 디렉토리 인제스트 |
| `cores/archive/insight_agent.py` | InsightAgent (Claude 기반) |
| `cores/archive/insight_prompts.py` | InsightAgent 프롬프트 관리 |
| `cores/archive/persistent_insights.py` | 영속적 인사이트 + 시맨틱 팩트 |
| `cores/archive/price_tracker.py` | 가격 추적기 |
| `cores/archive/query_engine.py` | 자연어 쿼리 엔진 |
| `archive_api.py` | 아카이브 REST API |
| `archive_query.py` | 아카이브 CLI |
| `firecrawl_client.py` | Firecrawl SDK 싱글톤 클라이언트 |
| `weekly_firecrawl_intelligence.py` | 주간 인텔리전스 스크립트 |
| `update_current_prices.py` | 현재가 일괄 업데이트 유틸리티 |
| `docs/archive/ARCHIVE_API_SETUP.md` | 아카이브 API 설정 가이드 |
| `docs/archive/ARCHIVE_DEPLOY_GUIDE.md` | 아카이브 배포 가이드 |
| `docs/archive/ARCHIVE_VALIDATION.md` | 아카이브 검증 시나리오 |

---

## 변경된 주요 파일

| 파일 | PR | 변경 내용 |
|------|----|-----------|
| `archive_api.py` | #256~#262 | InsightAgent `/insight_agent` 노출 등 아카이브 HTTP 표면·Firecrawl 연동 |
| `cores/archive/auto_insight.py` | #262 | 5개 인사이트 생성기, distill_semantic_facts() 추가 |
| `cores/archive/insight_agent.py` | #262 | Claude(AnthropicAugmentedLLM) 전환, KST 날짜 주입 |
| `cores/archive/persistent_insights.py` | #262 | 영속적 인사이트, 결과 기반 그라운딩, 시맨틱 팩트 |
| `stock_tracking_enhanced_agent.py` | #254 | 포트폴리오 조정 이력 로그 + 에이전트 주입 |
| `tracking/db_schema.py` | #254 | `portfolio_adjustment_log` 테이블 추가 |
| `prism-us/tracking/db_schema.py` | #254 | `us_portfolio_adjustment_log` 테이블 추가 |
| `tracking/compression.py` | #255 | gpt-5.4-mini → gpt-5.4 |
| `stock_analysis_orchestrator.py` | #262 | 아카이브 인제스트 훅 추가 |
| `requirements.txt` | #256, #262 | firecrawl-py, aiosqlite 등 의존성 추가 |

---

## 업데이트 방법

### 1. 코드 업데이트

```bash
git pull origin main
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

신규 패키지: `firecrawl-py>=4.22.0`, `aiosqlite`

### 3. 아카이브 DB 초기화 (신규)

아카이브 시스템은 첫 실행 시 자동으로 `archive.db`를 생성합니다. 수동 초기화가 필요하면:

```bash
python archive_query.py --stats  # DB 초기화 + 통계 확인
```

### 4. 아카이브 인제스트 (선택사항)

기존 분석 리포트를 소급 적재하려면:

```bash
python -m cores.archive.ingest --dir ./reports  # 기존 리포트 일괄 인제스트
```

### 5. 포트폴리오 조정 로그 테이블 (자동 마이그레이션)

`portfolio_adjustment_log` / `us_portfolio_adjustment_log` 테이블은 첫 실행 시 자동 생성됩니다. 별도 조치 불필요합니다.

### 6. 동작 확인

```bash
# KR 전체 파이프라인 (외부 메시징 비활성화 상태)
python stock_analysis_orchestrator.py --mode morning

# 아카이브 자연어 쿼리 테스트
python archive_query.py "삼성전자 최근 분석 요약"

# 자동 인사이트 생성 테스트
python -m cores.archive.auto_insight --mode daily --dry-run
```

---

## 알려진 제한사항

1. **아카이브 인제스트 대상**: Season 2(2025-09-29 이후) 분석 리포트만 인제스트됩니다. 이전 데이터는 수동 변환 또는 별도 처리가 필요합니다.
2. **Firecrawl API 키**: `/signal`, `/theme`, `/ask` 명령어 사용 시 `.env`에 `FIRECRAWL_API_KEY` 설정이 필요합니다.
3. **시맨틱 팩트 증류**: `persistent_insights`에 데이터가 충분히 쌓인 후(티커당 2건 이상) 실효적으로 동작합니다.
4. **압축 모델 변경**: gpt-5.4로 상향 조정되어 L3 압축 단계 비용이 소폭 증가할 수 있습니다.
---

## 외부 배포 공지 (아카이브)

v2.10.0 당시 별도 구독자용 마케팅 카피가 문서 하단에 실렸습니다. 해당 경로와 논조는 현재 레포에서 제거되었으며, 동일 기능은 `archive_api.py`, `archive_query.py`, `docs/archive/` 문서와 운영자 정의 출력으로 사용합니다.
