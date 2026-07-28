from eskit.projection import project
from eskit.resource.index import INDEX_SCHEMA
from eskit.render.generic import render_table, render_fields, render_context
from eskit.render.display_fields import DisplayField, DisplaySchema
from eskit.render.generic import render_heading

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
            path=(
                "ilm",
                "policy",
            ),
            label="Policy",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "ilm",
                "age_in_millis",
            ),
            label="Age",
            empty_value="(n/a)",
            duration_compact=True,
        ),
        DisplayField(
            path=(
                "ilm",
                "remaining_ms",
            ),
            label="Remaining",
            empty_value="(n/a)",
            duration_compact=True,
        ),
        DisplayField(
            path=("creation.date.string",),
            label="Created At",
        ),
    ]
)

GENERAL_DISPLAY = DisplaySchema(
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

STORAGE_DISPLAY = DisplaySchema(
    [
        DisplayField(("health",), label="Health"),
        DisplayField(("status",), label="Status"),
        DisplayField(("docs.count",), label="Documents"),
        DisplayField(("store.size",), label="Size"),
        DisplayField(("settings", "index", "number_of_shards"), label="Primary Shards"),
        DisplayField(("settings", "index", "number_of_replicas"), label="Replicas"),
    ]
)

LIFECYCLE_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=(
                "ilm",
                "managed",
            ),
            label="Managed",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "ilm",
                "policy",
            ),
            label="Policy",
            empty_value="(none)",
        ),
        DisplayField(path=(), blank_field=True),
        DisplayField(
            path=(
                "ilm",
                "phase",
            ),
            label="Phase",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "ilm",
                "action",
            ),
            label="Action",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "ilm",
                "step",
            ),
            label="Step",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "ilm",
                "retention",
            ),
            label="Retention",
            empty_value="(n/a)",
        ),
        DisplayField(path=(), blank_field=True),
        DisplayField(
            path=(
                "ilm",
                "age_in_millis",
            ),
            label="Age",
            empty_value="(n/a)",
        ),
        DisplayField(
            path=(
                "ilm",
                "remaining_ms",
            ),
            label="Remaining",
            empty_value="(n/a)",
        ),
        DisplayField(
            ("settings", "index", "refresh_interval"),
            label="Refresh Interval",
            empty_value="-",
        ),
    ]
)

MAPPING_DISPLAY = DisplaySchema(
    [
        DisplayField(
            ("mappings", "properties", "@timestamp", "type"), label="@timestamp Type"
        ),
        DisplayField(
            ("mappings", "properties", "@timestamp", "format"),
            label="@timestamp Format",
            empty_value="-",
        ),
    ]
)

RECOVERY_DISPLAY = DisplaySchema(
    [
        DisplayField(("index",)),
        DisplayField(("shard",)),
        DisplayField(("type",)),
        DisplayField(("stage",)),
        DisplayField(("time",)),
    ]
)

TARGET_DISPLAY = DisplaySchema(
    [
        DisplayField(("node",)),
        DisplayField(("host",)),
    ]
)

DATA_DISPLAY = DisplaySchema(
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


def render_cat_index(indices, context = None):

    render_table(project(indices, INDEX_DISPLAY.paths()), INDEX_DISPLAY, INDEX_SCHEMA)
    render_context(context)

def render_show_index(indices, context = None):
    render_heading("General")
    render_fields(
        project(indices, GENERAL_DISPLAY.paths()), GENERAL_DISPLAY, INDEX_SCHEMA
    )

    render_heading("Storage")
    render_fields(
        project(indices, STORAGE_DISPLAY.paths()), STORAGE_DISPLAY, INDEX_SCHEMA
    )

    render_heading("ILM")
    render_fields(
        project(indices, LIFECYCLE_DISPLAY.paths()), LIFECYCLE_DISPLAY, INDEX_SCHEMA
    )

    render_heading("Mapping")
    render_fields(
        project(indices, MAPPING_DISPLAY.paths()), MAPPING_DISPLAY, INDEX_SCHEMA
    )
    render_context(context)


def render_index_status_list(indices, context = None):

    render_table(project(indices, STATUS_DISPLAY.paths()), STATUS_DISPLAY, INDEX_SCHEMA)
    render_context(context)

def render_index_status_detail(index, context = None):
    """
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
    """

    render_heading("Recovery")
    render_fields(
        project(index, RECOVERY_DISPLAY.paths()), RECOVERY_DISPLAY, INDEX_SCHEMA
    )

    render_heading("Target")
    render_fields(project(index, TARGET_DISPLAY.paths()), TARGET_DISPLAY, INDEX_SCHEMA)

    render_heading("Data")
    render_fields(project(index, DATA_DISPLAY.paths()), DATA_DISPLAY, INDEX_SCHEMA)

    render_context(context)


def render_index_status(indices, context = None):
    render_index_status_list(indices)

    render_context(context)
