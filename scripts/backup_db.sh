#!/bin/bash
# CareBridge Database Backup Script
# Usage: ./backup_db.sh

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/carebridge_db_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set."
    exit 1
fi

echo "Starting database backup to $BACKUP_FILE..."
# Use pg_dump via the DATABASE_URL connection string
pg_dump "$DATABASE_URL" -F c -f "$BACKUP_FILE"

echo "Backup completed successfully."
ls -lh "$BACKUP_FILE"
