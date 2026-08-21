--- Test ---
Model: qwen3:4b
Question: Which operations are destructive?
Elapsed time: 65.523 seconds

--- Response ---
model: qwen3:4b
Based on the provided JSON structure for the `eskit` CLI tool, **no destructive operations are explicitly described**. Here's the reasoning:

### Key Observations from the JSON:
1. **Risk Level Indicates Safety**:
   - The `metadata` field for both `index` and `ilm` commands specifies `"risk": "read"`. In CLI tooling contexts, this typically means the operations are **read-only** and non-destructive (e.g., they do not modify data, delete resources, or alter system state).
   - The `ai` command has no risk metadata specified, but it involves interactive queries (e.g., answering questions), which are inherently non-destructive.

2. **Destructive Operations Are Not Present**:
   - The JSON describes only three top-level commands: `index`, `ilm`, and `ai`.
   - **No commands with destructive behavior** (e.g., `delete`, `remove`, `drop`, `purge`) are listed in the `commands` fields:
     - `index.commands` is empty (`{}`).
     - `ilm.commands` contains only `show` (a non-destructive operation).
     - `ai.commands` is empty (`{}`).
   - Destructive operations (like index deletion) would typically be part of a subcommand (e.g., `eskit index delete`), but the provided JSON does not include any such subcommands.

3. **Context of Elasticsearch (eskit's Domain)**:
   - `eskit` is an Elasticsearch CLI tool. In Elasticsearch, destructive operations (e.g., deleting indices) are common, but the provided JSON **does not describe any destructive subcommands**. This suggests the tool's current implementation focuses on **read-only operations** (as indicated by the `"risk": "read"` metadata).

### Why This Matters:
- **Destructive operations require explicit risk labeling** (e.g., `"risk": "write"` or `"risk": "delete"`). Since none of the described commands have such labels, they are not considered destructive.
- The absence of subcommands like `delete` in `index` or `ilm` further confirms that no destructive operations are defined in this JSON structure.

### Conclusion:
**There are no destructive operations described in the provided JSON**. All operations (as defined here) are non-destructive, consistent with the `"risk": "read"` metadata for `index` and `ilm`. If destructive operations were intended, they would need to be added as subcommands with appropriate risk labeling (e.g., `"risk": "delete"`).

> 💡 **Note**: In real-world usage, you might need to extend this CLI with destructive subcommands (e.g., `eskit index delete`). However, **based solely on the given JSON**, no destructive operations exist.
