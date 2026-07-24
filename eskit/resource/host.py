from eskit.resource.schema import Schema, Field, FieldType

HOST_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("ip",)),
        Field(("push-protected",), FieldType.BOOLEAN),
    ]
)

SSH_SCHEMA = Schema(
    [
        Field(("port",)),
        Field(("user",)),
        Field(("use_sshpass",), FieldType.BOOLEAN),
    ]
)

ELASTIC_SCHEMA = Schema(
    [
        Field(("user", "name")),
        Field(("port",)),
    ]
)

CACHE_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("last-updated",), type=FieldType.DATETIME),
    ]
)

CLUSTER_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("cluster_name",)),
        Field(("version", "number")),
        Field(("version", "build_flavor")),
    ]
)
