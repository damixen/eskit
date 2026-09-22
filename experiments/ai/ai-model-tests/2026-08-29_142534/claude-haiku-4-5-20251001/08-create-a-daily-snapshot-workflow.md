# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Create a daily snapshot workflow.
- **Elapsed time:** 8.391 seconds

# Response

# Usage ---
- **Input tokens:**  11075
- **Output tokens:** 660
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.014375

I'll help you understand how to create a daily snapshot workflow using ESKit. Let me break this down into the key steps and commands you'll need.

## Daily Snapshot Workflow

A typical daily snapshot workflow involves:

1. **Create a Repository** (if not already created)
2. **Create Daily Snapshots**
3. **Monitor Snapshot Status**
4. **Manage Snapshots** (optional cleanup)

### Step 1: Create a Repository

First, create a snapshot repository to store your snapshots:

```bash
eskit repo create my-daily-repo --type fs --location /path/to/backup/location
```

**Parameters:**
- `my-daily-repo`: Name of your repository
- `--type fs`: File system repository type
- `--location /path/to/backup/location`: Path where snapshots will be stored

### Step 2: Create Daily Snapshots

Create snapshots with a naming convention that includes the date. For example, for daily snapshots:

```bash
eskit snap create my-daily-repo/snapshot-$(date +%Y-%m-%d) --index "*" --wait
```

**Parameters:**
- `my-daily-repo/snapshot-$(date +%Y-%m-%d)`: Repository name and snapshot name with date
- `--index "*"`: Include all indices (or specify specific indices like `index1,index2`)
- `--wait`: Wait for the snapshot to complete before the command returns

### Step 3: Verify Snapshot Status

To check the status of a specific snapshot:

```bash
eskit snap show my-daily-repo/snapshot-$(date +%Y-%m-%d)
```

### Step 4: List All Snapshots

To see all snapshots in your repository:

```bash
eskit cat snap
```

## Automation via Cron

To automate this as a daily job, add to your crontab:

```bash
0 2 * * * /usr/local/bin/eskit snap create my-daily-repo/snapshot-$(date +\%Y-\%m-\%d) --index "*" --wait
```

This runs daily at 2 AM.

## Optional: Snapshot Cleanup

To delete old snapshots after a retention period (e.g., keep last 7 days), you could script:

```bash
eskit snap delete my-daily-repo/snapshot-$(date -d '8 days ago' +%Y-%m-%d) --force
```

**Important Notes:**
- Always verify your repository path is accessible and has sufficient disk space
- Use `--wait` for critical snapshots to ensure they complete before proceeding
- Test your restore process periodically to verify backup integrity
- Consider including global state with `--include_global_state` if needed

Would you like help setting up a specific configuration or understanding any of these commands in more detail?
