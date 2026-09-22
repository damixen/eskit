# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Can I delete a snapshot without confirmation?
- **Elapsed time:** 3.639 seconds

# Response

# Usage ---
- **Input tokens:**  11077
- **Output tokens:** 195
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.012052

No, you cannot delete a snapshot without confirmation. According to the ESKit command specification, the `eskit snap delete` command has **destructive** risk metadata that requires explicit user confirmation before execution.

The command includes a `--force` flag, but this is specifically described as:
> "Administrative override for safety checks. Use only when the user explicitly requests --force. Do not use it as a substitute for user confirmation."

This means the `--force` flag is **not** meant to bypass the confirmation requirement. Instead, it's an administrative override that should only be used when you have explicit confirmation from the user that they want to proceed with the deletion.

**The command syntax is:**
```
eskit snap delete <repo>/<snapshot> [--force]
```

In practice, ESKit will prompt you to confirm the deletion before actually deleting the snapshot, helping to prevent accidental data loss.
