model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25599
Output tokens: 873
Estimated cost with model:claude-sonnet-4-6: $0.089892

# Multi-Step Backup Workflow with ESKit

Here's a complete backup workflow covering initialization, pulling current state, creating a repository, taking a snapshot, and verifying it.

---

## Step 1 — Initialize ESKit

Set up ESKit in your working directory (optionally with demo data):

```bash
eskit init
```

---

## Step 2 — Set Your Target Host

Set the host you want to back up:

```bash
eskit host set <your-host-name>
```

Confirm the active host:

```bash
eskit host get
```

---

## Step 3 — Pull Current State into Cache

Sync ESKit's local cache with the live Elasticsearch cluster (indexes, snapshots, repos, ILM):

```bash
eskit pull
```

Or pull only Elasticsearch data:

```bash
eskit pull es
```

---

## Step 4 — Review Indexes Before Backup

Inspect the indexes you plan to back up:

```bash
eskit cat index
```

Or check a specific index in detail:

```bash
eskit index show <index-name>
```

---

## Step 5 — Create a Snapshot Repository

Create a filesystem repository to store the snapshot:

```bash
eskit repo create <repo-name> --location /path/to/backup/dir
```

> ⚠️ **Write operation** — This registers a new repository on your Elasticsearch cluster. Ensure the path is accessible from all cluster nodes.

Verify the repository was created:

```bash
eskit repo show <repo-name>
```

---

## Step 6 — Take a Snapshot

Create a snapshot of one or more indexes:

```bash
eskit snap create <repo-name>/<snapshot-name> --index <index-name> --wait
```

- Use `--index "*"` to snapshot **all** indexes.
- Use `--wait` to block until the snapshot completes.
- Use `--dry-run` first to preview the request without executing it:

```bash
eskit snap create <repo-name>/<snapshot-name> --index <index-name> --dry-run
```

> ⚠️ **Write operation** — This creates a snapshot on the cluster.

---

## Step 7 — Verify the Snapshot

Pull the updated snapshot cache:

```bash
eskit pull es
```

Then inspect the snapshot:

```bash
eskit snap show <repo-name>/<snapshot-name>
```

Or browse all snapshots in the cache:

```bash
eskit cat snap
```

---

## Step 8 — (Optional) Archive the Snapshot Locally

If you have an archive configured, pull it to local storage:

```bash
eskit archive pull <archive-name>
```

List available archives to confirm:

```bash
eskit archive list
```

---

## Summary

| Step | Command | Risk |
|------|---------|------|
| Init | `eskit init` | None |
| Set host | `eskit host set <host>` | None |
| Pull cache | `eskit pull` | Write (local) |
| Review indexes | `eskit cat index` | Read |
| Create repo | `eskit repo create <repo> --location <path>` | Write |
| Create snapshot | `eskit snap create <repo>/<snap> --index <idx> --wait` | Write |
| Verify snapshot | `eskit snap show <repo>/<snap>` | Read |
| Archive locally | `eskit archive pull <archive>` | Write |

---

> 💡 **Tip:** Use `--dry-run` on any write operation to preview it safely before execution. Use `--push` when operating against push-protected hosts.
