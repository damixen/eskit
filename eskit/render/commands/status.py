from eskit.render.generic import (
    render_heading,
    render_fields,
)
from eskit.render.projection import project

HOST_FIELDS = ["name", {"path": "push-protected", "format": "bool"}]


CLUSTER_FIELDS = [
    "cluster_name",
    {"path": "name", "label": "Node Name", "format": ""},
    {"path": "version.number", "label": "Version"},
]


CACHE_FIELDS = [
    {"path": "indices.last-updated", "label": "Index", "format": "datetime"},
    {"path": "repos.last-updated", "label": "Repository", "format": "datetime"},
    {"path": "snapshots.last-updated", "label": "Snapshot", "format": "datetime"},
    {"path": "version.last-updated", "label": "Version", "format": "datetime"},
]


def render_status(status):
    print("ESKit Status")

    host = project(
        status["host"],
        HOST_FIELDS,
    )

    render_heading("Current Host")
    render_fields(host, HOST_FIELDS)

    cluster = project(status["cluster"], CLUSTER_FIELDS)

    render_heading("Elasticsearch")
    render_fields(cluster, CLUSTER_FIELDS)

    cache = project(status["caches"], CACHE_FIELDS)

    render_heading("Cache (Last Updated)")
    render_fields(cache, CACHE_FIELDS)
