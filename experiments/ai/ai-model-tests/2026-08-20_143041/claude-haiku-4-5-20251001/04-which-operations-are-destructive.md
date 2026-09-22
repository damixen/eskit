# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25596
- **Output tokens:** 311
- **Estimated cost:** $0.027151

## Response

# Destructive Operations in ESKit

The following operations are marked as destructive and require explicit user confirmation before execution:

## 1. **Repository Deletion**
- **Command**: `eskit repo delete <name>`
- **Risk**: Destructive
- **Requires**: User must explicitly confirm the action before execution

## 2. **Snapshot Deletion**
- **Command**: `eskit snap delete <repo>/<snapshot>`
- **Risk**: Destructive
- **Requires**: User must explicitly confirm the action before execution

## 3. **Index Deletion**
- **Command**: `eskit index delete <index>`
- **Risk**: Destructive
- **Requires**: User must explicitly confirm the action before execution

## 4. **Archive Sync** (with mirroring)
- **Command**: `eskit archive sync <name>`
- **Risk**: Destructive
- **Note**: Syncs with a source host using mirroring, which can overwrite local data

## Safety Notes

All destructive operations support:
- **`--dry-run`** or **`-dry`**: Preview the operation without executing it
- **`--force`**: Administrative override for safety checks (should only be used when explicitly requested by the user, not as a substitute for confirmation)

These protections help prevent accidental data loss when working with critical Elasticsearch resources.
