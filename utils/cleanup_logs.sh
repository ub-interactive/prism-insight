#!/bin/bash

# Auto-detect project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"  # parent directory of utils

# Retention policy
DAYS_TO_KEEP_LOGS=7      # log files: 7 days
DAYS_TO_KEEP_REPORTS=30  # PDF/MD reports: 30 days

# Create utils directory if missing
mkdir -p "$PROJECT_ROOT/utils"

# Log start time
echo "$(date): log cleanup started" >> "$PROJECT_ROOT/utils/log_cleanup.log"

# =============================================================================
# 1. Log file patterns (7-day retention)
# =============================================================================
LOG_PATTERNS=(
    # KR market
    "ai_bot_*.log*"
    "trigger_results_morning_*.json"
    "trigger_results_afternoon_*.json"
    "*stock_tracking_*.log"
    "orchestrator_*.log"
    # US market
    "us_orchestrator_*.log"
    "trigger_results_us_*.json"
    # Compression logs
    "compression_*.log"
    # Macroeconomic intelligence
    "macro_intelligence_kr_*.json"
    "macro_intelligence_us_*.json"
)

# Delete logs older than 7 days in project root
for PATTERN in "${LOG_PATTERNS[@]}"; do
    find "$PROJECT_ROOT" -maxdepth 1 -name "$PATTERN" -type f -mtime +$DAYS_TO_KEEP_LOGS -exec rm {} \;
done

# =============================================================================
# 2. prism-us directory logs (7-day retention)
# =============================================================================
PRISM_US_DIR="$PROJECT_ROOT/prism-us"

if [ -d "$PRISM_US_DIR" ]; then
    # US performance tracker logs
    find "$PRISM_US_DIR" -maxdepth 1 -name "us_performance_tracker_*.log" -type f -mtime +$DAYS_TO_KEEP_LOGS -exec rm {} \;

    # US macroeconomic intelligence
    find "$PRISM_US_DIR" -maxdepth 1 -name "macro_intelligence_us_*.json" -type f -mtime +$DAYS_TO_KEEP_LOGS -exec rm {} \;

    # US scheduler log (truncate on Sundays)
    if [ $(date +%u) -eq 7 ]; then
        US_SCHEDULER_LOG="$PRISM_US_DIR/us_stock_scheduler.log"
        if [ -f "$US_SCHEDULER_LOG" ]; then
            > "$US_SCHEDULER_LOG"
            echo "$(date): truncated prism-us/us_stock_scheduler.log" >> "$PROJECT_ROOT/utils/log_cleanup.log"
        fi
    fi
fi

# =============================================================================
# 3. Process accumulated logs in logs directory (truncate on Sundays)
# =============================================================================
LOGS_DIR="$PROJECT_ROOT/logs"
if [ -d "$LOGS_DIR" ] && [ $(date +%u) -eq 7 ]; then
    LOG_ACCUMULATING_PATTERN="stock_analysis_*.log"
    find "$LOGS_DIR" -name "$LOG_ACCUMULATING_PATTERN" -type f -exec sh -c '> {}' \;
    echo "$(date): truncated accumulated logs under logs directory" >> "$PROJECT_ROOT/utils/log_cleanup.log"
fi

# =============================================================================
# 4. PDF/MD report files (30-day retention)
# =============================================================================

# KR market PDF reports
KR_PDF_DIR="$PROJECT_ROOT/pdf_reports"
if [ -d "$KR_PDF_DIR" ]; then
    DELETED_KR_PDF=$(find "$KR_PDF_DIR" -name "*.pdf" -type f -mtime +$DAYS_TO_KEEP_REPORTS -exec rm {} \; -print | wc -l)
    if [ "$DELETED_KR_PDF" -gt 0 ]; then
        echo "$(date): deleted ${DELETED_KR_PDF} KR PDF reports (older than 30 days)" >> "$PROJECT_ROOT/utils/log_cleanup.log"
    fi
fi

# US market PDF reports
US_PDF_DIR="$PRISM_US_DIR/pdf_reports"
if [ -d "$US_PDF_DIR" ]; then
    DELETED_US_PDF=$(find "$US_PDF_DIR" -name "*.pdf" -type f -mtime +$DAYS_TO_KEEP_REPORTS -exec rm {} \; -print | wc -l)
    if [ "$DELETED_US_PDF" -gt 0 ]; then
        echo "$(date): deleted ${DELETED_US_PDF} US PDF reports (older than 30 days)" >> "$PROJECT_ROOT/utils/log_cleanup.log"
    fi
fi

# US market MD reports
US_REPORTS_DIR="$PRISM_US_DIR/reports"
if [ -d "$US_REPORTS_DIR" ]; then
    DELETED_US_MD=$(find "$US_REPORTS_DIR" -name "*.md" -type f -mtime +$DAYS_TO_KEEP_REPORTS -exec rm {} \; -print | wc -l)
    if [ "$DELETED_US_MD" -gt 0 ]; then
        echo "$(date): deleted ${DELETED_US_MD} US MD reports (older than 30 days)" >> "$PROJECT_ROOT/utils/log_cleanup.log"
    fi
fi

# =============================================================================
# 5. Telegram message files (30-day retention)
# =============================================================================

# KR Telegram messages
KR_TELEGRAM_DIR="$PROJECT_ROOT/telegram_messages"
if [ -d "$KR_TELEGRAM_DIR" ]; then
    find "$KR_TELEGRAM_DIR" -type f -mtime +$DAYS_TO_KEEP_REPORTS -exec rm {} \;
fi

# US Telegram messages
US_TELEGRAM_DIR="$PRISM_US_DIR/telegram_messages"
if [ -d "$US_TELEGRAM_DIR" ]; then
    find "$US_TELEGRAM_DIR" -type f -mtime +$DAYS_TO_KEEP_REPORTS -exec rm {} \;
fi

# =============================================================================
# 6. Result summary
# =============================================================================

# Count and log remaining files after cleanup
REMAINING_LOGS=0
for PATTERN in "${LOG_PATTERNS[@]}"; do
    COUNT=$(find "$PROJECT_ROOT" -maxdepth 1 -name "$PATTERN" 2>/dev/null | wc -l)
    REMAINING_LOGS=$((REMAINING_LOGS + COUNT))
done

# Remaining report file count
REMAINING_PDF=0
[ -d "$KR_PDF_DIR" ] && REMAINING_PDF=$((REMAINING_PDF + $(find "$KR_PDF_DIR" -name "*.pdf" 2>/dev/null | wc -l)))
[ -d "$US_PDF_DIR" ] && REMAINING_PDF=$((REMAINING_PDF + $(find "$US_PDF_DIR" -name "*.pdf" 2>/dev/null | wc -l)))

echo "$(date): log cleanup complete - remaining logs: $REMAINING_LOGS, remaining PDFs: $REMAINING_PDF" >> "$PROJECT_ROOT/utils/log_cleanup.log"
