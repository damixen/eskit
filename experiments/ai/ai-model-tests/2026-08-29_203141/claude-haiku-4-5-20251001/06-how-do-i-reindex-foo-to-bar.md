# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I reindex foo to bar?
- **Elapsed time:** 3.114 seconds

# Response

# Usage ---
- **Input tokens:**  7593
- **Output tokens:** 181
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008498

To reindex from source index `foo` to destination index `bar`, use the following command:

```bash
eskit reindex foo bar
```

This command will reindex all documents from the `foo` index to the `bar` index.

**Optional flags you can add:**

- `-m, --mapping <name>` — Apply a specific mapping from your config to the destination index
- `--dry-run` — Preview the reindex operation without executing it
- `--host <host>` — Specify which host to operate on (if not set in `.current_host`)
- `-v, --verbose` — Enable verbose logging
- `-j, --json` — Output results in JSON format

**Example with options:**
```bash
eskit reindex foo bar --dry-run -v
```
