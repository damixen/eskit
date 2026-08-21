# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25597
- **Output tokens:** 343
- **Estimated cost:** $0.027312

## Response

# Creating an Index

To create an index in ESKit, use the **`eskit index create`** command.

## Basic Command

```bash
eskit index create <index_name>
```

Replace `<index_name>` with the name of the index you want to create.

## Example

```bash
eskit index create my-index
```

## With a Mapping

You can optionally apply a mapping from your config when creating the index:

```bash
eskit index create my-index -m my-mapping
```

Where `-m` or `--mapping` specifies the name of a mapping defined in your ESKit config file.

## Common Options

- **`--host <host>`** — Specify which host to operate on (optional if you have a current host set)
- **`-c, --config <path>`** — Path to config file (defaults to `.eskit/config.json`)
- **`--dry-run`** — Preview the request without executing it
- **`--push`** — Confirm execution on push-protected hosts
- **`-v, --verbose`** — Enable verbose logging
- **`-j, --json`** — Output in JSON format

## Example with Options

```bash
eskit index create my-index -m my-mapping --host production --dry-run
```

This command creates an index named `my-index` with the `my-mapping` mapping on the `production` host, but only shows what would be executed without actually performing it.
