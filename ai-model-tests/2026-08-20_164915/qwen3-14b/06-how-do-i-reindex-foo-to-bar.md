--- Test ---
Model: qwen3:14b
Question: How do I reindex foo to bar?
Elapsed time: 37.199 seconds

--- Response ---
model: qwen3:14b
To reindex from `foo` to `bar`, use the following command:

```bash
eskit reindex --source foo --destination bar
```

### Explanation:
- `--source foo`: Specifies the source index (`foo`) from which data will be reindexed.
- `--destination bar`: Specifies the destination index (`bar`) where data will be copied.

This command is part of the `eskit reindex` subcommand, which is designed for reindexing data between indices. Ensure you have the correct permissions and verify the indices exist before running this operation.
