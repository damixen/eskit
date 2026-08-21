# Test

- **Model:** claude-sonnet-4-6
- **Input tokens:** 25600
- **Output tokens:** 336
- **Estimated cost:** $0.081840

## Response

## Transferring an Archive to Another Host

Use the **`eskit archive push`** command to sync an archive to a destination host with mirroring.

```bash
eskit archive push <archive-name> --dst <destination>
```

### Examples

**Push to a remote ESKit host with a specific path:**
```bash
eskit archive push my-archive --dst Host1:/home/user/data
```

**Push to a local path:**
```bash
eskit archive push my-archive --dst /mnt/backup/data
```

### Useful Options

| Option | Description |
|---|---|
| `--dst` | **(Required)** Destination. Can be `<eskit_host>:<path>` for a remote host or a plain path. |
| `--contents` | Copy the **contents** of the archive directory into the destination (like a trailing `/` in rsync). |
| `--preview` | Run internal commands (e.g. rsync) in dry-run mode to see what would happen without making changes. |
| `--dry-run` / `-dry` | Show the request/command without executing it. |
| `--push` | Required if the target host is push-protected, to confirm the write operation. |

### Notes
- This command uses **mirroring**, so the destination will be synchronized to match the source archive.
- Use `--preview` first if you want to verify what will be transferred before committing.
