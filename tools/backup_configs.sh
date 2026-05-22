#!/bin/bash

################################################################################
# PRISM-INSIGHT scheduled backup script
# Created: 2025-12-05
# Description: backup key config files and databases
################################################################################

# Backup settings
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_BASE_DIR=~/prism_backups
BACKUP_DIR=$BACKUP_BASE_DIR/$DATE
PROJECT_DIR=$HOME/prism-insight
LOG_FILE=$BACKUP_BASE_DIR/backup.log

# Logging helper
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Create backup directory
mkdir -p $BACKUP_DIR
log "Backup started: $BACKUP_DIR"

# 1. Backup files in repository root
log "Backing up root files..."
cd $PROJECT_DIR

# .env file
if [ -f .env ]; then
    cp .env $BACKUP_DIR/
    log "✓ .env backup complete"
else
    log "⚠ .env file not found"
fi

# mcp_agent config files
for file in mcp_agent.*.yaml; do
    if [ -f "$file" ]; then
        cp "$file" $BACKUP_DIR/
        log "✓ $file backup complete"
    fi
done

# stock_tracking_db.sqlite
if [ -f stock_tracking_db.sqlite ]; then
    cp stock_tracking_db.sqlite $BACKUP_DIR/
    log "✓ stock_tracking_db.sqlite backup complete"
else
    log "⚠ stock_tracking_db.sqlite file not found"
fi

# 2. Backup trading directory
log "Backing up trading directory..."
mkdir -p $BACKUP_DIR/trading/config

if [ -f trading/config/kis_devlp.yaml ]; then
    cp trading/config/kis_devlp.yaml $BACKUP_DIR/trading/config/
    log "✓ trading/config/kis_devlp.yaml backup complete"
else
    log "⚠ trading/config/kis_devlp.yaml file not found"
fi

# 3. Backup examples directory
log "Backing up examples directory..."
mkdir -p $BACKUP_DIR/examples/streamlit

if [ -f examples/streamlit/config.py ]; then
    cp examples/streamlit/config.py $BACKUP_DIR/examples/streamlit/
    log "✓ examples/streamlit/config.py backup complete"
else
    log "⚠ examples/streamlit/config.py file not found"
fi

# Set backup file permissions (security)
find $BACKUP_DIR -type d -exec chmod 700 {} \;
find $BACKUP_DIR -type f -exec chmod 600 {} \;

# Check backup size
BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
log "Backup complete: $BACKUP_SIZE"

# Delete backups older than 7 days
log "Cleaning up old backups..."
find $BACKUP_BASE_DIR -maxdepth 1 -type d -mtime +7 ! -path $BACKUP_BASE_DIR -exec rm -rf {} \; 2>/dev/null
REMAINING=$(find $BACKUP_BASE_DIR -maxdepth 1 -type d ! -path $BACKUP_BASE_DIR | wc -l)
log "Remaining backups: ${REMAINING}"

# Print backup file list
log "Backup file list:"
ls -lh $BACKUP_DIR >> $LOG_FILE 2>&1

log "=========================================="
echo ""
echo "Backup is complete."
echo "Backup location: $BACKUP_DIR"
echo "Backup size: $BACKUP_SIZE"
echo "Log file: $LOG_FILE"
