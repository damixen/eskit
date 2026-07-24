from eskit.render.display_fields import DisplaySchema, DisplayField
from eskit.projection import project
from eskit.resource.snapshot import SNAPSHOT_SCHEMA
from eskit.render.generic import render_table_2, render_fields, render_heading

SNAPSHOT_DISPLAY = DisplaySchema(
    [
        DisplayField(("repository",)),
        DisplayField(("snapshot",)),
        DisplayField(("version",)),
        DisplayField(("indices",), width=50, preview=True),
        DisplayField(("state",)),
        DisplayField(("start_time",), label="Created At"),
    ]
)

GENERAL_DISPLAY = DisplaySchema(
    [
        DisplayField(("snapshot",)),
        DisplayField(("repository",)),
        DisplayField(("version",)),
        DisplayField(("indices",), width=50, preview=True),
        DisplayField(("state",)),
    ]
)

EXECUTION_DISPLAY = DisplaySchema(
    [
        DisplayField(("start_time",), label="Started"),
        DisplayField(("end_time",), label="Ended"),
        DisplayField(("duration_in_millis",), label="Duration"),
    ]
)

SHARD_DISPLAY = DisplaySchema(
    [
        DisplayField(("shards", "total"), label="Total"),
        DisplayField(("shards", "successful"), label="Successful"),
        DisplayField(("shards", "failed"), label="Failed"),
    ]
)

OPTIONS_DISPLAY = DisplaySchema(
    [
        DisplayField(("include_global_state",)),
    ]
)

CONTENTS_DISPLAY = DisplaySchema(
    [
        DisplayField(("indices",), label=None),
    ]
)


def normalize_snapshots(cache: dict) -> list[dict]:
    snapshots = []

    for repository in cache.values():
        snapshots.extend(repository["snapshots"])

    return snapshots


def render_cat_snapshot(snapshot):

    render_table_2(
        project(snapshot, SNAPSHOT_DISPLAY.paths()), SNAPSHOT_DISPLAY, SNAPSHOT_SCHEMA
    )


def render_show_snapshot(snapshot):
    render_heading("General")
    render_fields(
        project(snapshot, GENERAL_DISPLAY.paths()), GENERAL_DISPLAY, SNAPSHOT_SCHEMA
    )

    render_heading("Execution")
    render_fields(
        project(snapshot, EXECUTION_DISPLAY.paths()), EXECUTION_DISPLAY, SNAPSHOT_SCHEMA
    )

    render_heading("Shards")
    render_fields(
        project(snapshot, SHARD_DISPLAY.paths()), SHARD_DISPLAY, SNAPSHOT_SCHEMA
    )

    render_heading("Options")
    render_fields(
        project(snapshot, OPTIONS_DISPLAY.paths()), OPTIONS_DISPLAY, SNAPSHOT_SCHEMA
    )

    render_heading("Contents")

    render_heading(f"Indices ({len(snapshot["indices"])})", skip_newline=True)
    render_fields(
        project(snapshot, CONTENTS_DISPLAY.paths()), CONTENTS_DISPLAY, SNAPSHOT_SCHEMA
    )
