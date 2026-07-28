from eskit.resource.schema import Schema, Field, FieldType

REPOSITORY_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("type",)),
        Field(("uuid",)),
        Field(("settings", "location")),
        Field(("settings", "compress"), type=FieldType.BOOLEAN),
        Field(("snapshots",), FieldType.LIST),
    ]
)
