# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Can I delete a snapshot without confirmation?
- **Elapsed time:** 3.314 seconds

# Response

# Usage ---
- **Input tokens:**  7592
- **Output tokens:** 148
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008332

No, you cannot delete a snapshot without confirmation. 

The `eskit snap delete` command has **destructive** risk level, which means **the user must explicitly confirm the action before execution**.

Here's the command structure:

```bash
eskit snap delete <repo>/<snapshot> [--force] [options]
```

While there is a `--force` flag available, it is explicitly designed as an "administrative override for safety checks" and **should only be used when the user explicitly requests it** — not as a substitute for user confirmation.

In practice, ESKit will prompt you to confirm the deletion before proceeding, ensuring you don't accidentally delete important snapshots.
