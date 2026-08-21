--- Test ---
Model: qwen3:8b
Question: Compose a multi-step backup workflow.
Elapsed time: 34.090 seconds

--- Response ---
model: qwen3:8b
Here's a multi-step backup workflow using `eskit` with explanations for each step:

---

### **1. Initialize Backup Configuration**
**Command:**  
```bash
eskit config --config backup-config.json
```
**Purpose:**  
Create a configuration file (`backup-config.json`) to store backup settings like Elasticsearch hosts, storage paths, and retention policies.

**Example config:**
```json
{
  "elasticsearch": {
    "hosts": ["http://localhost:9200"],
    "username": "backup_user",
    "password": "secure_password"
  },
  "storage": {
    "path": "/backups/eskit",
    "retention": "7d"
  }
}
```

---

### **2. Create a Backup Archive**
**Command:**  
```bash
eskit archive --config backup-config.json --name daily_backup_20231010 --flat
```
**Purpose:**  
Create a compressed archive of your Elasticsearch indices. The `--flat` flag ensures flat directory structure for easier restoration.

**Key Parameters:**
- `--name`: Unique identifier for the backup (e.g., `daily_backup_20231010`).
- `--flat`: Simplifies directory structure for backup storage.
- `--config`: Specifies the configuration file from Step 1.

**Output:**  
- A `.tar.gz` file saved to the path defined in `storage.path` (e.g., `/backups/eskit/daily_backup_20231010.tar.gz`).

---

### **3. Verify Backup Integrity**
**Command:**  
```bash
eskit archive --config backup-config.json --name daily_backup_20231010 --view backup_view --fields status
```
**Purpose:**  
Validate the backup's integrity by checking its status (e.g., success/failure) and metadata.

**Key Parameters:**
- `--view`: Specifies a predefined view in the config (e.g., `backup_view`) to filter data.
- `--fields`: Retrieves specific fields like `status` or `size`.

**Example Output:**  
```json
{
  "status": "success",
  "size": "12.3GB",
  "timestamp": "2023-10-10T14:30:00Z"
}
```

---

### **4. Automate Retention with ILM (Optional)**
**Command:**  
```bash
eskit ilm show --config backup-config.json --name daily_backup_20231010 --fields policy
```
**Purpose:**  
Check or configure an ILM (Index Lifecycle Management) policy to automate retention (e.g., delete backups older than 7 days).

**Example Policy:**  
```json
{
  "policy": {
    "phases": {
      "delete": {
        "min_age": "7d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

---

### **5. Restore from Backup (If Needed)**
**Command:**  
```bash
eskit restore --config backup-config.json --name daily_backup_20231010 --verbose
```
**Purpose:**  
Recover data from the backup archive. Use `--verbose` for detailed logs during restoration.

---

### **6. Monitor and Audit**
**Command:**  
```bash
eskit archive --config backup-config.json --name daily_backup_20231010 --fields size,timestamp
```
**Purpose:**  
Audit backup metadata (e.g., size, timestamp) to ensure consistency and track growth over time.

---

### **Flags for Customization**
- `--verbose`: Enable detailed logs for troubleshooting.
- `--debug`: For advanced debugging (e.g., network requests).
- `--json`: Output results in structured JSON format for scripting.

---

This workflow ensures reliable backups, verification, and automation, while maintaining flexibility via configuration files and optional flags. 🧠💾
