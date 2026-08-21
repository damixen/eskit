model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25598
Output tokens: 220
Estimated cost with model:claude-sonnet-4-6: $0.080094

Based on the ESKit command description, **`eskit snap delete` is marked as a destructive operation**, and its metadata explicitly states:

> *"The user must explicitly confirm the action before execution."*

So **no**, you cannot skip confirmation by default. You must explicitly confirm the action before it is executed.

However, there is a `--force` flag available, which is described as:

> *"Administrative override for safety checks. Use only when the user explicitly requests --force. Do not use it as a substitute for user confirmation."*

So while `--force` exists as an override, it is intended strictly as an administrative safety override — **not** a way to routinely bypass confirmation.

Example command with `--force` (use with caution):

```bash
eskit snap delete <repo>/<snapshot> --force
```

⚠️ **Warning:** Deleting a snapshot is irreversible. Make sure you are certain before using `--force` to bypass safety checks.
