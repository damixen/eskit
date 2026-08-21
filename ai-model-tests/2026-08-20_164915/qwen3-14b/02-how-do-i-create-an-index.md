--- Test ---
Model: qwen3:14b
Question: How do I create an index?
Elapsed time: 63.972 seconds

--- Response ---
model: qwen3:14b
To create an index using `eskit`, use the following command structure:

```bash
eskit index create <name> [OPTIONS]
```

### Key Parameters:
- **`<name>`** (required): The name of the index you want to create.  
  Example: `my_index`

- **`--config`** (optional): Path to the config file (default: `.eskit/config.json`).  
  Example: `--config /path/to/custom-config.json`

- **`--host`** (optional): Specify a host if not set in `.current_host`.  
  Example: `--host http://localhost:9200`

- **Output Controls**:
  - `-v` / `--verbose`: Enable verbose logging.
  - `-d` / `--debug`: Enable debug logging.
  - `-j` / `--json`: Output results in JSON format.

---

### Example Command:
```bash
eskit index create my_index --config .eskit/config.json --host http://localhost:9200 -v
```

This creates an index named `my_index` using the specified config and host, with verbose logging enabled. Adjust parameters as needed for your environment.
