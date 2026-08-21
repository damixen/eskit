model: claude-haiku-4-5-20251001

--- Usage ---
Input tokens:  25595
Output tokens: 291
Estimated cost with model:claude-haiku-4-5-20251001: $0.027050

# ESKit Overview

ESKit is a **lightweight Elasticsearch toolkit** for managing:

- **Repositories** - snapshot storage locations
- **Snapshots** - backups of your Elasticsearch indices
- **Indices** - individual Elasticsearch indexes

## Key Features

ESKit provides a command-line interface to help you:

- **Manage repositories** - create, view, and delete snapshot repositories
- **Handle snapshots** - create, restore, and delete snapshots with options for selective index inclusion
- **Manage indices** - create, delete, and monitor indices
- **Work with ILM** (Index Lifecycle Management) - manage index lifecycle policies
- **Archive data** - pull, sync, and push data to/from local and remote locations
- **Reindex data** - move data between indices with optional mapping changes
- **Monitor tasks** - track Elasticsearch operations in progress
- **Manage multiple hosts** - switch between different Elasticsearch instances

## Common Use Cases

- **Backup and restore** Elasticsearch data via snapshots
- **Migrate data** between Elasticsearch clusters
- **Archive** and manage large datasets
- **Automate** index and repository management tasks

ESKit abstracts away the complexity of Elasticsearch API calls with intuitive command-line commands and caching for efficient operations.
