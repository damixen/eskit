--- Test ---
Model: qwen3:14b
Question: Which operations are destructive?
Elapsed time: 57.234 seconds

--- Response ---
model: qwen3:14b
Based on the provided tool structure, **destructive operations** (those that modify or delete data) are indicated by the `metadata.risk` field set to `"write"`. Here are the destructive operations identified:

---

### **1. `archive delete`**
- **Command**: `eskit archive delete`
- **Description**: Deletes an archive.
- **Risk**: `"write"` (destructive).
- **Key Argument**: `name` (required, specifies the archive name to delete).

---

### **2. `ilm delete`**
- **Command**: `eskit ilm delete`
- **Description**: Deletes an index lifecycle management (ILM) policy.
- **Risk**: `"write"` (destructive).
- **Key Argument**: `name` (required, specifies the ILM policy name to delete).

---

### **Why These Are Destructive**
- **Data Loss**: Both commands permanently remove resources (archives or ILM policies), which cannot be recovered without backups.
- **Risk Label**: The `"write"` risk flag explicitly indicates destructive behavior in the tool's metadata.

---

### **Non-Destructive Operations**
Commands with `metadata.risk` set to `"read"` (e.g., `show`, `list`, `get`) are safe and only retrieve data. For example:
- `eskit archive show` (views archive details).
- `eskit ilm show` (views ILM policies).

Always confirm destructive operations with backups or dry-run options if available.
