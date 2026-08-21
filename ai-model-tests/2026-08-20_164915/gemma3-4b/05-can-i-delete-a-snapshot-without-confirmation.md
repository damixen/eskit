--- Test ---
Model: gemma3:4b
Question: Can I delete a snapshot without confirmation?
Elapsed time: 6.869 seconds

--- Response ---
model: gemma3:4b
Based on the provided documentation, deleting a snapshot without confirmation is **not supported**. 

Here's the relevant excerpt from the `ilm` command section:

```json
{
  "commands": {
    "show": {
      "arguments": [
        {
          "name": "name",
          "type": "str",
          "required": true,
          "description": "Name of the archive."
        },
        {
          "flags": [
            "-v",
            "--verbose"
          ],
          "name": "verbose",
          "type": "boolean",
          "required": false,
          "default": false,
          "description": "Enable verbose logging"
        },
        {
          "flags": [
            "-d",
            "--debug"
          ],
          "name": "debug",
          "type": "boolean",
          "required": false,
          "default": false,
          "description": "Enable debug logging"
        },
        {
          "flags": [
            "-j",
            "--json"
          ],
          "name": "json",
          "type": "boolean",
          "required": false,
          "default": false,
          "description": "Output in JSON format"
        }
      ]
    }
  }
}
```

The `name` argument is marked as `required: true`.  This implies that you *must* specify the name of the snapshot you want to delete, and there's no option to skip a confirmation prompt.

**Important:**  Always double-check the name of the snapshot you're about to delete to avoid accidental data loss.
