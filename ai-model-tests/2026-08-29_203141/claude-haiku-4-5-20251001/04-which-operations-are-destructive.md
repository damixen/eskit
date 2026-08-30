# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Which operations are destructive?
- **Elapsed time:** 4.664 seconds

# Response

# Usage ---
- **Input tokens:**  7590
- **Output tokens:** 318
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.009180

# Destructive Operations in ESKit

The following operations are marked as **destructive** and require explicit user confirmation before execution:

## 1. **Repository Deletion**
```
eskit repo delete <name> [--force]
```
Deletes a repository. The `--force` flag is an administrative override, but user confirmation is still required.

## 2. **Snapshot Deletion**
```
eskit snap delete <name> [--force]
```
Deletes a snapshot. Like repo deletion, `--force` overrides safety checks but requires user confirmation.

## 3. **Index Deletion**
```
eskit index delete <index> [--force]
```
Deletes an index. The `--force` flag bypasses safety checks but user confirmation is mandatory.

## 4. **Archive Sync**
```
eskit archive sync <name> [--contents] [--preview]
```
Syncs with a source host using mirroring, which can overwrite local data.

---

## Important Safety Notes

- **All destructive operations require explicit user confirmation** before they execute
- The `--force` flag is an **administrative override for safety checks only** — it does not replace the need for user confirmation
- Use `--dry-run` to preview what would happen without actually executing the operation
- Use `--preview` with archive commands to see the changes that would be made
