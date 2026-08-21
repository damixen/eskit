model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25596
Output tokens: 293
Estimated cost with model:claude-sonnet-4-6: $0.081183

Based on the ESKit command description, the following operations are marked as **destructive**:

| Command | Description |
|---|---|
| `eskit repo delete` | Delete a repository |
| `eskit snap delete` | Delete a snapshot |
| `eskit index delete` | Delete an index |
| `eskit archive sync` | Sync with a source host with mirroring |

---

### ⚠️ Important Safety Notes

All destructive commands share these characteristics:

- **Confirmation required** — For `repo delete`, `snap delete`, and `index delete`, the metadata explicitly states: *"The user must explicitly confirm the action before execution."*
- **`--force` flag** — `repo delete`, `snap delete`, and `index delete` support a `--force` flag, which is described as an *"administrative override for safety checks"* and should only be used when explicitly requested.
- **`--dry-run` option** — Most of these commands support `-dry` / `--dry-run` to preview the operation without executing it — useful for verifying intent before committing.
- **`--push` flag** — Required to confirm execution on push-protected hosts.

It is strongly recommended to use `--dry-run` first when working with any of these commands.
