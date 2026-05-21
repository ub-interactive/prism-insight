#!/bin/bash

# =============================================================================
# PRISM-INSIGHT quick crontab setup script
# =============================================================================
# Configure crontab quickly with minimal setup.
# =============================================================================

# Color constants
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 PRISM-INSIGHT Crontab Quick Setup"
echo "=================================="

# Use current directory as project path
PROJECT_DIR=$(pwd)

# Auto-detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found. Install Python first.${NC}"
    exit 1
fi

# Create log directory
mkdir -p "$PROJECT_DIR/logs"

# Create temporary crontab file
TEMP_CRON="/tmp/prism_cron_$$"

# Backup existing crontab
if crontab -l &> /dev/null; then
    echo "📦 Backing up existing crontab..."
    crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d).txt"
    crontab -l > "$TEMP_CRON"
else
    touch "$TEMP_CRON"
fi

# Add PRISM-INSIGHT schedules
cat >> "$TEMP_CRON" << EOF

# === PRISM-INSIGHT automated schedule ===
# 09:30 - Morning analysis (Mon-Fri)
30 9 * * 1-5 cd $PROJECT_DIR && $PYTHON_CMD stock_analysis_orchestrator.py --mode morning >> $PROJECT_DIR/logs/morning.log 2>&1

# 15:40 - Afternoon analysis (Mon-Fri)
40 15 * * 1-5 cd $PROJECT_DIR && $PYTHON_CMD stock_analysis_orchestrator.py --mode afternoon >> $PROJECT_DIR/logs/afternoon.log 2>&1

# 07:00 - Data update (Mon-Fri)
0 7 * * 1-5 cd $PROJECT_DIR && $PYTHON_CMD update_stock_data.py >> $PROJECT_DIR/logs/update.log 2>&1

# 03:00 - Log cleanup
0 3 * * * cd $PROJECT_DIR && bash utils/cleanup_logs.sh 2>&1
EOF

# Install crontab
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"

echo -e "${GREEN}✅ Crontab setup complete!${NC}"
echo ""
echo "📋 Configured schedules:"
echo "  • 09:30 - Morning market analysis"
echo "  • 15:40 - Afternoon market analysis"
echo "  • 07:00 - Data update"
echo "  • 03:00 - Log cleanup"
echo ""
echo "💡 Check: crontab -l"
echo "💡 Remove: crontab -r"
