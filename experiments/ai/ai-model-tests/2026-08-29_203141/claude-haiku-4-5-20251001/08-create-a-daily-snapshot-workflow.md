# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Create a daily snapshot workflow.
- **Elapsed time:** 5.934 seconds

# Response

# Usage ---
- **Input tokens:**  7590
- **Output tokens:** 463
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.009905

# Daily Snapshot Workflow

To create a daily snapshot workflow with ESKit, you'll need to combine several commands. Here's how to set it up:

## Prerequisites

1. **Create a repository** (if you don't have one):
```bash
eskit repo create my-backup --type fs --location /path/to/backup/location
```

2. **Verify the repository exists**:
```bash
eskit repo show my-backup
```

## Daily Snapshot Commands

### Create a daily snapshot
```bash
eskit snap create my-backup/daily-$(date +%Y%m%d) --index "*" --wait
```

This command:
- Creates a snapshot named with today's date (e.g., `daily-20240115`)
- Includes all indices with `--index "*"`
- Waits for completion with `--wait`
- Stores it in the `my-backup` repository

### Optional: Include global state
If you want to backup cluster settings and other global state:
```bash
eskit snap create my-backup/daily-$(date +%Y%m%d) --index "*" --include_global_state --wait
```

## Automation Suggestions

**For Linux/Mac - Add to crontab:**
```bash
0 2 * * * cd /path/to/eskit && eskit snap create my-backup/daily-$(date +\%Y\%m\%d) --index "*" --wait
```
This runs daily at 2 AM.

**For scripting:**
Create a shell script `daily-snapshot.sh`:
```bash
#!/bin/bash
SNAPSHOT_NAME="my-backup/daily-$(date +%Y%m%d)"
eskit snap create "$SNAPSHOT_NAME" --index "*" --wait --verbose
```

## Monitoring

Check snapshot status:
```bash
eskit snap show my-backup/daily-20240115
```

List all snapshots:
```bash
eskit cat snap
```
