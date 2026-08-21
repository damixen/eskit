model: claude-haiku-4-5-20251001

--- Usage ---
Input tokens:  25597
Output tokens: 381
Estimated cost with model:claude-haiku-4-5-20251001: $0.027502

# Creating a Snapshot

To create a snapshot in ESKit, use the `eskit snap create` command.

## Basic Command

```bash
eskit snap create <repo>/<snapshot>
```

## Required Arguments

- **`<repo>/<snapshot>`** - The snapshot name in the format `repository_name/snapshot_name`

## Common Options

- **`--index`** - Specify which indices to include in the snapshot (supports wildcards like `*` and comma-separated values)
- **`--wait`** - Wait for the snapshot creation to complete before the command returns
- **`--dry-run`** - Preview the operation without executing it
- **`--push`** - Confirm execution on push-protected hosts

## Example

```bash
# Create a snapshot named "backup-001" in the "my-repo" repository
eskit snap create my-repo/backup-001

# Create a snapshot with specific indices
eskit snap create my-repo/backup-001 --index logs-*,metrics-*

# Create a snapshot and wait for completion
eskit snap create my-repo/backup-001 --index '*' --wait

# Preview the snapshot creation command
eskit snap create my-repo/backup-001 --dry-run
```

## Additional Options

You can also specify:
- `--include_global_state` - Include global cluster state in the snapshot
- `--ignore_unavailable` - Ignore unavailable indices (default: true)
- `-c, --config` - Path to config file
- `--host` - Target host (if not set in `.current_host`)
- `-v, --verbose` - Enable verbose logging
