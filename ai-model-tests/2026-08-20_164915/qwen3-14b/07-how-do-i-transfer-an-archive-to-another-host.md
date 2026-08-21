--- Test ---
Model: qwen3:14b
Question: How do I transfer an archive to another host?
Elapsed time: 58.897 seconds

--- Response ---
model: qwen3:14b
To transfer an archive to another host, use the `eskit archive move` command. This command requires specifying the target host and the archive name. Here's how to use it:

### Syntax
```bash
eskit archive move --host <target_host> <archive_name>
```

### Example
```bash
eskit archive move --host "https://new-host.example.com" "my_archive"
```

### Key Parameters
- `--host`: The URL of the target host where the archive will be moved. **Required**.
- `<archive_name>`: The name of the archive to transfer. **Required**.

### Optional Parameters
- `--config`: Specify a custom config file (default: `.eskit/config.json`).
- `--verbose` / `--debug`: Enable verbose or debug logging.
- `--json`: Output results in JSON format.

Ensure the target host is correctly configured in your `.eskit/config.json` file, or use the `--host` flag directly in the command.
