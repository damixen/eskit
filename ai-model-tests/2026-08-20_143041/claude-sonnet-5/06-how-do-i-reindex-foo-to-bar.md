model: claude-sonnet-5

--- Usage ---
Input tokens:  29617
Output tokens: 400
Estimated cost with model:claude-sonnet-5: $0.063234

To reindex data from one index to another, use the `eskit reindex` command with the source and destination index names as positional arguments.

**Command:**
```
eskit reindex foo bar
```

**Details:**
- `src` (required): Source index — supports comma-separated lists or `*` wildcards.
- `dst` (required): Destination index.

**Useful options:**
- `-m, --mapping <name>` — Apply a named mapping from your config to the destination index.
- `-dry, --dry-run` — Preview the request/command without executing it (recommended first, since this is a **write** operation).
- `--push` — Required to confirm execution if the target host is push-protected.
- `--host <host>` — Specify a host if not using the current default.
- `-c, --config <path>` — Use a custom config file (defaults to `.eskit/config.json`).

**Example with dry-run first (recommended):**
```
eskit reindex foo bar --dry-run
```
Then run for real:
```
eskit reindex foo bar
```

Note: This is a **write** operation — it will create/populate the `bar` index based on data from `foo`. It does not delete the source index `foo`.
