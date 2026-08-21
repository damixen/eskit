--- Test ---
Model: qwen3:8b
Question: How do I create an index?
Elapsed time: 14.216 seconds

--- Response ---
model: qwen3:8b
To create an index using **eskit**, follow these steps:

### ✅ Command
```bash
eskit create --name <your_index_name>
```

### 📌 Required Parameter
- `--name` (or `-n`): Specify the name of the index.  
  Example:  
  ```bash
  eskit create --name my_new_index
  ```

### 🚀 Optional Flags
- `--flat`: Create a flat (non-nested) structure for the index.
- `-v`/`--verbose`: Enable verbose logging for detailed output.
- `-d`/`--debug`: Enable debug-level logging for troubleshooting.
- `-j`/`--json`: Output the result in JSON format.

### 📁 Configuration
- The tool uses a default config file at `.eskit/config.json`. If you need to specify a different config or host, use:
  ```bash
  eskit create --config /path/to/config.json --host http://localhost:9200
  ```

### 📝 Notes
- Ensure Elasticsearch is running and accessible via the specified host.
- The `--name` parameter is mandatory. Replace `<your_index_name>` with your desired index name.

Let me know if you need help with advanced settings!
