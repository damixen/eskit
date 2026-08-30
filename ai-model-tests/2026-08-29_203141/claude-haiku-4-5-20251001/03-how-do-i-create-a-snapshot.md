# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I create a snapshot?
- **Elapsed time:** 5.302 seconds

# Response

# Usage ---
- **Input tokens:**  7591
- **Output tokens:** 428
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.009731

# Creating a Snapshot with ESKit

To create a snapshot, use the **`eskit snap create`** command.

## Basic Command

```bash
eskit snap create <repo>/<snapshot>
```

## Required Arguments
- **`<repo>/<snapshot>`** - The snapshot name in the format `repository_name/snapshot_name`

## Optional Arguments
- **`--index`** - Specify which indices to include in the snapshot. You can:
  - Use wildcards (e.g., `logs-*`)
  - Specify multiple indices separated by commas (e.g., `index1,index2`)
  - If omitted, all indices are included
  
- **`--include_global_state`** - Include global cluster state (default: false)
- **`--ignore_unavailable`** - Ignore unavailable indices (default: true)
- **`--wait`** - Wait for the snapshot creation to complete before the command returns (default: false)

## Common Options
- **`--host`** - Specify which host to operate on
- **`--dry-run`** - Preview the command without executing it
- **`-v, --verbose`** - Enable verbose logging
- **`-j, --json`** - Output in JSON format

## Examples

```bash
# Create a snapshot with all indices
eskit snap create my-repo/my-snapshot

# Create a snapshot with specific indices
eskit snap create my-repo/my-snapshot --index logs-2024-01,logs-2024-02

# Create a snapshot with wildcard pattern
eskit snap create my-repo/my-snapshot --index "logs-*"

# Create and wait for completion
eskit snap create my-repo/my-snapshot --wait

# Preview without creating
eskit snap create my-repo/my-snapshot --dry-run
```
