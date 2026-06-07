# PRISM-INSIGHT Setup Guide

> Complete installation and configuration guide for PRISM-INSIGHT

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Manual Installation](#manual-installation)
4. [Configuration Files](#configuration-files)
5. [Platform-Specific Setup](#platform-specific-setup)
6. [Optional Components](#optional-components)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Core runtime |
| Node.js | 18+ | MCP servers (Perplexity, Firecrawl) |
| pip | Latest | Package management |

### API Keys (Required for Full Features)

| Service | Purpose | Get Key |
|---------|---------|---------|
| OpenAI | GPT-5 for analysis & trading | [platform.openai.com](https://platform.openai.com/api-keys) |
| Anthropic | Claude for PDF/report generation | [console.anthropic.com](https://console.anthropic.com/) |
| Firecrawl | Web crawling MCP | [firecrawl.dev](https://www.firecrawl.dev/) |
| Perplexity | Web search MCP | [perplexity.ai](https://www.perplexity.ai/) |

### API Keys (Optional)

| Service | Purpose | Get Key |
|---------|---------|---------|
| Korea Investment & Securities | Automated trading | [KIS Developers](https://apiportal.koreainvestment.com/) |

---

## Quick Start with Docker

Docker is the recommended way to run PRISM-INSIGHT in production environments.

### Step 1: Clone Repository

```bash
git clone https://github.com/dragon1086/prism-insight.git
cd prism-insight
```

### Step 2: Prepare Configuration Files

```bash
# LLM/vendor API keys live in `.env` — see `.env.example`.
cp .env.example .env

# MCP layout + model overrides ship as tracked `mcp_agent.config.yaml` (no secrets inside).
```

### Step 3: Build and Run

```bash
# Build and start container
docker-compose up -d

# Check container status
docker ps

# View logs
docker-compose logs -f
```

### Step 4: Run Analysis

```bash
docker exec prism-insight-container python3 -m prism.ops.us.pipelines.stock_analysis_orchestrator --mode morning
```

### Docker Commands Reference

```bash
# Stop container
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View real-time logs
docker-compose logs -f prism-insight

# Access container shell
docker exec -it prism-insight-container /bin/bash
```

> **Note**: The Docker container includes scheduled cron jobs for automated daily analysis. See `docker/entrypoint.sh` for the schedule configuration.

---

## Manual Installation

For development or custom environments, follow these steps for manual installation.

### Step 1: Clone Repository

```bash
git clone https://github.com/dragon1086/prism-insight.git
cd prism-insight
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Prepare Configuration Files

Copy tuning / optional files:

```bash
# OPENAI_API_KEY, ANTHROPIC_API_KEY, optional MCP vendor keys — copy template then edit (.env.example)
cp .env.example .env


# Trading configuration (optional - for automated trading)
cp ./trading/config/kis_devlp.yaml.example ./trading/config/kis_devlp.yaml
```

### Step 4: Configure API Keys

Keys live in **`.env`** (loaded via `python-dotenv` wherever needed).

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
PERPLEXITY_API_KEY=pplx-...
# SEC Edgar MCP user-agent (required for sec-edgar-mcp polite access)
SEC_EDGAR_USER_AGENT="Your Org (contact@yourdomain.example)"
```

### Step 5: Customize MCP Servers (optional)

**`mcp_agent.config.yaml`** is versioned defaults (command lines, timeouts, model map). Edit locally if you add/remove MCP servers — keep secrets out of this file.

> **Note**: Use only US-market MCP servers documented in this repository.

### Step 6: Install Playwright (PDF Generation)

```bash
# Install package (included in requirements.txt)
pip install playwright

# Download Chromium browser
python3 -m playwright install chromium
```

See [Platform-Specific Setup](#platform-specific-setup) for detailed instructions.

### Step 7: Install Perplexity MCP Server

```bash
# Option A: Global install (recommended)
npm install -g @perplexity-ai/mcp-server

# Option B: Use npx (no install needed, runs on demand)
# Tracked `mcp_agent.config.yaml` already uses `npx` for Perplexity
```

## Configuration Files

### Core Settings (Required)

| File | Purpose |
|------|---------|
| `mcp_agent.config.yaml` | Tracked MCP server layout + OpenAI model map (no API keys). |
| `.env` | Secrets + runtime toggles: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, vendor MCP keys, etc. |
### Trading Settings (Optional)

| File | Purpose |
|------|---------|
| `trading/config/kis_devlp.yaml` | Korea Investment & Securities API |

```yaml
# kis_devlp.yaml
default_unit_amount: 10000     # Buy amount per stock (KRW)
auto_trading: true
default_mode: demo             # "demo" or "real"

kis_app_key: "YOUR_APP_KEY"
kis_app_secret: "YOUR_APP_SECRET"
kis_account_number: "12345678-01"
kis_account_code: "01"
```



## Platform-Specific Setup

### macOS

```bash
# Playwright
pip3 install playwright
python3 -m playwright install chromium

```

### Ubuntu / Debian

```bash
# Playwright with dependencies
pip install playwright
python3 -m playwright install --with-deps chromium

```

### Rocky Linux 8 / CentOS / RHEL

```bash
# Playwright
pip3 install playwright
playwright install chromium

# If --with-deps doesn't work, install dependencies manually:
dnf install -y epel-release
dnf install -y nss nspr atk at-spi2-atk cups-libs libdrm \
    libxkbcommon libXcomposite libXdamage libXfixes \
    libXrandr mesa-libgbm alsa-lib pango cairo

# Or use the installation script
cd utils
chmod +x setup_playwright.sh
./setup_playwright.sh

```

### Windows

```bash
# Playwright
pip install playwright
python -m playwright install chromium

```

For detailed Playwright setup, see [tools/playwright-setup.md](../tools/playwright-setup.md).

---

## Optional Components

### Automated Scheduling (Crontab)

Set up automatic execution:

```bash
# Simple setup (recommended)
chmod +x tools/setup_crontab_simple.sh
tools/setup_crontab_simple.sh

# Or advanced setup
chmod +x tools/setup_crontab.sh
tools/setup_crontab.sh
```

See [tools/crontab-setup.md](../tools/crontab-setup.md) for details.

### Morning Analysis

Run analysis using the package module directly:

```bash
# Run analysis
python -m prism.ops.us.pipelines.stock_analysis_orchestrator --mode morning
```

### Event-Driven Trading Signals

For Redis/Upstash or GCP Pub/Sub integration:

```bash
# .env file
UPSTASH_REDIS_REST_URL="https://xxx.upstash.io"
UPSTASH_REDIS_REST_TOKEN="your-token"

# Or for GCP
GCP_PROJECT_ID="your-gcp-project"
GCP_PUBSUB_SUBSCRIPTION_ID="your-subscription"
GCP_CREDENTIALS_PATH="/path/to/service-account.json"
```

---

## Verification

### Quick Test

```bash
python -m prism.ops.us.pipelines.stock_analysis_orchestrator --mode morning
```

### Test Individual Components

```bash
# 1. Test surge stock detection
python -m prism.ops.us.pipelines.trigger_batch morning INFO --output trigger_results.json

# 2. Test PDF conversion
python src/prism/reporting/pdf_converter.py sample.md sample.pdf

# 3. Test MCP server connection
python -m prism.ops.shared.dev.demo AAPL
```

### Expected Output

Successful run will create:
- `trigger_results_*.json` - Detected surge stocks
- `reports/*.md` - Analysis reports in Markdown
- `pdf_reports/*.pdf` - PDF versions of reports
- `var/db/stock_tracking_db.sqlite` - Trading simulation database

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Playwright PDF fails | Run `python3 -m playwright install chromium` |
| MCP server fails | Check API keys in `.env` and process environment |
| Kakao auth fails | Disable 2-step verification or confirm in app |
| JSON parsing error | Library auto-repairs; check logs for details |

### Debug Mode

Enable verbose logging:

```bash
# Set log level in code or environment
export LOG_LEVEL=DEBUG
python -m prism.ops.us.pipelines.stock_analysis_orchestrator --mode morning
```

### Log Files

Check logs for errors:

```bash
# Recent log files
ls -la *.log

# View specific log
tail -f stock_analysis_*.log
```

### Getting Help

- **Documentation**: [docs/](../docs/)
- **GitHub Issues**: [Report bugs](https://github.com/dragon1086/prism-insight/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dragon1086/prism-insight/discussions)

---

## Optional Components

### China A-Share Reports

CN A-share demo reports use [akshare](https://github.com/akfamily/akshare) (included in `requirements.txt`).

```bash
pip install -e .
python -m prism.ops.shared.dev.demo 600519 --market cn --language zh
python -m prism.ops.shared.dev.demo 000001 --market cn --language en
```

- Tickers are bare 6-digit codes (`600519`, `000001`); exchange is inferred automatically.
- Reports are saved under `var/reports/` and `var/pdf_reports/`.
- **Linux PDF with Chinese text:** install CJK fonts, e.g. `apt install fonts-noto-cjk` (Debian/Ubuntu).

---

## Next Steps

After successful setup:

1. **Try the Quick Start**: Run `python -m prism.ops.us.pipelines.stock_analysis_orchestrator --mode morning`
2. **Explore the Dashboard**: Visit [analysis.stocksimulation.kr](https://analysis.stocksimulation.kr/)
3. **Discuss on GitHub**: Open a thread in [Discussions](https://github.com/dragon1086/prism-insight/discussions)
4. **Customize**: Modify agents in `src/prism/core/us/agents/` directory

---

**Document Version**: 1.0
**Last Updated**: 2026-01-28
