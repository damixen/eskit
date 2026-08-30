# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Compose a multi-step backup workflow.
- **Elapsed time:** 7.548 seconds

# Response

# Usage ---
- **Input tokens:**  7593
- **Output tokens:** 572
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.010453

# Multi-Step Backup Workflow

Here's a comprehensive backup workflow using ESKit commands:

## Step 1: Prepare and Verify
First, check your current host and pull the latest cache data:

```bash
eskit host get
eskit pull
```

## Step 2: View Current State
Before backing up, review your repositories, snapshots, and indices:

```bash
eskit cat repo
eskit cat snap
eskit cat index
```

## Step 3: Create or Verify Repository
Ensure you have a backup repository ready:

```bash
eskit repo show my-backup-repo
```

Or create one if needed:

```bash
eskit repo create my-backup-repo --type fs --location /path/to/backup/location
```

## Step 4: Create Snapshot(s)
Create snapshots of your indices. Here are common patterns:

**Backup all indices:**
```bash
eskit snap create my-backup-repo/snapshot-$(date +%Y%m%d-%H%M%S) --index "*" --wait
```

**Backup specific indices:**
```bash
eskit snap create my-backup-repo/logs-backup --index "logs-*,metrics-*" --wait
```

**Include global state (cluster settings, templates, ILM policies):**
```bash
eskit snap create my-backup-repo/full-backup --index "*" --include_global_state --wait
```

## Step 5: Archive to External Location
After snapshotting, optionally archive to an external location:

```bash
eskit archive pull my-archive --contents
```

Or sync with a destination for redundancy:

```bash
eskit archive sync my-archive --contents
```

## Step 6: Verify Backup
Confirm the snapshot was created successfully:

```bash
eskit snap show my-backup-repo/snapshot-20240115-143022
eskit repo show my-backup-repo/snapshot-20240115-143022
```

## Step 7: Monitor Status
Check the overall status:

```bash
eskit status
```

---

## Safety Notes

- Use `--dry-run` flag on any command to preview actions without executing
- The `--wait` flag ensures the operation completes before returning
- Always verify backups exist and are accessible
- For destructive operations, explicit user confirmation is required

This workflow ensures your data is backed up to both Elasticsearch snapshots and optionally to external archives for disaster recovery.
