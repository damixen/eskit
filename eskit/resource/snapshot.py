from eskit.resource.schema import Schema, Field, FieldType

SNAPSHOT_SCHEMA = Schema(
    [
        Field(("repository",)),
        Field(("snapshot",)),
        Field(("uuid",)),
        Field(("version",)),
        Field(("indices",), type=FieldType.LIST),
        Field(("state",)),
        Field(("start_time",), type=FieldType.DATETIME),
        Field(("end_time",), type=FieldType.DATETIME),
        Field(("duration_in_millis",), type=FieldType.DURATION),
        Field(
            (
                "shards",
                "total",
            ),
            type=FieldType.INTEGER,
        ),
        Field(
            (
                "shards",
                "failed",
            ),
            type=FieldType.INTEGER,
        ),
        Field(
            (
                "shards",
                "successful",
            ),
            type=FieldType.INTEGER,
        ),
        Field(("include_global_state",), type=FieldType.BOOLEAN),
    ]
)
