from eskit.projection import project
from eskit.resource.archive import ARCHIVE_SCHEMA
from eskit.render.generic import render_table, render_fields, render_heading
from eskit.render.display_fields import DisplayField, DisplaySchema

ARCHIVE_DISPLAY = DisplaySchema(
    [
        DisplayField(("name",)),
        DisplayField(("updated_at",)),
        DisplayField(("remote_src_stat", "name"), label="Remote Src"),
        DisplayField(
            (
                "remote_src_stat",
                "mtime_iso",
            ),
            label="Last Modified At",
        ),
        DisplayField(
            (
                "remote_src_stat",
                "size",
            ),
            label="Size"
        ),
        DisplayField(("local_dst_stat", "name"), label="Local Dst"),
        DisplayField(
            (
                "local_dst_stat",
                "mtime_iso",
            ),
            label="Last Modified At",
        ),
        DisplayField(
            (
                "local_dst_stat",
                "size",
            ),
            label="Size"
        ),
    ]
)

GENERAL_SCHEMA = DisplaySchema(
    [
        DisplayField(("name",)),
        DisplayField(("created_at",)),
        DisplayField(("updated_at",)),
        DisplayField(("last_pull",)),
    ]
)

REMOTE_SOURCE_SCHEMA = DisplaySchema(
    [
        DisplayField(("remote_src_stat", "name"), label="Name"),
        DisplayField(
            (
                "remote_src_stat",
                "mtime_iso",
            ),
            label="Last Modified At",
        ),
        DisplayField(
            (
                "remote_src_stat",
                "atime_iso",
            ),
            label="Accessed At",
        ),
        DisplayField(
            (
                "remote_src_stat",
                "size",
            ),
            label="Size"
        ),
    ]
)

LOCAL_DESTINATION_SCHEMA = DisplaySchema(
    [
        DisplayField(("local_dst_stat", "name"), label="Name"),
        DisplayField(
            (
                "local_dst_stat",
                "mtime_iso",
            ),
            label="Last Modified At",
        ),
        DisplayField(
            (
                "local_dst_stat",
                "atime_iso",
            ),
            label="Accessed At",
        ),
        DisplayField(
            (
                "local_dst_stat",
                "size",
            ),
            label="Size"
        ),
    ]
)


def render_list_archives(archives):

    render_table(
        project(archives, ARCHIVE_DISPLAY.paths()), ARCHIVE_DISPLAY, ARCHIVE_SCHEMA
    )


def render_show_archive(archive):
    render_heading("General")
    render_fields(
        project(archive, GENERAL_SCHEMA.paths()), GENERAL_SCHEMA, ARCHIVE_SCHEMA
    )

    render_heading("Remote Source")
    render_fields(
        project(archive, REMOTE_SOURCE_SCHEMA.paths()),
        REMOTE_SOURCE_SCHEMA,
        ARCHIVE_SCHEMA,
    )

    render_heading("Local Destination")
    render_fields(
        project(archive, LOCAL_DESTINATION_SCHEMA.paths()),
        LOCAL_DESTINATION_SCHEMA,
        ARCHIVE_SCHEMA,
    )
