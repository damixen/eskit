# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I transfer an archive to another host?
- **Elapsed time:** 4.351 seconds

# Response

# Usage ---
- **Input tokens:**  7594
- **Output tokens:** 281
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.008999

To transfer an archive to another host, use the **`eskit archive push`** command.

## Command

```bash
eskit archive push <name> --dst <destination>
```

## Arguments

- **`<name>`** (required): Name of the archive to push
- **`--dst`** (required): Destination host in the format `<eskit_host>:<path>`
  - Example: `Host1:/home/user/data`

## Optional Flags

- **`--contents`**: Copy the contents of the archive directory into the destination (equivalent to using a trailing `/` on the rsync source path)
- **`--preview`**: Execute internal commands (like rsync) in dry-run mode to see what would be transferred
- **`--dry-run`**: Show only the request/command without executing it

## Example

```bash
eskit archive push my-archive --dst RemoteHost:/backup/archives
```

## Notes

- This command uses **mirroring**, which means it will sync and overwrite files at the destination to match the source
- The operation is marked as **destructive**, so use caution
- Use `--preview` first if you want to see what would be transferred before actually executing the push
