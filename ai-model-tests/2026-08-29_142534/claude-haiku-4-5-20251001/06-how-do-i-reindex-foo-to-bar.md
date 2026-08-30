# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I reindex foo to bar?
- **Elapsed time:** 3.552 seconds

# Response

# Usage ---
- **Input tokens:**  11078
- **Output tokens:** 224
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.012198

To reindex from index `foo` to index `bar`, you would use the `reindex` command with the following syntax:

```bash
eskit reindex foo bar
```

This command will reindex all documents from the source index `foo` to the destination index `bar`.

**Optional parameters you might find useful:**

- `--mapping <name>` or `-m <name>`: Apply a specific mapping configuration from your config file to the destination index
- `--dry-run`: Preview the command without actually executing it
- `--host <host>`: Specify which host to operate on (if not already set)

**Example with a mapping:**
```bash
eskit reindex foo bar --mapping my_mapping
```

**Example with dry-run to preview:**
```bash
eskit reindex foo bar --dry-run
```

The source index can also accept wildcards (e.g., `foo*`) or multiple indices separated by commas if you need to reindex from multiple sources.
