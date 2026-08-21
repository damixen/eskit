model: claude-haiku-4-5-20251001

--- Usage ---
Input tokens:  25596
Output tokens: 888
Estimated cost with model:claude-haiku-4-5-20251001: $0.030036

# Creating a Daily Snapshot Workflow

I'll help you set up a daily snapshot workflow using ESKit. Here's a comprehensive guide:

## Basic Daily Snapshot Command

To create a snapshot manually, use:

```bash
eskit snap create <repo>/<snapshot-name> --wait
```

**Example:**
```bash
eskit snap create my-repo/daily-2024-01-15 --wait
```

### Command Options:
- `--wait` - Waits for the snapshot creation to complete before returning
- `--index <pattern>` - Specify which indices to include (e.g., `logs-*` or `--index logs-2024-01-*,metrics-*`)
- `--include_global_state` - Include cluster state in the snapshot
- `--push` - Required if your host is push-protected

## Automated Daily Workflow Setup

### Option 1: Using a Cron Job (Linux/macOS)

Create a shell script `daily-snapshot.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
REPO="my-repo"
SNAPSHOT_NAME="daily-${DATE}"

eskit snap create ${REPO}/${SNAPSHOT_NAME} \
  --index "logs-*,metrics-*" \
  --wait \
  --push
```

Then add to crontab to run daily at 2 AM:

```bash
0 2 * * * /path/to/daily-snapshot.sh >> /var/log/eskit-snapshots.log 2>&1
```

### Option 2: Using Job Scheduling (Windows)

Create a batch file and schedule it using Windows Task Scheduler:

```batch
@echo off
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
eskit snap create my-repo/daily-%mydate% --index "logs-*" --wait --push
```

## Pre-Workflow Checklist

Before automation, ensure:

1. **Repository exists:**
   ```bash
   eskit repo show my-repo
   ```

2. **Host is configured:**
   ```bash
   eskit host show
   ```

3. **Test the snapshot manually:**
   ```bash
   eskit snap create my-repo/test-snapshot --dry-run
   ```

## Monitoring & Management

### List recent snapshots:
```bash
eskit cat snap
```

### Check snapshot details:
```bash
eskit snap show my-repo/daily-2024-01-15
```

### Monitor snapshot progress:
```bash
eskit task get <task-id>
```

## Retention Policy Example

Clean up old snapshots (keep last 7 days):

```bash
#!/bin/bash
REPO="my-repo"
KEEP_DAYS=7
CUTOFF_DATE=$(date -d "${KEEP_DAYS} days ago" +%Y-%m-%d)

# List and delete snapshots older than cutoff
eskit cat snap | while read snapshot; do
  if [[ $snapshot < $CUTOFF_DATE ]]; then
    eskit snap delete ${REPO}/${snapshot} --force --push
  fi
done
```

## Recommended Configuration

For a robust workflow, I suggest:

- **Schedule:** Daily at off-peak hours (e.g., 2-4 AM)
- **Retention:** Keep 7-30 days of snapshots
- **Include indices:** Use patterns like `logs-*`, `metrics-*` to exclude internal indices
- **Logging:** Capture output for monitoring and troubleshooting
- **Notification:** Add alerting if snapshots fail

Would you like help setting up any specific part of this workflow?
