# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25598
- **Output tokens:** 241
- **Estimated cost:** $0.026803

## Response

# Deleting a Snapshot

Snapshots require explicit confirmation before deletion due to their destructive nature. The `eskit snap delete` command has safety mechanisms in place:

**Basic command:**
```bash
eskit snap delete <repo>/<snapshot>
```

**Safety features:**
- The command is marked as **destructive** in ESKit
- **User confirmation is required** before execution
- You cannot bypass this with automation — the user must explicitly confirm the action

**Available options:**
- `--dry-run` / `-dry`: Preview the deletion without executing it
- `--force`: An administrative override for safety checks, but this should only be used when the user explicitly requests `--force` — it's not a substitute for user confirmation
- `--push`: Used to confirm execution on push-protected hosts

**Example with dry-run to preview:**
```bash
eskit snap delete my-repo/my-snapshot --dry-run
```

The confirmation requirement is a safety feature to prevent accidental data loss, so snapshots cannot be silently deleted even with `--force`.
