> **Operational note:** Mentions of external chat distribution describe retired infrastructure.
> Use `archive_api.py` endpoints (`/health`, `/query`, `/insight_agent`) from your own HTTPS clients.

---

# Deployment

자체 인스턴스에서 PRISM Archive를 운영하기 위한 배포 가이드입니다.

두 가지 배포 모드를 지원합니다:

- **단일 서버 모드** (권장): 한 대의 서버가 분석, archive DB, archive API 게이트웨이를 모두 담당.
- **양 서버 모드**: DB/배치 서버와 선택적 프록시(게이트웨이) 서버를 분리하고 SSH 터널로 연결.

---

## 1. 시스템 요구사항

### 하드웨어 (최소 / 권장)

| 항목 | 최소 | 권장 |
|---|---|---|
| RAM | 2 GB | 4 GB (분석 파이프라인 포함 시) |
| CPU | 1 vCPU | 2 vCPU |
| 디스크 | 10 GB | 50 GB (1년치 리포트 + 가격 히스토리) |
| OS | Ubuntu 22.04+, Debian 12, Rocky 9 | 동일 |

### 소프트웨어

- Python 3.11+
- SQLite 3.38+ (FTS5 지원, 대부분의 최신 리눅스에 기본 포함)
- Node.js 18+ (firecrawl / perplexity MCP 용)
- `uv` / `uvx` (yahoo_finance / sec_edgar / time MCP 용)
- `openssh-client`, `autossh` (양 서버 모드 전용)

### 계정

- **OpenAI API 키** — 임베딩 + 주간 압축 / fact 증류 (`gpt-5.4-mini`)
- **Anthropic API 키** — InsightAgent (`claude-sonnet-4-6`)
- (선택) Perplexity, Firecrawl API 키 — 외부 도구용

---

## 2. 환경변수

프로젝트 루트에 `.env` 생성:

### 필수

```bash
# InsightAgent 쿼터 (KST 자정 리셋)
INSIGHT_DAILY_LIMIT=20
```

### 양 서버 모드 전용

db-server `.env`:
```bash
ARCHIVE_API_KEY=<openssl rand -hex 32>
ARCHIVE_API_HOST=127.0.0.1          # 외부 노출 금지, SSH 터널만 허용
ARCHIVE_API_PORT=8765
```

app-server `.env`:
```bash
ARCHIVE_API_URL=http://127.0.0.1:8765   # SSH 터널 경유
ARCHIVE_API_KEY=<db-server와 동일 값>
```

### LLM / MCP API 키 (`.env` 전용)

OpenAI, Anthropic, Perplexity, Firecrawl 등은 레포에서 제거된 secrets YAML 파일 없이 **`.env`** 에만 두세요 (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등 — `.env.example` 참조).

Perplexity · Firecrawl 는 **`.env`**의 `PERPLEXITY_API_KEY`, `FIRECRAWL_API_KEY` 로 설정합니다. `mcp_agent.config.yaml` 은 MCP 서버 정의만 포함합니다(Git 에서 추적, 비밀 값 없음). 로컬에서만 구조를 덮어쓰려면 `mcp_agent.config.yaml.example` 을 참고해 편집합니다.

### 전체 환경변수 레퍼런스

| 변수 | 기본값 | 설명 |
|---|---|---|
| `ARCHIVE_API_URL` | (없음) | 양 서버 모드 활성화. 미설정 시 단일 서버 모드 |
| `ARCHIVE_API_KEY` | (없음) | Bearer 토큰. `/health` 제외 모든 엔드포인트 보호 |
| `ARCHIVE_API_HOST` | `0.0.0.0` | FastAPI 바인드 주소. SSH 터널 시 `127.0.0.1` |
| `ARCHIVE_API_PORT` | `8765` | FastAPI 포트 |
| `INSIGHT_DAILY_LIMIT` | `20` | `/insight` 사용자당 일일 한도. `0` = 무제한 |

---

## 3. 단일 서버 모드 설치 (5단계)

### Step 1. 코드 & 의존성

```bash
git clone git@github.com:dragon1086/prism-insight.git
cd prism-insight
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install -g npx   # MCP 서버용
```

### Step 2. 설정 파일

```bash
cp .env.example .env
# 저장소에 포함된 기본 `mcp_agent.config.yaml` 사용 또는 로컬에서 편집 — `.env`에 API 키 입력
```

### Step 3. DB 마이그레이션

`init_db()`는 idempotent — 몇 번을 호출해도 안전.

```bash
python -c "import asyncio; from cores.archive.archive_db import init_db; asyncio.run(init_db())"
```

확인:
```bash
sqlite3 archive.db ".tables" | tr ' ' '\n' | grep -iE 'insight|weekly|quota'
# 기대 출력:
# insight_cost_daily
# insight_feedback
# insight_tool_usage
# persistent_insights
# persistent_insights_fts
# ticker_semantic_facts
# user_insight_quota
# weekly_insight_summary
```

### Step 4. 데이터 시드 (리포트 있으면)

```bash
# 기존 분석 리포트 인제스트 (US 전용)
python -m cores.archive.ingest --dir reports/ --market us --dry-run
python -m cores.archive.ingest --dir reports/ --market us

# 장기 가격 히스토리 백필 (20~40분 소요)
python update_current_prices.py --concurrency 2
```

SEASON2_START(`2025-09-29`) 이전 리포트는 자동 스킵.

### Step 5. archive_api 상주 실행

```bash
mkdir -p logs
nohup python archive_api.py >> logs/archive_api.log 2>&1 &
disown
```

기동 로그 확인 예:
```
INFO:     Uvicorn running on http://127.0.0.1:8765
```
(`ARCHIVE_API_HOST`/`ARCHIVE_API_PORT`는 `.env`를 따름.)

### Step 6. cron 등록

```bash
crontab -e
```

```cron
# 일일 인사이트 (매일 02시)
0 2 * * * cd /home/prism/prism-insight && source venv/bin/activate && python -m cores.archive.auto_insight --type daily --market both >> logs/auto_insight.log 2>&1

# 주간 압축 + 시맨틱 fact 증류 (매주 월 03시)
0 3 * * 1 cd /home/prism/prism-insight && source venv/bin/activate && python -m cores.archive.auto_insight --type all --narrative >> logs/auto_insight.log 2>&1

# 장기 가격 업데이트 (매주 월 04시)
0 4 * * 1 cd /home/prism/prism-insight && source venv/bin/activate && python update_current_prices.py --concurrency 2 >> logs/price_update.log 2>&1
```

---

## 4. 양 서버 모드 (DB/배치 서버 + 앱 서버)

PRISM-INSIGHT 본 배포가 양 서버를 쓸 때 사용. archive DB의 디스크/CPU 부하와 공개 HTTP 트래픽을 분리합니다.

### 아키텍처

```
[HTTPS 클라이언트] ──► [app-server 선택: SSH 터널 종단만]
                                │ 127.0.0.1:8765
                                ▼
                       [db-server archive_api + archive.db + cron]
```

### 4-1. db-server 설정

Step 1~4는 단일 서버 모드와 동일. 이후:

```bash
# .env에 추가
cat >> .env <<EOF
ARCHIVE_API_KEY=$(openssl rand -hex 32)
ARCHIVE_API_HOST=127.0.0.1
ARCHIVE_API_PORT=8765
EOF

# 단일 서버 모드에서는 로컬에서 직접 InsightAgent 호출 가능 — archive_api 선택 사항.
nohup python archive_api.py >> logs/archive_api.log 2>&1 &

# 헬스 체크
curl -s http://127.0.0.1:8765/health
# {"status":"ok",...}

# 외부 바인드 확인 (127.0.0.1만 노출되어야 함)
ss -tln | grep 8765
# LISTEN 0  2048  127.0.0.1:8765  0.0.0.0:*
```

### 4-2. app-server 설정

```bash
# 1. 앱 서버에 prism 유저 SSH 키 있는지 확인 (없으면 생성)
sudo -u prism ssh-keygen -t ed25519 -f ~prism/.ssh/id_ed25519 -N ""

# 2. prism 공개 키를 db-server에 등록 (포트 포워드 전용 권한)
PRISM_PUB=$(sudo cat /home/prism/.ssh/id_ed25519.pub)
ssh root@DB_SERVER_IP "echo 'command=\"echo tunnel-only\",no-pty,no-X11-forwarding,no-agent-forwarding,no-user-rc,permitopen=\"127.0.0.1:8765\" $PRISM_PUB' >> ~/.ssh/authorized_keys"

# 3. SSH 터널 wrapper 스크립트
sudo -u prism tee /home/prism/prism-insight/bin/archive_tunnel.sh <<'EOF'
#!/bin/bash
# Persistent SSH tunnel: app-server -> db-server:8765
while true; do
  ssh -N -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
      -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new \
      -L 127.0.0.1:8765:127.0.0.1:8765 \
      root@DB_SERVER_IP
  echo "tunnel exited at $(date), reconnecting in 5s" >&2
  sleep 5
done
EOF
sudo chmod +x /home/prism/prism-insight/bin/archive_tunnel.sh
sudo chown prism:prism /home/prism/prism-insight/bin/archive_tunnel.sh

# 4. 터널 기동
sudo -u prism nohup /home/prism/prism-insight/bin/archive_tunnel.sh \
  >> /home/prism/prism-insight/logs/archive_tunnel.log 2>&1 &

# 5. .env에 app-server 설정 추가
sudo -u prism tee -a /home/prism/prism-insight/.env <<EOF
ARCHIVE_API_URL=http://127.0.0.1:8765
ARCHIVE_API_KEY=<db-server와 동일 값>
INSIGHT_DAILY_LIMIT=20
EOF

# 6. 터널 통해 응답 확인
sudo -u prism curl -s http://127.0.0.1:8765/health
```

### 4-3. app-server (선택 클라이언트 전용 계정 PATH 점검)

app-server에서는 일반적으로 **SSH 터널 + curl 스모크**만 수행하면 됩니다. 별도의 파이썬 장시간 프로세스는 필요 없습니다.

> **주의:** 로컬에서 `uvx` MCP를 실행하는 모든 파이프라인은 login shell 또는 `PATH`에 `~/.local/bin`이 포함되어야 합니다 (`sudo -iu prism …`).

### 4-4. 프로덕션 추천 — systemd 서비스

`/etc/systemd/system/prism-archive-api.service` (db-server):
```ini
[Unit]
Description=PRISM Archive API
After=network.target

[Service]
User=root
WorkingDirectory=/root/prism-insight
EnvironmentFile=/root/prism-insight/.env
ExecStart=/root/prism-insight/bin/python archive_api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/archive-tunnel.service` (app-server):
```ini
[Unit]
Description=SSH tunnel to archive-api on db-server
After=network-online.target

[Service]
User=prism
Environment="AUTOSSH_GATETIME=0"
ExecStart=/usr/bin/autossh -M 0 -N \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new \
  -L 127.0.0.1:8765:127.0.0.1:8765 \
  root@DB_SERVER_IP
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now prism-archive-api           # db-server
systemctl enable --now archive-tunnel              # app-server
```

---

## 5. 보안 체크리스트

- [ ] `ARCHIVE_API_KEY` 32자 이상의 무작위 토큰 (`openssl rand -hex 32`)
- [ ] `ARCHIVE_API_HOST=127.0.0.1` — 공용 인터넷 노출 금지
- [ ] `ss -tln | grep 8765`로 바인드 확인
- [ ] db-server `authorized_keys`에서 app-server 키에 `command="echo tunnel-only", permitopen="127.0.0.1:8765"` 제한 적용
- [ ] `.env` git ignored (`chmod 600 .env`)
- [ ] `.gitignore`에 `archive.db*`, `*.db`, `logs/`, `.env` 포함
- [ ] cron 로그 주기적 로테이션 (logrotate)

---

## 6. 트러블슈팅

### `/insight_agent` 타임아웃 또는 빈 응답

- **단일 서버 모드**: `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 확인. `python archive_query.py --insight-stats`가 에러 없으면 DB는 정상.
- **양 서버 모드**: archive_api 또는 터널 로그에서 `Archive API returned` 같은 메시지를 확인합니다. 터널이 살아 있는지 확인:
  ```bash
  pgrep -af archive_tunnel.sh
  pgrep -af "ssh.*8765:127.0.0.1:8765"
  curl -s http://127.0.0.1:8765/health    # app-server에서
  ```

### `uvx: command not found` 오류

bot / archive_api 프로세스의 PATH에 `~/.local/bin`이 빠짐:
```bash
PID=$(pgrep -f 'archive_api|uvicorn' | head -1)
cat /proc/$PID/environ | tr '\0' '\n' | grep ^PATH=
```

`/home/<user>/.local/bin` 누락이면 login shell로 재시작:
```bash
sudo -iu prism bash -c '...'   # -i 플래그가 .bash_profile 로드
```

### InsightAgent 출력 날짜가 어긋남

InsightAgent 또는 서버 시간대 주입 로직 확인. `cores/archive/insight_agent.py`의 `_build_retrieval_context` 근처 `today_kst` 로직 확인. 서버 시간대 설정 (`date -u`, `timedatectl`) 점검.

### `confidence_score` 컬럼 없다는 오류

오래된 DB. `init_db()` 재실행:
```bash
python -c "
import asyncio
from cores.archive.archive_db import init_db, _initialized_paths
_initialized_paths.clear()
asyncio.run(init_db())
"
```

`_migrate_persistent_insights_columns()`가 idempotent로 컬럼 추가.

### 비용 폭증 대응

```bash
# 일 누적 확인
sqlite3 archive.db "SELECT * FROM insight_cost_daily ORDER BY date DESC LIMIT 7"

# perplexity/firecrawl 호출 급증이면 시스템 프롬프트 가드레일 강화 또는
# INSIGHT_DAILY_LIMIT 축소
```

시스템 프롬프트 (`cores/archive/insight_prompts.py`)에 `각 도구 1회 이하 권장` 조항이 있으나 LLM 지시 준수 여부는 결정적이지 않음. 관찰이 중요.

### DB 백업

```bash
# hot backup (SQLite 기본 툴)
sqlite3 archive.db ".backup backup_$(date +%Y%m%d).db"

# 복구
cp backup_20260422.db archive.db
```

WAL 모드 사용 중이므로 `archive.db-wal`, `archive.db-shm` 파일도 함께 있을 수 있습니다 (정상).

---

## 7. 업그레이드 / 마이그레이션

신규 버전으로 업그레이드:
```bash
git pull origin main
pip install -r requirements.txt
# 스키마 변경 자동 적용 (init_db는 idempotent + ALTER TABLE 마이그레이션 포함)
python -c "
import asyncio
from cores.archive.archive_db import init_db, _initialized_paths
_initialized_paths.clear()
asyncio.run(init_db())
"
# 서비스 재시작
systemctl restart prism-archive-api
```

### 롤백

```sql
-- 모든 Phase B 테이블 제거 (archive 테이블은 유지)
DROP TABLE IF EXISTS insight_feedback;
DROP TABLE IF EXISTS ticker_semantic_facts;
DROP TABLE IF EXISTS persistent_insights;
DROP TABLE IF EXISTS persistent_insights_fts;
DROP TABLE IF EXISTS weekly_insight_summary;
DROP TABLE IF EXISTS insight_tool_usage;
DROP TABLE IF EXISTS user_insight_quota;
DROP TABLE IF EXISTS insight_cost_daily;
DROP VIEW IF EXISTS insight_metrics_daily;
ALTER TABLE persistent_insights DROP COLUMN confidence_score;   -- SQLite 3.35+
```

`report_archive` / `report_enrichment` / `ticker_price_history`는 핵심 데이터이므로 보존.

---

## 8. 참고

- [ARCHITECTURE.md](ARCHITECTURE.md) — 시스템이 어떻게 돌아가는지
- [USAGE.md](USAGE.md) — 사용자 인터페이스 전체
- 설계 의사결정 원본: `docs/superpowers/specs/2026-04-21-persistent-insight-agent-design.md`
