# Test

- **Model:** qwen3:14b
- **Question:** What is ESKit?
- **Elapsed time:** 80.854 seconds

## Response

ESKit is a command-line interface (CLI) tool designed to interact with **Elasticsearch** (ES) for managing archives, index lifecycle management (ILM), and AI-related tasks. It provides a structured way to perform operations such as:

### Key Features:
1. **Archive Management** (`eskit archive`):
   - Manage Elasticsearch archives (e.g., show details, retrieve metadata).
   - Supports filtering fields, flat output, and JSON formatting.

2. **Index Lifecycle Management (ILM)** (`eskit ilm`):
   - Handle lifecycle policies for indices (e.g., show configurations, manage retention rules).
   - Integrates with Elasticsearch's ILM framework for automated index management.

3. **AI Integration** (`eskit ai`):
   - Interact with AI models (e.g., ask questions using LLMs like Claude, Qwen, Gemma).
   - Supports specifying models, outputting results as JSON, and saving commands to files.

### Common Options:
- **Config File**: Use `--config` to specify a configuration file (default: `.eskit/config.json`).
- **Host**: Specify a host with `--host` (falls back to `.current_host` if unset).
- **Output**: Use `-j` for JSON output, `-v`/`-d` for verbose/debug logging.

### Example Commands:
- `eskit archive show <name>`: Display details of an archive.
- `eskit ilm show <name>`: View ILM policies for an index.
- `eskit ai --question "Explain ILM" --model qwen3:4b`: Ask an AI question using a specific model.

ESKit simplifies Elasticsearch administration and extends its capabilities with AI tools, making it useful for developers and DevOps engineers working with Elasticsearch clusters.
