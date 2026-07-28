from eskit.resource.schema import Schema, Field, FieldType

ARCHIVE_SCHEMA = Schema(
    [
        Field(("name",)),
        Field(("created_at",), type=FieldType.DATETIME),
        Field(("updated_at",), type=FieldType.DATETIME),
        Field(("last_pull",), type=FieldType.DATETIME),
        Field(("remote_src_stat", "name")),
        Field(("remote_src_stat", "mode")),
        Field(("remote_src_stat", "owner")),
        Field(("remote_src_stat", "group")),
        Field(
            (
                "remote_src_stat",
                "mtime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "remote_src_stat",
                "atime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "remote_src_stat",
                "ctime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "remote_src_stat",
                "size",
            ),
            type=FieldType.SIZE,
        ),
        Field(("local_dst_stat", "name")),
        Field(("local_dst_stat", "mode")),
        Field(("local_dst_stat", "owner")),
        Field(("local_dst_stat", "group")),
        Field(
            (
                "local_dst_stat",
                "mtime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "local_dst_stat",
                "atime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "local_dst_stat",
                "ctime_iso",
            ),
            type=FieldType.DATETIME,
        ),
        Field(
            (
                "local_dst_stat",
                "size",
            ),
            type=FieldType.SIZE,
        ),
        # config
        Field(("type",)),
        Field(("remote_src",)),
        Field(("local_dst",)),
    ]
)
