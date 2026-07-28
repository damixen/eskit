from dataclasses import dataclass
from typing import Any

AUTO_LABEL = object()

@dataclass
class DisplayField:
    path: tuple[str, ...]
    label: str | None | object = AUTO_LABEL
    width: int | None = None
    preview: bool | None = None
    preview_single: str | None = None
    preview_plural: str | None = None
    preview_allow_zero: bool | None = None
    empty_value: str | None = None
    duration_compact: bool | None = None
    blank_field: bool | None = None


class DisplaySchema:
    def __init__(self, fields: list[DisplayField]):
        self.fields = fields

    def paths(self) -> list[tuple[str, ...]]:
        return [field.path for field in self.fields if not field.blank_field]

    def names(self) -> list[str]:
        return [".".join(field.path) for field in self.fields if not field.blank_field]


def build_field_name_list(
    view_config, views, fields
) -> list[str] | list[dict[str, Any]]:
    """
    Builds a unique list of fields from views and explicit field selections.
    """
    result = []

    for view in views or []:
        result.extend(view_config.get(view, []))

    if fields:
        result.extend(fields.split(","))

    return list(dict.fromkeys(result))


def normalize_display_fields(
    fields: list[str] | list[dict[str, Any]],
) -> list[DisplayField]:
    result = []

    seen = set()

    for field in fields:
        normalized = normalize_display_field(field)

        path = normalized.path

        if path in seen:
            continue

        seen.add(path)
        result.append(normalized)

    return result


def normalize_path(path: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(path, str):
        return tuple(path.split("."))

    return tuple(path)


def normalize_display_field(field: str | dict[str, Any]):
    if isinstance(field, str):
        return DisplayField(path=normalize_path(field), label=None)

    _path = normalize_path(field["path"])
    _label = field.get("label", None)

    return DisplayField(path=_path, label=_label)
