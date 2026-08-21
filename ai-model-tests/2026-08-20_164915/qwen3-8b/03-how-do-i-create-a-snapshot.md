# Test

- **Model:** qwen3:8b
- **Question:** How do I create a snapshot?
- **Elapsed time:** 13.386 seconds

## Response

To create a snapshot using **eskit**, follow these steps:

### ✅ Command Syntax
```bash
eskit snapshot create --name <archive_name> [optional_flags]
```

### 📌 Required Parameters
- `--name <archive_name>`:  
  Specify the name of the archive (snapshot).  
  **Example**: `--name my_snapshot`

### 📌 Optional Flags
- `--flat`:  
  Output data in a flat structure (no nested dictionaries).  
  **Example**: `--flat`

- `-v, --verbose`:  
  Enable verbose logging for detailed output.

- `-d, --debug`:  
  Enable debug logging for troubleshooting.

- `-j, --json`:  
  Output results in JSON format.

- `-c, --config <path>`:  
  Use a custom config file (default: `.eskit/config.json`).

- `--host <host_url>`:  
  Specify the Elasticsearch host (optional if already set in `.current_host`).

### 📝 Example
```bash
eskit snapshot create --name daily_backup --flat -v
```
This command creates a snapshot named `daily_backup` with flat output and verbose logging.

### 📌 Notes
- Ensure Elasticsearch is running and accessible.
- Snapshots require proper permissions and storage space.
- Use `--help` for additional options or details. 

Let me know if you need further assistance!
