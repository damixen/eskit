model: claude-sonnet-5

--- Usage ---
Input tokens:  29618
Output tokens: 678
Estimated cost with model:claude-sonnet-5: $0.066016

To transfer an archive to another host, use the **`eskit archive push`** command. This syncs (mirrors) the local archive data to a destination host.

**Command syntax:**
```
eskit archive push <name> --dst <destination>
```

**Key arguments:**
- `name` (required) – Name of the archive to push.
- `--dst` (required) – Destination target. Use `<eskit_host>:<path>` to target a remote host, e.g. `Host1:/home/user/data`.
- `--contents` (optional) – Copies only the *contents* of the archive directory into the destination (like a trailing `/` in rsync), rather than the archive folder itself.
- `--preview` (optional) – Runs the underlying sync command (e.g. rsync) in dry-run mode so you can see what would happen without actually transferring anything.
- `-dry` / `--dry-run` (optional) – Shows the request/command that would be executed without running it.
- `--push` (optional) – Confirms execution if the target host is push-protected.

**Example:**
```
eskit archive push my_archive --dst Host1:/data/archives --contents
```

**Note on safety:** This command is marked as a **write** operation because it can overwrite/modify data at the destination host through mirroring. If you're unsure about the effect, run it first with `--preview` or `--dry-run` to review what will be synced before actually performing the transfer.
