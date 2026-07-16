from typing import Any, overload
from dataclasses import dataclass


@dataclass
class Field:
    path: str
    label: str | None = None
    format: str | None = None


def build_field_list(view_config, views, fields):
    """
    Builds a unique list of fields from views and explicit field selections.
    """
    result = []

    for view in views or []:
        result.extend(view_config.get(view, []))

    if fields:
        result.extend(fields.split(","))

    return list(dict.fromkeys(result))


def get_path(data, path):
    current = data

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        part = part.replace("$", ".")

        if part not in current:
            return None

        current = current[part]

    return current


def set_path(data, path, value):
    parts = path.split(".")
    current = data

    for part in parts[:-1]:
        part = part.replace("$", ".")

        if part not in current:
            current[part] = {}

        current = current[part]

    current[parts[-1].replace("$", ".")] = value


def normalize_field(field):
    if isinstance(field, str):
        return Field(path=field, label=None, format=None)

    _path = field["path"]
    _label = field.get("label", None)
    _format = field.get("format", None)

    return Field(path=_path, label=_label, format=_format)


@overload
def project(
    value: dict[str, Any],
    fields: list[str] | list[dict[str, str]],
    flatten: bool = False,
) -> dict[str, Any]: ...


@overload
def project(
    value: list[dict[str, Any]],
    fields: list[str] | list[dict[str, str]],
    flatten: bool = False,
) -> list[dict[str, Any]]: ...


def project(
    value: dict[str, Any] | list[dict[str, Any]],
    fields: list[str] | list[dict[str, str]],
    flatten: bool = False,
) -> dict[str, Any] | list[dict[str, Any]]:

    if isinstance(value, list):
        return project_list(value, fields, flatten)

    return project_object(value, fields, flatten)


def project_list(
    value: list[dict[str, Any]],
    fields: list[str] | list[dict[str, str]],
    flatten: bool = False,
) -> list[dict[str, Any]]:

    return [project_object(item, fields, flatten) for item in value]


def project_object(
    value: dict[str, Any],
    fields: list[str] | list[dict[str, str]],
    flatten: bool = False,
) -> dict[str, Any]:

    out: dict[str, Any] = {}

    for field in fields:
        descriptor = normalize_field(field)

        path = descriptor.path

        field_value = get_path(value, path)

        if flatten:
            out[path] = field_value
        elif field_value is not None:
            set_path(out, path, field_value)

    return out
