# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25599
- **Output tokens:** 961
- **Estimated cost:** $0.030404

## Response

# Multi-Step Backup Workflow for ESKit

Here's a comprehensive backup workflow that demonstrates best practices for protecting your Elasticsearch data:

## Workflow Overview

### Step 1: Prepare and Validate
```bash
# Set the target host
eskit host set production

# Verify current status
eskit status --json

# Pull latest repository and snapshot information
eskit pull es
```

### Step 2: Create a Snapshot Repository
```bash
# Create a filesystem-based backup repository
eskit repo create backup-repo \
  --type fs \
  --location /backup/elasticsearch/snapshots \
  --dry-run

# Execute the creation (add --push if host is push-protected)
eskit repo create backup-repo \
  --type fs \
  --location /backup/elasticsearch/snapshots \
  --push
```

### Step 3: Create Full Cluster Snapshot
```bash
# Create a comprehensive snapshot of all indices and global state
eskit snap create backup-repo/full-backup-$(date +%Y%m%d-%H%M%S) \
  --index "*" \
  --include_global_state \
  --ignore_unavailable true \
  --wait \
  --push
```

### Step 4: Create Selective Snapshots (Optional)
```bash
# Backup specific index patterns
eskit snap create backup-repo/logs-backup-$(date +%Y%m%d-%H%M%S) \
  --index "logs-*" \
  --ignore_unavailable true \
  --wait \
  --push

# Backup critical indices
eskit snap create backup-repo/critical-backup-$(date +%Y%m%d-%H%M%S) \
  --index "critical-*,production-*" \
  --include_global_state \
  --wait \
  --push
```

### Step 5: Verify Snapshots
```bash
# List all snapshots in the repository
eskit cat snap

# Show detailed information about the latest snapshot
eskit snap show backup-repo/full-backup-20240115-143022 --json

# Check snapshot status
eskit snap show backup-repo/full-backup-20240115-143022 \
  --fields "snapshot,state,indices,start_time,end_time"
```

### Step 6: Archive to Remote Location (Optional)
```bash
# Pull snapshot data to local archive
eskit archive pull backup-repo \
  --preview \
  --contents

# Sync with remote archive location
eskit archive sync backup-repo \
  --dst remote-host:/archive/backups \
  --preview
```

### Step 7: Monitor Backup Progress
```bash
# Check running tasks
eskit task get <task_id>

# List recent backup jobs
eskit job list --local --json
```

### Step 8: Document and Cleanup (Optional)
```bash
# Review snapshot details
eskit snap show backup-repo/full-backup-20240115-143022 --view detailed

# Delete old snapshots if retention policy requires it
eskit snap delete backup-repo/old-snapshot-20240101 \
  --force \
  --dry-run \
  --push
```

## Safety Features Used

- **`--dry-run`**: Preview changes before execution
- **`--push`**: Confirm modifications on protected hosts
- **`--wait`**: Ensure operations complete before proceeding
- **`--preview`**: Test archive operations safely
- **`--ignore_unavailable true`**: Handle missing indices gracefully

## Best Practices

1. **Schedule regularly**: Run this workflow daily/weekly based on data criticality
2. **Verify restorability**: Periodically test snapshot restoration
3. **Monitor logs**: Check verbose output for warnings
4. **Document snapshots**: Use descriptive names with timestamps
5. **Test recovery**: Practice restoration procedures
6. **Automate cleanup**: Remove old snapshots based on retention policy
7. **Secure backups**: Store backups in protected locations with access controls

This workflow ensures comprehensive data protection with validation at each step.
