# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How can I see snapshot cache in eskit?
- **Elapsed time:** 4.097 seconds

# Response

# Usage ---
- **Input tokens:**  7594
- **Output tokens:** 265
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008919

To see the snapshot cache in ESKit, use the **`eskit cat snap`** command.

This command displays cached snapshot information that has been pulled from your Elasticsearch host.

**Basic usage:**
```bash
eskit cat snap
```

**Common options you can add:**
- `--config` / `-c` - Specify a custom config file (defaults to `.eskit/config.json`)
- `--host` - Specify which host to operate on
- `--view` - Use a named view defined in your config
- `--fields` - Retrieve specific fields from the snapshot data
- `--flat` - Flatten the output structure
- `--json` / `-j` - Output results in JSON format
- `--verbose` / `-v` - Enable verbose logging
- `--debug` / `-d` - Enable debug logging

**Example with JSON output:**
```bash
eskit cat snap --json
```

**Note:** Before you can view the snapshot cache, you may need to pull the data from your Elasticsearch host using:
```bash
eskit pull es
```

This fetches the latest snapshot information from your configured Elasticsearch host into the cache.
