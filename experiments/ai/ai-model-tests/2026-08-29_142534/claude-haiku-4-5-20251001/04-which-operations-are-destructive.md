# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** Which operations are destructive?
- **Elapsed time:** 4.214 seconds

# Response

# Usage ---
- **Input tokens:**  11075
- **Output tokens:** 274
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.012445

Based on the ESKit command description, the following operations are marked as **destructive**:

1. **`eskit repo delete`** - Delete repository
   - Requires explicit user confirmation before execution
   - Has a `--force` flag for administrative override

2. **`eskit snap delete`** - Delete a snapshot
   - Requires explicit user confirmation before execution
   - Has a `--force` flag for administrative override

3. **`eskit index delete`** - Delete an index
   - Requires explicit user confirmation before execution
   - Has a `--force` flag for administrative override

4. **`eskit archive sync`** - Sync with a source host with mirroring
   - This operation mirrors/overwrites the destination with source data, so it's destructive to the destination

These operations are flagged as destructive because they either:
- **Delete data permanently** (repo delete, snap delete, index delete), or
- **Overwrite/mirror data** (archive sync), which can result in loss of existing data at the destination

All of these operations include safety mechanisms - they require explicit user confirmation before execution, and some include a `--force` flag that should only be used when the user explicitly requests it.
