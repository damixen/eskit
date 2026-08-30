# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I create an index?
- **Elapsed time:** 3.909 seconds

# Response

# Usage ---
- **Input tokens:**  7591
- **Output tokens:** 298
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.009081

# Creating an Index

To create an index in ESKit, use the `eskit index create` command.

## Command Syntax

```bash
eskit index create <index> [options]
```

## Required Arguments

- `<index>` - Name of the index to create

## Optional Arguments

- `-m, --mapping <mapping>` - Name of a mapping defined in your config to apply to the index

## Common Options

- `--config <path>` - Path to config file (default: `.eskit/config.json`)
- `--host <host>` - Specify which host to operate on
- `--dry-run` - Preview the command without executing it
- `-v, --verbose` - Enable verbose logging
- `-d, --debug` - Enable debug logging
- `-j, --json` - Output in JSON format

## Examples

**Create a simple index:**
```bash
eskit index create my-index
```

**Create an index with a specific mapping:**
```bash
eskit index create my-index --mapping my-mapping
```

**Preview the creation without executing:**
```bash
eskit index create my-index --dry-run
```

**Create on a specific host with verbose output:**
```bash
eskit index create my-index --host myhost -v
```
