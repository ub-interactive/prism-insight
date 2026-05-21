# PRISM Archive — 자가개선형 장기투자 인사이트 엔진

> 분석 리포트가 누적될수록, 사용자 대화가 쌓일수록, **답변 품질이 복리로 좋아지는** RAG 시스템.

PRISM Archive는 PRISM-INSIGHT의 일일 주식 분석 리포트를 SQLite FTS5에 영속화하고, 사용자의 자연어 질문을 Claude/GPT에 합성시켜 **장기투자 의사결정을 보조하는 메모리-증강 에이전트**입니다.

단순한 RAG가 아닌, 사용자의 모든 대화·피드백·실제 종목 수익률을 **5계층 지식 메모리**로 통합해 시간이 지날수록 더 정확한 답변을 생산합니다.

---

## ✨ 다른 RAG 시스템과의 차별점

| 보통의 RAG | PRISM Archive |
|---|---|
| 검색 → LLM 합성 → 답변 후 끝 | 답변을 **영구 저장**하고 다음 retrieval에 재활용 |
| 키워드/벡터 단일 검색 | **5계층 컨텍스트** (semantic facts → outcomes → weekly summary → past insights → raw reports) |
| 이전 답변의 정확도 평가 안 함 | **👍/👎 사용자 피드백**으로 confidence 보정, 재검색 시 가중치 자동 적용 |
| 종목 추천만 출력 | **객관적 outcome (실제 수익률·MDD·시장국면)을 컨텍스트에 강제 주입** → "추천했지만 -X%였다"같은 자가비판 가능 |
| 컨텍스트가 누적될수록 토큰 폭증 | 주간 잡이 **Mem0/Auto Dream 패턴**으로 fact를 distill, raw는 superseded 처리 |
| 단일 LLM | Anthropic(MCP function calling)·OpenAI(embedding) 역할 분리, 비용 가드레일 |
| 운영자 전용 | **HTTP·대시보드·커스텀 클라이언트**로 대화형 인사이트에 접근 |

이 모든 게 **SQLite + 두 대의 Vultr 서버 + SSH 터널**로 동작합니다. Neo4j도, Pinecone도, 별도 인프라 없음.

---

## 🚀 도입 배경

PRISM-INSIGHT는 매일 다수 종목의 미국 주식 분석 리포트(MD)를 자동 생성합니다. 누적된 수천 건의 리포트는 단순한 디스크 위 파일에 머물면서:

- 검색 불가 — `grep`이 한계
- 시간 경과 후 인사이트 휘발 — 어떤 추천이 맞고 틀렸는지 잊힘
- 사용자가 "장기투자할 만한 종목 패턴이 뭐야?"같은 메타 질문을 못 함

**PRISM Archive는 이 갭을 메워**, 분석 자산을 살아있는 의사결정 도구로 변환합니다.

핵심 개발 원칙:
- **데이터가 시간이 갈수록 강해진다** (compound knowledge)
- **사용자가 실수를 교정할 수 있다** (RLHF-lite via 👍/👎)
- **객관적 결과로 추측을 보정한다** (outcome grounding)
- **운영 비용은 사이드 프로젝트 수준** (월 $1 미만 가능)

---

## ⚡ 5분 안에 시작하기

```bash
# 1. 의존성
pip install -r requirements.txt

# 2. 필요 시 .env (예: ARCHIVE_API_KEY)
echo "ARCHIVE_API_KEY=your-secret" >> .env

# 3. 마이그레이션
python -c "import asyncio; from cores.archive.archive_db import init_db; asyncio.run(init_db())"

# 4. 기존 리포트 인제스트 (SEASON2_START=2025-09-29 이후만, US)
python -m cores.archive.ingest --dir reports/ --market us

# 5. HTTP API 기동 (예: pipeline 서버에서)
ARCHIVE_API_KEY=your-secret uvicorn archive_api:app --host 127.0.0.1 --port 8765
```

`/query` 또는 `/insight_agent` 엔드포인트로 클라이언트를 붙이거나, `archive_query.py` CLI를 사용하세요. **👍/👎** 피드백 호출은 동일하게 `/feedback` 경로로 제공됩니다.

자세한 옵션은 [DEPLOYMENT.md](DEPLOYMENT.md), 사용법은 [USAGE.md](USAGE.md), 내부 동작은 [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📚 문서 인덱스

| 문서 | 대상 |
|---|---|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 시스템을 이해하려는 개발자 — 5계층 메모리, 자가개선 루프, 데이터 모델 |
| **[USAGE.md](USAGE.md)** | HTTP API·CLI로 아카이브를 조회하려는 사용자 |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 자체 인스턴스를 운영하려는 관리자 — 단일/양서버, env, 보안, 트러블슈팅 |

부가 자료:
- 설계 문서: `docs/superpowers/specs/2026-04-21-persistent-insight-agent-design.md`
- 구현 계획: `docs/superpowers/plans/2026-04-21-persistent-insight-agent.md`

---

## 🛠 핵심 컴포넌트 (소스 트리)

```
cores/archive/
├── archive_db.py            # SQLite 스키마 + DDL + FTS5 트리거
├── ingest.py                # MD 리포트 → archive.db 파이프라인
├── query_engine.py          # 단순 NL 쿼리 (FTS + LLM 합성, /query 엔드포인트)
├── auto_insight.py          # daily/weekly L1·L2 + 주간 압축 + 시맨틱 fact 증류 cron
├── persistent_insights.py   # 영구 인사이트 CRUD, FTS+임베딩 재랭킹, 쿼터, 피드백
├── embedding.py             # OpenAI text-embedding-3-small + BLOB 직렬화
├── insight_prompts.py       # InsightAgent 시스템 프롬프트 (firecrawl 가드레일 포함)
└── insight_agent.py         # mcp-agent + Claude function calling, 5-tier retrieval

archive_api.py               # FastAPI: /health /stats /search /query /insight_agent /feedback
archive_query.py             # CLI (--search / --stats / --insight-stats)

> **Note:** 과거에 별도 채팅 런타임을 붙였다면 HTTP/CLI 경로로 이전하세요.

---

## 📜 라이선스

PRISM-INSIGHT 본 프로젝트의 라이선스를 따릅니다 (`LICENSE`).
