import json
from dataclasses import asdict, is_dataclass
from typing import Any
from eskit.render.generic import render_object
from eskit.render.commands.status import render_status
from eskit.render.commands.host import (
    render_host_show,
    render_host_get,
    render_host_set,
)
from eskit.render.commands.index import (
    render_cat_index,
    render_show_index,
    render_index_status,
    render_reindex_mapping,
    render_index_create,
    render_index_delete,
    render_reindex,
)
from eskit.render.commands.repository import (
    render_cat_repository,
    render_show_repository,
    render_delete_repo,
    render_create_repo,
)
from eskit.render.commands.snapshot import (
    render_cat_snapshot,
    render_show_snapshot,
    render_create_snapshot,
    render_delete_snapshot,
    render_restore_snapshot,
)
from eskit.render.commands.job import render_show_job, render_list_jobs
from eskit.render.commands.archive import render_show_archive, render_list_archives, render_pull, render_push, render_sync
from eskit.render.commands.ilm import render_cat_ilm, render_show_ilm
from eskit.render.commands.metadata import render_pull_metadata
from eskit.render.commands.task import render_task_get
from eskit.render.commands.init import render_init
from eskit.projection import project
from eskit.result import Result, ResultCode

RENDERER = {
    "cmd_status": render_status,
    "cmd_show_host": render_host_show,
    "cmd_set_host": render_host_set,
    "cmd_get_host": render_host_get,
    "cat_index": render_cat_index,
    "cat_repository": render_cat_repository,
    "cat_snapshot": render_cat_snapshot,
    "cmd_show_index": render_show_index,
    "show_repository": render_show_repository,
    "show_snapshot": render_show_snapshot,
    "cmd_restore_status": render_index_status,
    "cmd_read_job": render_show_job,
    "cmd_reindex": render_reindex,
    "cmd_list_jobs": render_list_jobs,
    "cmd_list_archives": render_list_archives,
    "cmd_show_archive": render_show_archive,
    "cat_ilm": render_cat_ilm,
    "cmd_show_ilm": render_show_ilm,
    "cmd_pull": render_pull_metadata,
    "cmd_delete_repo": render_delete_repo,
    "cmd_create_repo": render_create_repo,
    "cmd_reindex_mapping": render_reindex_mapping,
    "cmd_create_snapshot": render_create_snapshot,
    "cmd_delete_snapshot": render_delete_snapshot,
    "cmd_restore_snapshot" : render_restore_snapshot,
    "cmd_delete_index" : render_index_delete,
    "cmd_create_index" : render_index_create,
    "cmd_get_task" : render_task_get,
    "cmd_init" : render_init,
    "cmd_pull_archive" : render_pull,
    "cmd_sync_archive" : render_sync,
    "cmd_push_archive" : render_push
}


def render_command(command, value, context):
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


def render_result(args, result: Result):
    # get some context needed for rendering from args
    # call render

    if not result:
        return

    if result.code == ResultCode.CANCELED:
        print("Canceled.")
        return

    if result.code != ResultCode.SUCCESS:
        return

    from eskit.projection import build_field_list, normalize_projection

    context = result.command_context
    fields = []
    output_format = ""
    flatten = False
    command = ""
    if context:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        output_format = context.render.output_format
        flatten = context.render.flat
        command = context.command
    # print("output_format:", output_format)
    # print("command:", command)
    projection = normalize_projection(fields)

    render(
        result.value,
        command=command,
        output_format=output_format,
        fields=projection,
        flatten=flatten,
        context=result.context,
    )


def render(
    value: Any,
    *,
    command: str | None,
    output_format: str = "table",
    fields: list[tuple[str, ...]],
    flatten: bool = False,
    context: dict[str, Any] | None,
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
