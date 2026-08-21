model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25597
Output tokens: 354
Estimated cost with model:claude-sonnet-4-6: $0.082101

## Creating a Snapshot

Use the `eskit snap create` command to create a snapshot. The snapshot name must follow the format `<repo>/<snapshot>`.

### Basic Command

```bash
eskit snap create <repo>/<snapshot>
```

### Common Options

| Option | Description |
|---|---|
| `--index <name>` | Specify which index (or indices) to snapshot. Supports `*` wildcards and comma-separated values. |
| `--include_global_state` | Include the global cluster state in the snapshot. |
| `--wait` | Wait for the snapshot to complete before returning. |
| `--dry-run` | Preview the request without executing it. |
| `--push` | Required if the host is push-protected. |

### Examples

**Snapshot an entire repository:**
```bash
eskit snap create my-repo/my-snapshot
```

**Snapshot a specific index:**
```bash
eskit snap create my-repo/my-snapshot --index my-index
```

**Snapshot multiple indices with a wildcard:**
```bash
eskit snap create my-repo/my-snapshot --index "logs-*"
```

**Wait for completion:**
```bash
eskit snap create my-repo/my-snapshot --index my-index --wait
```

**Preview without executing:**
```bash
eskit snap create my-repo/my-snapshot --dry-run
```

> **Note:** If your host is push-protected, you must add `--push` to confirm the operation.
