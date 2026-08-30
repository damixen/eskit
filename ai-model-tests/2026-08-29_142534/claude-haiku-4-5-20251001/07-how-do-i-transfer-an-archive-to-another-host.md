# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How do I transfer an archive to another host?
- **Elapsed time:** 4.756 seconds

# Response

# Usage ---
- **Input tokens:**  11079
- **Output tokens:** 346
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.012809

To transfer an archive to another host, you would use the **`eskit archive push`** command. Here's how it works:

## Command Overview

**`eskit archive push`** syncs an archive with a destination host using mirroring.

## Basic Syntax

```bash
eskit archive push <name> --dst <destination>
```

## Parameters

- **`<name>`** (required): The name of the archive you want to transfer
- **`--dst <destination>`** (required): The destination host and path in the format `<eskit_host>:<path>`
  - Example: `Host1:/home/user/data`

## Useful Options

- **`--contents`**: Copy the contents of the archive directory into the destination (equivalent to using a trailing `/` on rsync source)
- **`--preview`**: Execute in dry-run mode to see what would be transferred without actually doing it
- **`--dry-run`**: Shows the command without executing it

## Example

```bash
# Transfer archive named "my_archive" to Host1
eskit archive push my_archive --dst Host1:/backups/data

# Preview what would be transferred
eskit archive push my_archive --dst Host1:/backups/data --preview

# Transfer just the contents
eskit archive push my_archive --dst Host1:/backups/data --contents
```

This command uses rsync under the hood with mirroring, so it's efficient for incremental transfers and keeps the destination synchronized with the source archive.
