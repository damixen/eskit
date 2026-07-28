import json
from dataclasses import asdict, is_dataclass
from typing import Any
from eskit.render.generic import render_object, render_table
from eskit.render.commands.status import render_status
from eskit.render.commands.host import render_host_show
from eskit.render.commands.index import (
    render_cat_index,
    render_show_index,
    render_index_status,
)
from eskit.render.commands.repository import (
    render_cat_repository,
    render_show_repository,
)
from eskit.render.commands.snapshot import render_cat_snapshot, render_show_snapshot
from eskit.render.commands.job import render_show_job, render_list_jobs
from eskit.render.commands.archive import render_show_archive, render_list_archives
from eskit.render.commands.ilm import render_cat_ilm, render_show_ilm
from eskit.projection import project

RENDERER = {
    "status": render_status,
    "show_host_config": render_host_show,
    "cat_index": render_cat_index,
    "cat_repository": render_cat_repository,
    "cat_snapshot": render_cat_snapshot,
    "show_index": render_show_index,
    "show_repository": render_show_repository,
    "show_snapshot": render_show_snapshot,
    "status_index": render_index_status,
    "show_job": render_show_job,
    "list_jobs": render_list_jobs,
    "list_archives": render_list_archives,
    "show_archive": render_show_archive,
    "cat_ilm": render_cat_ilm,
    "show_ilm": render_show_ilm
}


def render_command(
    command,
    value,
    context
):
    renderer = RENDERER.get(command)

    if renderer:
        renderer(value, context)
        return

    render_object(value)


def normalize(value: Any) -> Any:
    """
    Convert dataclasses to dictionaries recursively.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    if isinstance(value, list):
        return [normalize(v) for v in value]

    return value


def render(
    value: Any,
    *,
    command: str | None,
    output_format: str = "table",
    fields: list[tuple[str, ...]],
    flatten: bool = False,
    context: dict[str, Any] | None
):
    value = normalize(value)

    if fields:
        value = project(
            value,
            fields,
            flatten=flatten,
        )

    if output_format == "json":
        render_json(value)
        return

    if command:
        render_command(command, value, context)
        return

    render_object(value)


def render_json(value):
    print(json.dumps(value, indent=2))
