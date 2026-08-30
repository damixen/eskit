# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I create an repository?
- **Elapsed time:** 4.695 seconds

# Response

# Usage ---
- **Input tokens:**  7591
- **Output tokens:** 265
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008916

To create a repository in ESKit, use the **`eskit repo create`** command.

Here's the command structure:

```bash
eskit repo create <name> --type <type> --location <location>
```

**Required arguments:**
- `<name>` - Name of the repository
- `--location <path>` - Location (path to a folder) where the repository will be created

**Optional arguments:**
- `--type <type>` - Type of repository (default: `fs` for filesystem)

**Example:**
```bash
eskit repo create my-backup --type fs --location /path/to/backup/folder
```

**Common options you can also use:**
- `--config` - Specify a custom config file
- `--host` - Specify which host to operate on
- `--dry-run` - Preview the command without executing it
- `--verbose` - Enable verbose logging
- `--debug` - Enable debug logging
- `--json` - Output in JSON format

**Note:** This is a write operation, so use `--dry-run` first if you want to preview what will happen before actually creating the repository.
