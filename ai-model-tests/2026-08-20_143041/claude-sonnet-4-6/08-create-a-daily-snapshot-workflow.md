model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25596
Output tokens: 697
Estimated cost with model:claude-sonnet-4-6: $0.087243

# Daily Snapshot Workflow with ESKit

Here's a step-by-step workflow you can use to take daily snapshots with ESKit.

---

## 1. Initialize ESKit (first time only)

```bash
eskit init
```

---

## 2. Set Your Target Host

```bash
eskit host set <your-host-name>
```

Confirm it is set correctly:

```bash
eskit host get
```

---

## 3. Create a Repository (if not already done)

A snapshot requires a repository. Create one pointing to a filesystem location:

```bash
eskit repo create my-daily-repo --location /mnt/snapshots/daily
```

> ⚠️ **Note:** This is a **write** operation. If your host is push-protected, add `--push` to confirm. Use `--dry-run` to preview the request first.

---

## 4. Take a Daily Snapshot

Name your snapshot with a date for easy identification (e.g., `snap-2025-07-16`):

```bash
eskit snap create my-daily-repo/snap-2025-07-16 --index "*" --wait
```

- `--index "*"` — captures all indices.
- `--wait` — blocks until the snapshot completes before returning.

> ⚠️ **Note:** This is a **write** operation. Add `--push` if the host is push-protected.

---

## 5. Verify the Snapshot

```bash
eskit snap show my-daily-repo/snap-2025-07-16
```

Or list all snapshots in the repository via the cache:

```bash
eskit pull
eskit cat snap
```

---

## 6. Automate with a Cron Job

Add an entry to your crontab (`crontab -e`) to run the snapshot every day at 2:00 AM:

```cron
0 2 * * * eskit snap create my-daily-repo/snap-$(date +\%Y-\%m-\%d) --index "*" --wait
```

---

## Optional: Clean Up Old Snapshots

To delete an older snapshot you no longer need:

```bash
eskit snap delete my-daily-repo/snap-2025-07-01
```

> ⚠️ **`snap delete` is a destructive operation.** You must explicitly confirm the action before ESKit will execute it. Use `--dry-run` to preview first.

---

## Summary

| Step | Command |
|---|---|
| Set host | `eskit host set <host>` |
| Create repo | `eskit repo create <repo> --location <path>` |
| Take snapshot | `eskit snap create <repo>/<snap> --index "*" --wait` |
| Verify | `eskit snap show <repo>/<snap>` |
| Delete old snaps | `eskit snap delete <repo>/<snap>` |
