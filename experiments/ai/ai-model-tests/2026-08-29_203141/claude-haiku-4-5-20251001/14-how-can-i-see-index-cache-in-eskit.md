# Test
- **Model:** claude-haiku-4-5-20251001
- **Question:** How can I see index cache in eskit?
- **Elapsed time:** 4.742 seconds

# Response

# Usage ---
- **Input tokens:**  7594
- **Output tokens:** 339
- **Estimated cost with model:**claude-haiku-4-5-20251001: $0.009289

To see the index cache in ESKit, use the **`eskit cat index`** command.

This command shows cached information about indexes.

## Basic Usage

```bash
eskit cat index
```

## With Common Options

You can enhance the output with these common arguments:

- **`--json`** / **`-j`**: Output in JSON format
  ```bash
  eskit cat index --json
  ```

- **`--view <name>`**: Apply a named view defined in your config
  ```bash
  eskit cat index --view <view_name>
  ```

- **`--fields <fields>`**: Retrieve specific fields
  ```bash
  eskit cat index --fields settings.index.provided_name
  ```

- **`--flat`**: Flatten the output structure
  ```bash
  eskit cat index --flat
  ```

- **`--verbose`** / **`-v`**: Enable verbose logging
  ```bash
  eskit cat index --verbose
  ```

- **`--config`** / **`-c`**: Specify a custom config file
  ```bash
  eskit cat index --config /path/to/config.json
  ```

## Note

The `cat index` command reads from the local cache. If the cache is empty or outdated, you may need to first pull the data from Elasticsearch:

```bash
eskit pull es
```

This will update the cache with current index information from your Elasticsearch host.
