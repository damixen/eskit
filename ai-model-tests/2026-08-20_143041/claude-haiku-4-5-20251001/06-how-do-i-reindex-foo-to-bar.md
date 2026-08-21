# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25599
- **Output tokens:** 284
- **Estimated cost:** $0.027019

## Response

To reindex from index `foo` to index `bar`, use the `eskit reindex` command:

```bash
eskit reindex foo bar
```

This command will reindex all documents from the source index `foo` to the destination index `bar`.

**Additional options you can use:**

- `--mapping <name>` - Apply a specific mapping defined in your config when reindexing
- `--host <host>` - Specify which host to operate on (optional if set in `.current_host`)
- `-c, --config <file>` - Use a different config file (default: `.eskit/config.json`)
- `--dry-run` - Preview the operation without executing it
- `--push` - Confirm execution on a push-protected host
- `-v, --verbose` - Enable verbose logging
- `-j, --json` - Output results in JSON format

**Example with a mapping:**
```bash
eskit reindex foo bar --mapping my_mapping
```

**Example to preview first:**
```bash
eskit reindex foo bar --dry-run
```

Note: The source index `foo` can also use wildcards or multiple indices separated by commas if you need to reindex multiple sources to a single destination.
