# Test

- **Model:** qwen3:14b
- **Question:** How do I create a snapshot?
- **Elapsed time:** 56.451 seconds

## Response

To create a snapshot using the `eskit` CLI, use the following command:

```bash
eskit snapshot create <snapshot-name> <repository-name> [flags]
```

### Key Parameters:
- **`<snapshot-name>`**: The name you want to assign to the snapshot.
- **`<repository-name>`**: The name of the [Elasticsearch repository](https://www.elastic.co/guide/en/elasticsearch/reference/current/snapshot-restore.html#_repositories) where the snapshot will be stored. Ensure the repository is already configured in Elasticsearch.

### Optional Flags:
- `--wait-for-completion`: Wait until the snapshot is fully created before returning control to the terminal. Omit this flag to return immediately after initiating the snapshot.

---

### Example:
```bash
eskit snapshot create my_backup my_repo --wait-for-completion
```

This command creates a snapshot named `my_backup` in the `my_repo` repository and waits for it to complete.

---

### Notes:
- Ensure the repository (`my_repo` in the example) is properly configured in Elasticsearch (e.g., via `elasticsearch.yml` and repository setup).
- You can use flags like `--config`, `--host`, or `--verbose` if needed (inherited from parent commands).
