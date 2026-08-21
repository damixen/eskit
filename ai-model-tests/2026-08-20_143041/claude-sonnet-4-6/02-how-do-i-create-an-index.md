# Test

- **Model:** claude-sonnet-4-6
- **Input tokens:** 25597
- **Output tokens:** 356
- **Estimated cost:** $0.082131

## Response

## Creating an Index

Use the `eskit index create` command to create a new Elasticsearch index.

### Basic Command

```bash
eskit index create <index-name>
```

### Options

| Option | Description |
|--------|-------------|
| `<index-name>` | **(Required)** Name of the index to create |
| `-m, --mapping <name>` | Apply a named mapping defined in your config |
| `--host <host>` | Specify a host (optional if set in `.current_host`) |
| `-c, --config <path>` | Config file path (default: `.eskit/config.json`) |
| `-dry, --dry-run` | Preview the request without executing it |
| `--push` | Required to execute on push-protected hosts |
| `-v, --verbose` | Enable verbose logging |
| `-j, --json` | Output in JSON format |

### Examples

**Create a simple index:**
```bash
eskit index create my-index
```

**Create an index with a mapping from your config:**
```bash
eskit index create my-index --mapping my-mapping
```

**Preview the request before executing:**
```bash
eskit index create my-index --dry-run
```

**Create on a specific host:**
```bash
eskit index create my-index --host my-host
```

> **Note:** This is a **write** operation. If your target host is push-protected, you will need to add the `--push` flag to confirm execution.
