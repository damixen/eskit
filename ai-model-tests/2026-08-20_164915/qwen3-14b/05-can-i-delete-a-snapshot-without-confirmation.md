--- Test ---
Model: qwen3:14b
Question: Can I delete a snapshot without confirmation?
Elapsed time: 33.113 seconds

--- Response ---
model: qwen3:14b
Yes, you can delete a snapshot without confirmation by using the `--force` flag. 

**Example command:**
```bash
eskit snapshot delete <snapshot_name> --force
```

This will delete the specified snapshot immediately without prompting for confirmation. 

---

### Key Details from the CLI Structure:
- **Command:** `eskit snapshot delete`
- **Flag:** `--force` (deletes without confirmation)
- **Required Arguments:** 
  - `<snapshot_name>` (name of the snapshot to delete)
- **Optional Flags:**
  - `--config` (specify a config file, default: `.eskit/config.json`)
  - `--host` (specify a host, optional if `.current_host` exists)
  - `-v`, `--verbose`, `-d`, `--debug`, `-j`, `--json` (logging/formatting options)
