model: claude-sonnet-5

--- Usage ---
Input tokens:  29615
Output tokens: 748
Estimated cost with model:claude-sonnet-5: $0.066710

To create a snapshot in ESKit, use the `eskit snap create` command.

## Command
```
eskit snap create <repo>/<snapshot> [options]
```

**Required argument:**
- `name` — Must be in the form `<repo>/<snapshot>`, e.g. `my-repo/snapshot-2024-01-01`

**Useful optional flags:**
| Flag | Description |
|---|---|
| `--index` | Index (or comma-separated indices) to include in the snapshot. Supports `*` wildcards. If omitted, all indices are included. |
| `--include_global_state` | Include cluster global state in the snapshot (default: false). |
| `--ignore_unavailable` | Ignore indices that are unavailable (default: true). |
| `--wait` | Wait for the snapshot creation to complete before returning. |
| `-dry`, `--dry-run` | Show the request/command that would be executed, without actually running it. |
| `--push` | Required to confirm execution if the host is push-protected. |
| `--host` | Specify which host to target (otherwise uses current host). |
| `-c`, `--config` | Path to config file (default `.eskit/config.json`). |

## Example
Create a snapshot named `snapshot-2024-01-01` in repo `my-repo`, including only indices matching `logs-*`, and wait for completion:

```
eskit snap create my-repo/snapshot-2024-01-01 --index "logs-*" --wait
```

To just preview what would happen without executing:
```
eskit snap create my-repo/snapshot-2024-01-01 --index "logs-*" --dry-run
```

**Note:** This is a **write** operation — it will modify data in the specified repository on the Elasticsearch host. If your host is push-protected, you'll need to add `--push` to confirm the action.
