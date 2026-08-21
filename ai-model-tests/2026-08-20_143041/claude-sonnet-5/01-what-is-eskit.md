model: claude-sonnet-5

--- Usage ---
Input tokens:  29612
Output tokens: 583
Estimated cost with model:claude-sonnet-5: $0.065054

ESKit is a light-weight command-line toolkit for managing Elasticsearch resources. Based on its command structure, it's designed to help with:

- **Repositories** (`eskit repo`) – create, show, and delete Elasticsearch snapshot repositories.
- **Snapshots** (`eskit snap`) – create, restore, show, and delete snapshots.
- **Indices** (`eskit index`) – create, show, delete indices, and check recovery status.
- **Reindexing** (`eskit reindex`) – copy data from one index to another.
- **ILM** (`eskit ilm`) – view Index Lifecycle Management policies.
- **Archives** (`eskit archive`) – sync/pull/push data archives between hosts (using rsync-like mirroring).
- **Hosts** (`eskit host`) – manage and switch between configured Elasticsearch host connections.
- **Caching** (`eskit pull`, `eskit cat`) – pull resource metadata into a local cache and inspect it offline.
- **Jobs & Tasks** (`eskit job`, `eskit task`) – track long-running operations and Elasticsearch tasks.
- **Status** (`eskit status`) – get an overview of the current ESKit state.
- **AI helper** (`eskit ai`) – ask natural language questions to get help with ESKit usage.

To get started, you typically run:

```
eskit init
```

This initializes ESKit's local configuration (optionally with `--demo` to load a demo dataset). From there, you can set up a host with `eskit host set <host>` and begin managing your Elasticsearch repositories, snapshots, and indices.

Would you like a walkthrough of a specific workflow, like creating a snapshot or setting up a repository?
