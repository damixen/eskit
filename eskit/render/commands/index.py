from eskit.projection import project
from eskit.resource.index import INDEX_SCHEMA
from eskit.render.generic import render_table_2, render_fields
from eskit.render.display_fields import DisplayField, DisplaySchema
from eskit.render.generic import (
    render_heading)

INDEX_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=("health",),
            label="Health",
        ),
        DisplayField(path=("index",), label="Name", width=50),
        DisplayField(
            path=("docs.count",),
            label="Docs",
        ),
        DisplayField(
            path=("store.size",),
            label="Size",
        ),
        DisplayField(
            path=(
                "version",
                "created",
            ),
            label="Version",
        ),
        DisplayField(
            path=("creation.date.string",),
            label="Created At",
        ),
    ]
)

GENERAL_SCHEMA = DisplaySchema(
    [
        DisplayField(("index",), label="Name"),
        DisplayField(("uuid",), label="UUID"),
        DisplayField(("creation.date.string",), label="Created At"),
        DisplayField(
            path=(
                "settings",
                "index",
                "version",
                "created",
            ),
            label="Version",
        ),
    ]
)

STORAGE_SCHEMA = DisplaySchema(
    [
        DisplayField(("health",), label="Health"),
        DisplayField(("status",), label="Status"),
        DisplayField(("docs.count",), label="Documents"),
        DisplayField(("store.size",), label="Size"),
        DisplayField(("settings", "index", "number_of_shards"), label="Primary Shards"),
        DisplayField(("settings", "index", "number_of_replicas"), label="Replicas"),
    ]
)

LIFECYCLE_SCHEMA = DisplaySchema(
    [
        DisplayField(("settings", "index", "lifecycle", "name"), label="ILM Policy"),
        DisplayField(
            ("settings", "index", "refresh_interval"), label="Refresh Interval"
        ),
    ]
)

MAPPING_SCHEMA = DisplaySchema(
    [
        DisplayField(
            ("mappings", "properties", "@timestamp", "type"), label="@timestamp Type"
        ),
        DisplayField(
            ("mappings", "properties", "@timestamp", "format"),
            label="@timestamp Format",
        ),
    ]
)

RECOVERY_SCHEMA = DisplaySchema(
    [
        DisplayField(("index",)),
        DisplayField(("shard",)),
        DisplayField(("type",)),
        DisplayField(("stage",)),
        DisplayField(("time",)),



    ]
)

TARGET_SCHEMA = DisplaySchema(
    [
        DisplayField(("node",)),
        DisplayField(("host",)),
    ]
)

DATA_SCHEMA = DisplaySchema(
    [
        DisplayField(("files_total",), label="Total Files"),
        DisplayField(("files_percent",), label="File Progres"),
        DisplayField(("bytes_total",), label="Total Bytes"),
        DisplayField(("bytes_percent",), label="Bytes Progress"),
    ]
)

STATUS_DISPLAY = DisplaySchema(
    [
        DisplayField(("index",)),
        DisplayField(("shard",)),
        DisplayField(("type",)),
        DisplayField(("stage",)),
        DisplayField(("time",)),
        DisplayField(("files_total",), label="Total Files"),
        DisplayField(("bytes_total",), label="Total Bytes"),
        DisplayField(("bytes_percent",), label="Progress"),
    ]

)

def render_cat_index(indices):

    render_table_2(project(indices, INDEX_DISPLAY.paths()), INDEX_DISPLAY, INDEX_SCHEMA)


def render_show_index(indices):
    render_heading("General")
    render_fields(
        project(indices, GENERAL_SCHEMA.paths()), GENERAL_SCHEMA, INDEX_SCHEMA
    )

    render_heading("Storage")
    render_fields(
        project(indices, STORAGE_SCHEMA.paths()), STORAGE_SCHEMA, INDEX_SCHEMA
    )

    render_heading("Lifecycle")
    render_fields(
        project(indices, LIFECYCLE_SCHEMA.paths()), LIFECYCLE_SCHEMA, INDEX_SCHEMA
    )

    render_heading("Mapping")
    render_fields(
        project(indices, MAPPING_SCHEMA.paths()), MAPPING_SCHEMA, INDEX_SCHEMA
    )

def render_index_status_list(indices):

    render_table_2(project(indices, STATUS_DISPLAY.paths()), STATUS_DISPLAY, INDEX_SCHEMA)


def render_index_status_detail(index):

    '''
    Recovery
    --------
    Index      logstash-2026.06.30
    Shard      0
    Type       Existing Store
    Stage      done
    Time       1.4 s

    Target
    ------
    Node   tpotcluster-node-01
    Host   127.0.0.1

    Data
    ----
    Total Files  52
    Total Size   310.2 MB
    '''

    render_heading("Recovery")
    render_fields(
        project(index, RECOVERY_SCHEMA.paths()), RECOVERY_SCHEMA, INDEX_SCHEMA
    )

    render_heading("Target")
    render_fields(
        project(index, TARGET_SCHEMA.paths()), TARGET_SCHEMA, INDEX_SCHEMA
    )

    render_heading("Data")
    render_fields(
        project(index, DATA_SCHEMA.paths()), DATA_SCHEMA, INDEX_SCHEMA
    )

def render_index_status(indices):
    render_index_status_list(indices)