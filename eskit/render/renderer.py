from dataclasses import asdict, is_dataclass
import json

from eskit.render.projection import project


def normalize(value):
    """
    Convert dataclasses to dictionaries recursively.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    if isinstance(value, list):
        return [normalize(v) for v in value]

    return value


def render(
    value,
    *,
    output_format="table",
    fields=None,
    flatten=False,
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
    else:
        render_human(value)


def render_json(value):
    print(json.dumps(value, indent=2))


def render_human(value):
    if isinstance(value, list):
        render_table(value)
    else:
        for key, val in value.items():
            print(f"{key}: {val}")


def render_table(rows):
    # TODO: implement pretty table
    print(rows)