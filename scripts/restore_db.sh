#!/bin/bash
# CareBridge Database Restore Script
# Usage: ./restore_db.sh <backup_file.sql>

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE not found."
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set."
    exit 1
fi

echo "WARNING: This will overwrite the current database."
read -p "Are you sure you want to restore from $BACKUP_FILE? (y/N): " confirm

if [[ "$confirm" != [yY] ]]; then
    echo "Restore aborted."
    exit 0
fi

echo "Starting database restore from $BACKUP_FILE..."
# Clean the database first, then restore
pg_restore -c -d "$DATABASE_URL" "$BACKUP_FILE"

echo "Restore completed successfully."
# Flush redis cache to prevent stale data issues
if [ -n "$REDIS_URL" ]; then
    echo "Flushing Redis cache..."
    # Warning: this flushes all redis databases on this URL
    redis-cli -u "$REDIS_URL" flushall
fi
