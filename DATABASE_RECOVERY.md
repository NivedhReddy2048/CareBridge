# CareBridge Database Backup & Rollback Strategy

## Overview
This document outlines the procedures for backing up and restoring the PostgreSQL database, managing Django migrations, and recovering from catastrophic data corruption in the CareBridge Enterprise Platform.

## 1. Automated & Manual Backups
**Render Infrastructure:**
Render automatically provisions daily snapshots for managed PostgreSQL databases.

**Manual Backups (Pre-Deployment):**
Before applying any major migrations, manually create a backup using the provided script:
```bash
# Ensure DATABASE_URL is set in your environment
./scripts/backup_db.sh
```
This script uses `pg_dump` with the custom format (`-F c`) and stores the backup with a timestamp in the `./backups/` directory.

## 2. Restore Procedures (Rollback)
If a deployment fails, data is corrupted, or a destructive migration causes data loss, you must restore the database.

**Restoring from a Dump:**
```bash
./scripts/restore_db.sh ./backups/carebridge_db_20260526_123456.sql
```
- This script uses `pg_restore -c` to cleanly drop existing tables and restore the schema and data.
- **IMPORTANT:** After a database restore, the script attempts to flush the Redis cache (`redis-cli flushall`). Redis persists cached DB query results and session states; flushing ensures consistency between the cache and the restored database.

## 3. Migration Rollback Strategy
If a deployment introduces a bad migration but data is not lost (e.g., adding a buggy column):
1. Identify the problematic app and migration.
2. Reverse the migration locally or via CLI:
   ```bash
   python manage.py migrate <app_name> <previous_migration_name>
   ```
3. Revert the code commit that introduced the bad migration.
4. Redeploy the platform.

**Destructive Migrations:**
Operations like `RemoveField` or dropping tables cannot be reversed via Django migrations if the data was already deleted. In such cases, you MUST perform a full database restore using `restore_db.sh`.

## 4. Storage Recovery Guidance (S3)
- The database stores references (URLs/Paths) to AWS S3 objects.
- If the database is rolled back, any files uploaded *after* the backup was taken will become "orphaned" in S3 (they exist in the bucket but have no database reference).
- S3 objects themselves are not deleted during a DB restore.
- To clean up orphaned files, you will need a periodic cleanup script or AWS S3 Lifecycle rules based on object tagging.
