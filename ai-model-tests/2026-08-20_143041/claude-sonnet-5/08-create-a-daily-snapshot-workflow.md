# Test

- **Model:** claude-sonnet-5
- **Input tokens:** 29618
- **Output tokens:** 1349
- **Estimated cost:** $0.072726

## Response

Here's how to set up a daily snapshot workflow using ESKit's `snap` and `repo` commands. ESKit itself does not include a built-in scheduler, so the "daily" part is achieved by running the `eskit snap create` command on a recurring basis (e.g. via cron or a scheduled task), while ESKit handles the actual snapshot creation against Elasticsearch.

### 1. Make sure a repository exists

Snapshots are stored in a repository. Create one once, if not already set up:

```
eskit repo create <repo_name> --location <path_to_repo_folder>
```

- `--type` defaults to `fs` (filesystem repository).
- If the host is push-protected, you'll need to add `--push` to confirm the write.

You can verify it exists with:
```
eskit repo show <repo_name>
```

### 2. Create the daily snapshot

Snapshots must be named as `<repo>/<snapshot>`. For a daily workflow, you'd typically include a date in the snapshot name so each day's run creates a unique snapshot instead of overwriting a previous one:

```
eskit snap create <repo_name>/<snapshot_name> --wait
```

Example, using a dynamically generated date-based name (this is standard shell scripting around the command, not an ESKit feature):

```
eskit snap create my_repo/daily-$(date +%F) --wait
```

Optional flags you may find useful:
- `--index <pattern>` — limit the snapshot to specific indices (supports wildcards and comma-separated lists). Omit to snapshot everything.
- `--include_global_state` — include cluster state in the snapshot.
- `--wait` — wait for snapshot completion before the command returns (useful for scripting/cron so you know when it's done).
- `-dry`/`--dry-run` — preview the request without executing it.
- `--push` — required confirmation if the target host is push-protected.

### 3. Schedule it daily

Since ESKit doesn't have a native scheduler, wrap the `eskit snap create` command in a cron job (or similar) on the machine running ESKit, e.g.:

```
0 2 * * * eskit snap create my_repo/daily-$(date +\%F) --wait --host prod
```

This runs the snapshot every day at 2 AM against the `prod` host.

### 4. (Optional) Verify or clean up old snapshots

- Check existing snapshots: `eskit repo show <repo>` or `eskit snap show <repo>/<snapshot>`
- Delete old snapshots if you need retention management: `eskit snap delete <repo>/<snapshot>` — **note this is a destructive operation** and requires explicit user confirmation before running (ESKit will prompt unless `--force` is used, and `--force` should only be used when you explicitly intend to skip that safety check).

Let me know if you'd like help defining a retention/cleanup step or restoring from one of these snapshots.
