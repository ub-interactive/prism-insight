#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DAYS_TO_KEEP_LOGS=7
DAYS_TO_KEEP_REPORTS=30

mkdir -p "$PROJECT_ROOT/utils"
echo "$(date): cleanup started" >> "$PROJECT_ROOT/utils/log_cleanup.log"

if [ -d "$PROJECT_ROOT/logs" ]; then
  find "$PROJECT_ROOT/logs" -type f -mtime +$DAYS_TO_KEEP_LOGS -delete
fi

find "$PROJECT_ROOT" -maxdepth 1 -name "*.log*" -type f -mtime +$DAYS_TO_KEEP_LOGS -delete
find "$PROJECT_ROOT" -maxdepth 1 -name "trigger_results_*.json" -type f -mtime +$DAYS_TO_KEEP_LOGS -delete

for dir in "$PROJECT_ROOT/reports" "$PROJECT_ROOT/pdf_reports" "$PROJECT_ROOT/telegram_messages"; do
  if [ -d "$dir" ]; then
    find "$dir" -type f -mtime +$DAYS_TO_KEEP_REPORTS -delete
  fi
done

echo "$(date): cleanup completed" >> "$PROJECT_ROOT/utils/log_cleanup.log"
