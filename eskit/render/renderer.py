import json
from dataclasses import asdict, is_dataclass
from typing import Any
from eskit.render.projection import project
from eskit.render.generic import render_object, render_table
from eskit.render.commands.status import render_status


def render_command(
    command,
    value,
):
    if command == "status":
        render_status(value)
        return

    render_human(value)


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
    fields: list[str] | None,
    flatten: bool = False,
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
        render_command(command, value)
        return

    if isinstance(value, list):
        render_table(value)
    else:
        render_object(value)


def render_json(value):
    print(json.dumps(value, indent=2))


def render_human(value):
    if isinstance(value, list):
        render_table(value)
    else:
        for key, val in value.items():
            print(f"{key}: {val}")
