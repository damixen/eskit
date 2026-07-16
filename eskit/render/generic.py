from typing import Any
from datetime import datetime
from eskit.render.projection import get_path, normalize_field


def render_table(rows):
    # TODO: implement pretty table
    print(rows)


def render_object(rows):
    # TODO: implement pretty table
    print(rows)


def format_label(path: str) -> str:
    words = (
        path.replace("$", ".")
        .replace(".", " ")
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )

    return " ".join(word.capitalize() for word in words)


def format_datetime(value: str) -> str:
    dt = datetime.strptime(
        value,
        "%A, %B %d, %Y at %I:%M %p",
    )

    return dt.strftime("%Y-%m-%d %H:%M")


def format_value(value, format_type=None):
    if value is None:
        return ""

    if format_type == "datetime":
        return format_datetime(value)

    if format_type == "bool":
        return "Yes" if value else "No"

    return str(value)


def render_heading(title: str):
    print()
    print(title)
    print("-" * len(title))


def render_fields(
    data: dict[str, Any],
    fields: list[str] | list[dict[str, str]],
    *,
    flatten: bool = False,
):
    if not data:
        return

    rows = []

    for field in fields:
        descriptor = normalize_field(field)
        path = descriptor.path

        label = descriptor.label or format_label(path)

        if flatten:
            value = data.get(path)
        else:
            value = get_path(data, path)

        rows.append((label, format_value(value, descriptor.format)))

    width = max(len(label) for label, _ in rows)

    for label, value in rows:
        print(f"{label:<{width}}  {value}")
