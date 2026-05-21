#!/bin/bash

# Auto-detect project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Enable .pyenv environment
PYENV_ROOT="$HOME/.pyenv"
export PYENV_ROOT
export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
fi

# Configure log file
LOG_FILE="$PROJECT_ROOT/stock_scheduler.log"

# Logging helper
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Change directory to project root
cd "$PROJECT_ROOT" || exit 1

# Check market open day
log "Checking stock market open day"
"$PYTHON_BIN" "$PROJECT_ROOT/check_market_day.py"
MARKET_CHECK=$?

if [ $MARKET_CHECK -ne 0 ]; then
    log "Today is not a stock market open day. Skipping execution."
    exit 0
fi

# Runtime mode
MODE=$1
TODAY=$(date +%Y%m%d)

# Batch log file (daily)
BATCH_LOG_FILE="$PROJECT_ROOT/logs/stock_analysis_${MODE}_${TODAY}.log"
mkdir -p "$PROJECT_ROOT/logs"

# Log selected mode and log path
log "Execution mode: $MODE, log file: $BATCH_LOG_FILE"

# Resolve Python executable (priority: venv > pyenv > system)
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
    log "Using virtualenv Python: $PYTHON_BIN"
elif [ -f "$HOME/.pyenv/shims/python" ]; then
    PYTHON_BIN="$HOME/.pyenv/shims/python"
    log "Using pyenv Python: $PYTHON_BIN"
else
    PYTHON_BIN="python3"
    log "Using system Python: $PYTHON_BIN"
fi

# Log selected mode and log path
log "Execution mode: $MODE, log file: $BATCH_LOG_FILE"

# Run batch in the background
log "Starting $MODE batch in background"
nohup "$PYTHON_BIN" "$PROJECT_ROOT/stock_analysis_orchestrator.py" --mode "$MODE" > "$BATCH_LOG_FILE" 2>&1 &

# Save launched process ID
PID=$!
log "Started with process ID: $PID"

# Create PID file (for status checks)
echo $PID > "$PROJECT_ROOT/logs/stock_analysis_${MODE}_${TODAY}.pid"

log "$MODE batch execution request completed"
exit 0