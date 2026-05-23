#!/bin/bash
set -e

# =============================================================================
# PRISM-INSIGHT Docker Entrypoint Script
# =============================================================================

echo "========================================"
echo "  PRISM-INSIGHT Container Starting"
echo "  Timezone: $TZ"
echo "  Date: $(date)"
echo "========================================"

# Ensure log directory exists
mkdir -p /app/prism-insight/src/var/logs /app/prism-insight/src/var/reports /app/prism-insight/src/var/pdf_reports

# -----------------------------------------------------------------------------
# Cron Setup
# -----------------------------------------------------------------------------

# Check if ENABLE_CRON is set (default: true)
ENABLE_CRON="${ENABLE_CRON:-true}"

if [ "$ENABLE_CRON" = "true" ]; then
    echo "[INIT] Setting up cron..."

    # Install crontab from docker/crontab file
    if [ -f /app/prism-insight/deploy/docker/crontab ]; then
        crontab /app/prism-insight/deploy/docker/crontab
        echo "[INIT] Crontab installed successfully"

        # Show installed crontab
        echo "[INIT] Installed cron jobs:"
        crontab -l | grep -v "^#" | grep -v "^$" | head -20
    else
        echo "[WARN] Crontab file not found: /app/prism-insight/deploy/docker/crontab"
    fi

    # Start cron service
    service cron start
    echo "[INIT] Cron service started"
else
    echo "[INIT] Cron disabled (ENABLE_CRON=false)"
fi

# -----------------------------------------------------------------------------
# Environment Check
# -----------------------------------------------------------------------------

echo ""
echo "[INIT] Environment Check:"
echo "  - Python: $(python3 --version)"
echo "  - Node.js: $(node --version)"
echo "  - Working Dir: $(pwd)"

# -----------------------------------------------------------------------------
# Database Initialization
# -----------------------------------------------------------------------------

echo ""
echo "[INIT] Initializing databases..."

python3 << 'INIT_DB_EOF'
import sqlite3
import sys
import logging
from tracking.db_schema import (
    create_tables,
    create_indexes,
    add_market_column_to_shared_tables,
    migrate_us_performance_tracker_columns,
    migrate_us_watchlist_history_columns,
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "/app/prism-insight/stock_tracking_db.sqlite"

try:
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    logger.info("  [US] Creating US-only canonical tables...")
    create_tables(cursor, conn)
    create_indexes(cursor, conn)
    add_market_column_to_shared_tables(cursor, conn)
    migrate_us_performance_tracker_columns(cursor, conn)
    migrate_us_watchlist_history_columns(cursor, conn)
    logger.info("  [US] Database initialized")

    # =========================================================================
    # Verify Tables Created
    # =========================================================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"  [OK] Database has {len(tables)} tables: {', '.join(sorted(tables)[:10])}...")

    conn.close()
    logger.info("[INIT] Database initialization complete")

except Exception as e:
    logger.error(f"[ERROR] Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
INIT_DB_EOF

if [ $? -ne 0 ]; then
    echo "[ERROR] Database initialization failed!"
    exit 1
fi

# -----------------------------------------------------------------------------
# Run Command or Keep Container Alive
# -----------------------------------------------------------------------------

echo ""
echo "[INIT] Initialization complete"
echo "========================================"

# If arguments are passed, execute them
if [ $# -gt 0 ]; then
    echo "[EXEC] Running: $@"
    exec "$@"
else
    # Keep container running (for cron and interactive use)
    echo "[IDLE] Container is running. Cron jobs will execute on schedule."
    echo "[IDLE] Use 'docker exec' to interact with the container."
    echo "[IDLE] Press Ctrl+C to stop."

    # Keep alive while logging cron output
    tail -f /var/log/cron.log 2>/dev/null || tail -f /dev/null
fi
