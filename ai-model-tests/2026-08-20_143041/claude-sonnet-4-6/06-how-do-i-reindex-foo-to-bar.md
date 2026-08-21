# Test

- **Model:** claude-sonnet-4-6
- **Input tokens:** 25599
- **Output tokens:** 218
- **Estimated cost:** $0.080067

## Response

The `eskit reindex` command copies data from a source index to a destination index.

Here is the command to reindex `foo` to `bar`:

```
eskit reindex foo bar
```

**Optional flags you might find useful:**

- `--dry-run` — Preview the operation without executing it:
  ```
  eskit reindex --dry-run foo bar
  ```
- `--mapping <name>` — Apply a mapping from your config during reindex:
  ```
  eskit reindex --mapping my_mapping foo bar
  ```
- `--host <name>` — Target a specific host if not already set:
  ```
  eskit reindex --host my_host foo bar
  ```

> **Note:** `reindex` is a **write** operation — it will modify resources on the target host. If your host is push-protected, you will also need to add the `--push` flag to confirm the operation.
