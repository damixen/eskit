# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How can I see repository cache in eskit?
- **Elapsed time:** 4.093 seconds

# Response

# Usage ---
- **Input tokens:**  7594
- **Output tokens:** 266
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008924

To see repository cache in ESKit, use the **`eskit cat`** command with the `repo` kind:

```bash
eskit cat repo
```

This command displays cached information about repositories. 

You can enhance this command with optional arguments:

- **`--config`** or **`-c`**: Specify a custom config file (default: `.eskit/config.json`)
- **`--host`**: Target a specific host
- **`--view`**: Apply a named view defined in your config
- **`--fields`**: Retrieve specific fields from the data
- **`--flat`**: Flatten the output structure
- **`--json`** or **`-j`**: Output in JSON format
- **`--verbose`** or **`-v`**: Enable verbose logging
- **`--debug`** or **`-d`**: Enable debug logging

**Example with JSON output:**
```bash
eskit cat repo --json
```

**Note:** Before viewing the repository cache, you may need to pull repository data from your current host using:
```bash
eskit pull es
```

This ensures the cache is populated with the latest repository information.
