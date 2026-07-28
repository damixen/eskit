from eskit.projection import project
from eskit.resource.host import HOST_SCHEMA, CACHE_SCHEMA, CLUSTER_SCHEMA
from eskit.render.display_fields import DisplaySchema, DisplayField
from eskit.render.generic import render_fields, render_table, render_heading, render_context

HOST_DISPLAY = DisplaySchema(
    [
        DisplayField(("name", )), 
        DisplayField(("push-protected", ))
    ]
)

CLUSTER_DISPLAY = DisplaySchema(
    [
        DisplayField(("name", ), label="Node"),
        DisplayField(("cluster_name", ), label="Cluster"),
        DisplayField(("version", "number",), label="Version"),
        DisplayField(("version", "build_flavor"), label="Build"),
    ]
)

CACHE_DISPLAY = DisplaySchema(
    [
        DisplayField(("name", )),
        DisplayField(("last-updated", ), label="Last Updated"),
    ]
)

def render_status(status, context = None):
    print("ESKit Status")

    render_heading("Current Host")
    render_fields(project(status["host"], HOST_DISPLAY.paths()), HOST_DISPLAY, HOST_SCHEMA)

    render_heading("Elasticsearch")
    render_fields(project(status["cluster"], CLUSTER_DISPLAY.paths()), CLUSTER_DISPLAY, CLUSTER_SCHEMA)

    render_heading("Caches")
    render_table(project(status["caches"], CACHE_DISPLAY.paths()), CACHE_DISPLAY, CACHE_SCHEMA)

    render_context(context)