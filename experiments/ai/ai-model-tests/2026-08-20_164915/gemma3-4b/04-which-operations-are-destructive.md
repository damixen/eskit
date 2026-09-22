# Test

- **Model:** gemma3:4b
- **Question:** Which operations are destructive?
- **Elapsed time:** 4.524 seconds

## Response

Based on the provided JSON data, here's a breakdown of the operations that are considered destructive:

*   **`ilm` commands:**
    *   The `show` command, when used with the `name` argument, effectively *deletes* the archive with that name.  It retrieves and displays information about the archive, but the core operation of deleting is initiated through this command.

*   **`ai` commands:**
    *   While the `ai` commands themselves don't directly delete anything, they interact with external AI models that can perform destructive actions based on the questions posed. (e.g. generating malicious code, etc.)

**Important Note:**

The `metadata` section within each command's definition indicates the "risk" level as "read." This primarily signifies that the operation is designed to read data, not modify or delete it directly. However, the actions taken *through* those commands (especially the `ilm` command) can lead to deletions.

Do you want me to elaborate on a specific operation or provide more detail about a particular command's potential for destructive actions?
