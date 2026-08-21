--- Test ---
Model: qwen3:8b
Question: Which operations are destructive?
Elapsed time: 9.572 seconds

--- Response ---
model: qwen3:8b
The destructive operation in the provided tool is:

**`delete`** (under the `archive` command)

### Explanation:
- The `delete` command has a `risk`: `"delete"` in its metadata, indicating it is a destructive operation.
- Other commands like `show`, `archive`, and `ilm show` have `risk`: `"read"`, which are non-destructive.

### Summary:
- **Destructive**: `delete` (removes data)
- **Non-destructive**: `show`, `archive`, `ilm show` (read-only operations)
