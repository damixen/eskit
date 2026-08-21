model: claude-sonnet-5

--- Usage ---
Input tokens:  29619
Output tokens: 731
Estimated cost with model:claude-sonnet-5: $0.066548

# Multi-Step Backup Workflow

Here's a typical ESKit workflow for backing up Elasticsearch data using snapshots. This involves creating a repository (if needed), then taking a snapshot, and verifying it.

## Step 1: Create a Snapshot Repository (one-time setup)

If you don't already have a repository configured, create one:

```
eskit repo create my_backup_repo --location /path/to/backup/folder --type fs
```

- `--location` is required — path to the folder where snapshots will be stored.
- `--type` defaults to `fs` if omitted.

You can preview the request first without executing it:

```
eskit repo create my_backup_repo --location /path/to/backup/folder --dry-run
```

## Step 2: Verify the Repository Exists

```
eskit repo show my_backup_repo
```

## Step 3: Create the Snapshot

```
eskit snap create my_backup_repo/snapshot_2024_01_15 --index my_index* --wait
```

- Name must be in `<repo>/<snapshot>` format.
- `--index` supports wildcards and comma-separated lists; omit to snapshot all indices.
- `--include_global_state` can be added to include cluster state.
- `--wait` blocks until the snapshot finishes.
- Use `--dry-run` first if you want to preview the request.

## Step 4: Confirm the Snapshot Was Created

```
eskit snap show my_backup_repo/snapshot_2024_01_15
```

## Step 5 (Optional): List All Cached Snapshots

If you'd like to pull fresh data and check cached snapshot info:

```
eskit pull
eskit cat snap
```

---

### ⚠️ Notes on Safety
- `repo create` and `snap create` are marked **write** operations — they modify state on the cluster/host.
- If your host is push-protected, you'll need to add `--push` to confirm execution.
- Nothing here is destructive (like `repo delete` or `snap delete`), so no explicit user confirmation step is required for this backup flow. If you later want to **delete** an old snapshot or repository, note that those commands are marked `destructive` and require explicit confirmation before running.
