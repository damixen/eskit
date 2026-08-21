--- Test ---
Model: qwen3:4b
Question: Create a daily snapshot workflow.
Elapsed time: 46.229 seconds

--- Response ---
model: qwen3:4b
To create a **daily snapshot workflow** using the `eskit` CLI, you can schedule the `settings snapshot` command to run once a day (e.g., via a cron job). Here's how:

---

### ✅ Step-by-Step Workflow
1. **Identify the index** you want to snapshot (e.g., `my_index`).
2. **Create a cron job** to execute the command daily at a specific time (e.g., 2 AM).

#### Example Cron Job (Linux/macOS)
```bash
0 2 * * * eskit settings snapshot --index "my_index"
```

**Explanation**:
- `0 2 * * *`: Runs the command at **2:00 AM every day**.
- `eskit settings snapshot --index "my_index"`: Creates a daily snapshot for the specified index.

---

### 🔧 Why This Works
- The `eskit settings snapshot` command (defined in your JSON) **requires an index name** (`--index`).
- This command **writes** to Elasticsearch (as indicated by `metadata: { "risk": "write" }`), so it’s safe to schedule for daily backups.
- No additional configuration is needed—just the cron job.

---

### 📝 Notes
- Replace `my_index` with your actual index name.
- Ensure Elasticsearch is running and the index exists before scheduling.
- For advanced workflows (e.g., repository-based snapshots), you’d need to extend this with Elasticsearch’s repository configuration.

This workflow ensures **reliable daily snapshots** with minimal overhead. 🚀
