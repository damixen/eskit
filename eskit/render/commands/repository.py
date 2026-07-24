from eskit.render.display_fields import DisplaySchema, DisplayField
from eskit.projection import project
from eskit.resource.repository import REPOSITORY_SCHEMA
from eskit.render.generic import render_table_2, render_fields
from eskit.render.generic import (
    render_heading)

REPOSITORY_DISPLAY = DisplaySchema(
    [
        DisplayField(("name",), "Name"),
        DisplayField(("type",), "Type"),
        DisplayField(("settings", "location"), label="Location"),
        DisplayField(("settings", "compress"), label="Compress"),
    ]
)

GENERAL_DISPLAY = DisplaySchema(
    [
        DisplayField(("name",), "Name"),
        DisplayField(("type",), "Type"),
        DisplayField(("uuid",), label="UUID"),
    ]
)

SETTINGS_DISPLAY = DisplaySchema(
    [
        DisplayField(("settings", "location"), label="Location"),
        DisplayField(("settings", "compress"), label="Compress"),
    ]
)

SNAPSHOTS_DISPLAY = DisplaySchema(
    [
        DisplayField(("snapshots",), label=None),
    ]
)



def render_cat_repository(repos):
    render_table_2(
        project(repos, REPOSITORY_DISPLAY.paths()),
        REPOSITORY_DISPLAY,
        REPOSITORY_SCHEMA,
    )

def render_show_repository(repo):
    render_heading("Repository")
    render_fields(project(repo, GENERAL_DISPLAY.paths()), GENERAL_DISPLAY, REPOSITORY_SCHEMA)

    render_heading("Settings")
    render_fields(project(repo, SETTINGS_DISPLAY.paths()), SETTINGS_DISPLAY, REPOSITORY_SCHEMA)

    render_heading("Snapshots")
    render_fields(project(repo, SNAPSHOTS_DISPLAY.paths()), SNAPSHOTS_DISPLAY, REPOSITORY_SCHEMA)