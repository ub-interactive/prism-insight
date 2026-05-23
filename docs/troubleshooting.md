# Troubleshooting - PRISM-INSIGHT

> **Note**: Extended troubleshooting. Quick fixes: [CURSOR.md](../CURSOR.md) · [AGENTS.md](../AGENTS.md).

---

## Common Issues

### Issue 1: Playwright PDF Generation Fails

**Symptoms**:
```
Error: Browser executable not found
```

**Solution**:
```bash
# Install Chromium browser
python3 -m playwright install chromium

# Ubuntu: Install dependencies
python3 -m playwright install --with-deps chromium

# Or use setup script
cd utils && chmod +x setup_playwright.sh && ./setup_playwright.sh
```

---

### Issue 2: Optional Firebase Bridge Not Sending Pushes

**Symptoms**: `firebase_bridge.notify` exits early or mobile QA devices never receive FCM traffic.

**Checklist**:
1. Confirm `.env`: `FIREBASE_BRIDGE_ENABLED=true` and `GOOGLE_APPLICATION_CREDENTIALS` resolves inside the runtime (absolute paths work best under Docker binds).
2. Validate the Firebase project + service-account JSON scopes in GCP/Firebase console.
3. Tail application logs—the bridge absorbs most exceptions but still logs warnings once logging is WARNING+.

---

### Issue 4: MCP Server Connection Failed (e.g. Yahoo Finance MCP)

**Symptoms**:
```
Error: MCP server 'yahoo_finance' not responding
```

**Solution**:
```bash
# 1. Ensure uv / uvx is available
uvx --version

# 2. Verify mcp_agent.config.yaml has the yahoo_finance entry
grep -n "yahoo_finance" src/config/mcp_agent.config.yaml

# 3. Smoke-check the package (needs network).
uvx --from yahoo-finance-mcp yahoo-finance-mcp --help || true

# 4. Confirm API-related secrets for other MCPs (firecrawl, perplexity) in `.env`:
grep -v '^#' .env | grep -E 'FIRECRAWL_|PERPLEXITY_' || true
```

---

### Issue 5: Trading API Authentication Failed

**Symptoms**:
```
Error: KIS API authentication failed
```

**Solution**:
```bash
# 1. Verify kis_devlp.yaml configuration
cat src/prism/trading/config/kis_devlp.yaml

# 2. Check credentials
# - kis_app_key: Valid?
# - kis_app_secret: Valid?
# - kis_account_number: Correct format?

# 3. Test authentication
python -c "from trading.kis_auth import get_access_token; print(get_access_token())"

# 4. Check token expiration (tokens expire every 24 hours)
# Authentication happens automatically on each request
```

---

### Issue 6: JSON Parsing Error in Trading Scenarios

**Symptoms**:
```
Error: Invalid JSON in trading scenario
```

**Solution**:
```python
# 1. Use json-repair for automatic fixing
from json_repair import repair_json
import ujson

try:
    data = ujson.loads(json_str)
except Exception:
    # Attempt repair
    repaired = repair_json(json_str)
    data = ujson.loads(repaired)

# 2. Test JSON validation
python tests/quick_json_test.py

# 3. Check agent output format
# Ensure trading agents return valid JSON structure
```

---

### Issue 7: GPT-5 Output Formatting Issues

**Symptoms**:
- Unexpected `##` headers appearing in output
- Tool call artifacts in generated text
- Markdown formatting inconsistencies

**Solution**:
```python
# cores/utils.py provides automatic cleanup
from cores.utils import clean_markdown

# Automatic fixes applied:
# - Remove GPT-5 tool call artifacts
# - Convert ## headers to bold text in body
# - Add missing newlines after headers
# - Clean up inconsistent markdown

cleaned_text = clean_markdown(raw_output)
```

**Note**: GPT-5 model output requires additional processing compared to GPT-4.1. The `cores/utils.py` file contains several fixes for GPT-5-specific formatting quirks.

---

### Issue 8: prism-us Namespace / Shadowed `cores` Imports

> **Background**: Some older developer trees duplicated the US pipeline inside a `prism-us/` subdirectory and prepended it to `PYTHONPATH`.

**Symptoms**: `ImportError` / `ModuleNotFoundError` referencing `cores.*` even though the modules exist next to `stock_analysis_orchestrator.py`.

**Cause**: Another `cores/` package resolves earlier on `sys.path`, shadowing this repository.

**Fix**:
1. Run tooling from this repository root only (avoid inserting `prism-us/` prefixes into `PYTHONPATH`).
2. If legacy folders remain, reorder `PYTHONPATH` so the canonical project root wins.

**Verification**:
```bash
python -c "import cores, pathlib; print(pathlib.Path(cores.__file__).resolve())"
```

---

### Issue 9: Out of Memory During Analysis

**Symptoms**: Process killed during large batch analysis

**Solution**:
```bash
# 1. Reduce batch size
# Modify stock_analysis_orchestrator.py
MAX_CONCURRENT_ANALYSES = 3  # Reduce from 5

# 2. Lower concurrency knobs in orchestrator / tracking agents if tuned locally

# 3. Increase system memory or swap

# 4. Process stocks individually
for stock_code in stock_list:
    python cores/main.py --stock-code $stock_code
```

---

## Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Set to DEBUG level
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
```

---

## Getting Help

1. **Check logs**: `tail -f log_*.log`
2. **GitHub Issues**: [Report issues](https://github.com/dragon1086/prism-insight/issues)
3. **Documentation**:
   - [README.md](../README.md)
   - [CONTRIBUTING.md](../CONTRIBUTING.md)
   - [utils/CRONTAB_SETUP.md](../utils/CRONTAB_SETUP.md)
   - [utils/PLAYWRIGHT_SETUP.md](../utils/PLAYWRIGHT_SETUP.md)

---

*See also: [CURSOR.md](../CURSOR.md) | [agent-reference.md](agent-reference.md) | [tasks-reference.md](tasks-reference.md)*
