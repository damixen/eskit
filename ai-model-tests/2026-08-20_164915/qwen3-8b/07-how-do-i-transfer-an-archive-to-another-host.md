# Test

- **Model:** qwen3:8b
- **Question:** How do I transfer an archive to another host?
- **Elapsed time:** 37.111 seconds

## Response

To transfer an archive to another host using `eskit`, follow these steps:

### ✅ Command Syntax
```bash
eskit archive transfer --host <target_host> --name <archive_name>
```

### 📌 Parameters
- `--host <target_host>`: Specify the target host (required unless already set in `.current_host`).
- `--name <archive_name>`: Name of the archive to transfer (required).
- Optional flags: Use `-v`, `-d`, or `-j` for verbose/debug logging or JSON output.

### 📝 Example
```bash
eskit archive transfer --host eshost-2.example.com --name my_archive
```

### 📌 Notes
- If the host is already defined in `.current_host`, you may omit `--host`.
- Ensure the archive exists and the target host is accessible.
