--- Test ---
Model: qwen3:14b
Question: How do I create an repository?
Elapsed time: 66.932 seconds

--- Response ---
model: qwen3:14b
To create a repository using the `eskit` CLI, you can use the `repository create` command. Here's how:

### Syntax:
```bash
eskit repository create --name <repository-name> --type <repository-type> --settings '{"host": "your-host", "port": your-port}'
```

### Parameters:
- `--name`: **Required**. The name of the repository (e.g., `my-repo`).
- `--type`: **Required**. The repository type (e.g., `fs` for file system, `s3` for Amazon S3, etc.).
- `--settings`: **Required**. A JSON string containing configuration details. For example:
  ```json
  {"host": "localhost", "port": 9200}
  ```

### Example:
```bash
eskit repository create --name my-backup-repo --type fs --settings '{"host": "localhost", "port": 9200}'
```

### Notes:
- Replace `<repository-name>`, `<repository-type>`, and the JSON settings with your desired values.
- Ensure the JSON format is valid (use quotes and commas correctly).
- The `type` can vary based on your Elasticsearch setup (e.g., `fs`, `s3`, `gcs`, etc.).

Let me know if you need help with specific repository types or configurations!
