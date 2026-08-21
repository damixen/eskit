# Test

- **Model:** claude-sonnet-5
- **Input tokens:** 29612
- **Output tokens:** 468
- **Estimated cost:** $0.063904

## Response

To create an index in ESKit, use the `eskit index create` command.

## Command

```
eskit index create <index> [options]
```

### Required argument
- `<index>` — Name of the index to create.

### Common optional flags
| Flag | Description |
|------|--------------|
| `-m, --mapping <name>` | Apply a mapping defined in the config to the new index. |
| `-dry, --dry-run` | Show the request/command that would be executed, without actually creating the index. |
| `--push` | Confirm execution on a push-protected host (required if the target host is protected). |
| `-c, --config <path>` | Specify a config file (default: `.eskit/config.json`). |
| `--host <name>` | Specify which host to operate on (default: current host). |
| `-v, --verbose` / `-d, --debug` | Enable verbose/debug logging. |
| `-j, --json` | Output result in JSON format. |

## Example

Create an index named `my-index` using a mapping called `logs-mapping`:

```
eskit index create my-index --mapping logs-mapping
```

Preview the request first (recommended before running against production):

```
eskit index create my-index --mapping logs-mapping --dry-run
```

**Note:** This is a **write** operation (risk: `write`), meaning it will modify the cluster state by creating a new index. If the target host is push-protected, you'll need to add `--push` to confirm the change.
