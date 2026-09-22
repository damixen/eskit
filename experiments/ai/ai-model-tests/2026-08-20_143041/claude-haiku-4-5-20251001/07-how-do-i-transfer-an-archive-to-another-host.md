# Test

- **Model:** claude-haiku-4-5-20251001
- **Input tokens:** 25600
- **Output tokens:** 348
- **Estimated cost:** $0.027340

## Response

# Transferring an Archive to Another Host

To transfer an archive to another host, use the **`eskit archive push`** command, which syncs your local archive to a destination host with mirroring.

## Basic Command

```bash
eskit archive push <name> --dst <destination>
```

## Parameters

- **`<name>`** (required): Name of the archive to push
- **`--dst`** (required): Destination host in the format `<eskit_host>:<path>`
  - Example: `Host1:/home/user/data`

## Common Options

| Option | Description |
|--------|-------------|
| `--contents` | Copy the contents of the archive directory into the destination (equivalent to trailing `/` in rsync) |
| `--preview` | Execute internal commands like rsync with dry-run mode to see what would be transferred |
| `--dry-run` | Show the command without executing it |
| `--push` | Required to confirm execution on push-protected hosts |
| `-v, --verbose` | Enable verbose logging |

## Example

```bash
eskit archive push my-archive --dst Host1:/home/user/backups
```

To preview the transfer first:
```bash
eskit archive push my-archive --dst Host1:/home/user/backups --preview
```

**Note:** This is a **destructive operation** - the destination will be mirrored to match the source, meaning files in the destination that don't exist in the source will be deleted.
