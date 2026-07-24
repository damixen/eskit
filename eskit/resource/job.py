from eskit.resource.schema import Schema, Field, FieldType

JOB_SCHEMA = Schema([
    Field(("id",)),
    Field(("name",)),
    Field(("type",)),
    Field(("host",)),
    Field(("status",)),
    Field(("created_at",), type=FieldType.DATETIME),
    Field(("updated_at",), type=FieldType.DATETIME),
    Field(("payload","src",)),
    Field(("payload","dst",)),
    Field(("result","task_id",)),
    Field(("pid",)),
    Field(("log_path",)),
    Field(("cache_path",)),
    Field(("preview",), type=FieldType.BOOLEAN),
    
])