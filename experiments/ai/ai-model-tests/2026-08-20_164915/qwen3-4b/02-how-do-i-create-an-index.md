# Test

- **Model:** qwen3:4b
- **Question:** How do I create an index?
- **Elapsed time:** 42.556 seconds

## Response

Based on the provided schema for the `eskit` command-line tool, the command to create a new index is:

**`eskit index create <index-name>`**

### Explanation:
1. **`eskit index`**: The top-level command for index management.
2. **`create`**: The subcommand for creating a new index.
3. **`<index-name>`**: The required name of the index (a **positional argument**). This must be specified (e.g., `eskit index create my_index`).

### Key Details from Schema:
- The `index` command has a `commands` object containing `create` (with `risk: "write"`).
- The `create` command requires the index name as a mandatory input (consistent with Elasticsearch best practices).
- Optional flags (e.g., `--verbose`, `--config`, `--host`) can be added if needed, but the **minimal command** only requires `<index-name>`.

### Example:
```bash
# Create an index named "users"
eskit index create users
```

### Why this works:
- The schema explicitly defines `eskit index create` as the command for creating indices (with `risk: "write"` indicating it modifies data).
- The index name is treated as a **positional argument** (not a flag), matching the typical pattern in CLI tools (e.g., `eskit index show <index-name>`).

> 💡 **Note**: If you need advanced features (e.g., index mappings), use additional flags like `--mapping` (as supported by the tool's schema). For the simplest case, the above command suffices.
