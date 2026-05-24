---
name: prism-reports
description: >-
  Report output paths for PRISM-INSIGHT agent prompts and PDF/markdown reports.
  Use when editing src/prism/core/agents/, report_generation.py,
  report_generator.py, or English user-facing report copy.
---

# PRISM-INSIGHT reports

## Output paths

`src/var/reports/`, `src/var/pdf_reports/` — use `prism.paths` (`REPORTS_DIR`, `PDF_REPORTS_DIR`).

## Language

- Analysis agents and synthesis prompts run in **English**.
- Non-English output uses `prism.reporting.translation` (`apply_report_output_language`) after the final markdown is assembled.
- Model key: `openai.models.us_translation` in `src/config/mcp_agent.config.yaml`.
- Code comments and logs: English.
