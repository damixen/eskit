from eskit.resource.schema import Schema, Field, FieldType

ILM_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("version",), FieldType.INTEGER),
        Field(("modified_date",), FieldType.DATETIME),
        Field(("policy", "phases", "hot", "min_age")),
        Field(("policy", "phases", "hot", "actions", "rollover", "max_age")),
        Field(("policy", "phases", "hot", "actions", "rollover", "max_primary_shard_size")),
        Field(("policy", "phases", "delete", "min_age")),
        Field(("policy", "phases", "delete", "actions", "delete", "delete_searchable_snapshot")),
        Field(("policy", "_meta", "managed"), FieldType.BOOLEAN),
        Field(("in_use_by", "indices"), FieldType.LIST),
    ]
)

