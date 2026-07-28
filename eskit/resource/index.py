from eskit.resource.schema import Schema, Field, FieldType

INDEX_SCHEMA = Schema(
    [
        Field(("health",)),
        Field(("status",)),
        Field(("index",)),
        Field(("uuid",)),
        Field(("docs.count",), type=FieldType.INTEGER),
        Field(("store.size",), type=FieldType.SIZE),
        Field(("creation.date.string",), type=FieldType.DATETIME),
        Field(("version", "created"), type=FieldType.TEXT),
        Field(("ilm", "managed"), type=FieldType.BOOLEAN),
        Field(
            ("ilm", "policy"),
        ),
        Field(("ilm", "age_in_millis"), type=FieldType.DURATION),
        Field(
            ("ilm", "phase"),
        ),
        Field(
            ("ilm", "action"),
        ),
        Field(
            ("ilm", "step"),
        ),
        Field(("ilm", "remaining_ms"), type=FieldType.DURATION),
        Field(
            ("ilm", "retention"),
        ),
        Field(("settings", "index", "provided_name"), type=FieldType.TEXT),
        Field(("settings", "index", "creation_date"), type=FieldType.TEXT),
        Field(("settings", "index", "uuid"), type=FieldType.TEXT),
        Field(("settings", "index", "provided_name"), type=FieldType.TEXT),
        Field(("settings", "index", "creation_date"), type=FieldType.TEXT),
        Field(("settings", "index", "number_of_shards"), type=FieldType.INTEGER),
        Field(("settings", "index", "refresh_interval"), type=FieldType.TEXT),
        Field(("settings", "index", "number_of_replicas"), type=FieldType.INTEGER),
        Field(("settings", "index", "lifecycle", "name"), type=FieldType.TEXT),
        Field(("settings", "index", "version", "created"), type=FieldType.TEXT),
        Field(("mappings", "properties", "@timestamp", "type"), type=FieldType.TEXT),
        Field(("mappings", "properties", "@timestamp", "format"), type=FieldType.TEXT),
        Field(("time",)),
        Field(("stage",)),
        Field(("target_node",)),
        Field(("target_host",)),
        Field(("files_percent",)),
        Field(("files_total",)),
        Field(("bytes_total",), type=FieldType.SIZE),
        Field(("bytes_percent",)),
        Field(("shard",)),
        Field(("type",)),
    ]
)
