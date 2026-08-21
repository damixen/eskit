model: claude-sonnet-4-6

--- Usage ---
Input tokens:  25595
Output tokens: 329
Estimated cost with model:claude-sonnet-4-6: $0.081720

# What is ESKit?

ESKit is a **light-weight Elasticsearch toolkit** designed for managing:

- **Repositories** – Create, show, and delete Elasticsearch snapshot repositories.
- **Snapshots** – Create, delete, restore, and view snapshots.
- **Indices** – Create, delete, show, and check recovery status of indices.
- **ILM (Index Lifecycle Management)** – View lifecycle management policies.
- **Archives** – Pull, push, sync, and manage data archives.
- **Hosts** – Manage and switch between multiple Elasticsearch host configurations.

## Key Features

- **Cache-based workflow** – Use `eskit pull` to fetch resource data from a host into a local cache, then inspect it with `eskit cat`.
- **Multi-host support** – Configure multiple hosts and switch between them easily with `eskit host set`.
- **Safety controls** – Destructive operations (like deleting indices or snapshots) require explicit confirmation, and a `--dry-run` option lets you preview commands before executing them.
- **Flexible output** – Most commands support JSON output (`-j`) and custom field/view filtering.
- **AI assistant** – An `eskit ai` command allows you to ask questions using an LLM model.

## Getting Started

Initialize ESKit with:
```
eskit init
```
Or try it out with demo data:
```
eskit init --demo
```
