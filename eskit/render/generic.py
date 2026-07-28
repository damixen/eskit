from typing import Any
from eskit.projection import get_path
from eskit.render.formatters import (
    format_label,
    format_value2,
    resolve_label,
)
from eskit.render.display_fields import DisplaySchema, AUTO_LABEL
from eskit.resource.schema import Schema, FieldType


def truncate(value, width: int) -> str:
    if len(value) <= width:
        return value

    return value[: width - 3] + "..."


def render_table(
    rows: list[dict[str, Any]], display_schema: DisplaySchema, resource_schema: Schema
):
    if not rows:
        print("(none)")
        return

    # Build headers
    headers = [
        label
        for field in display_schema.fields
        if (label := resolve_label(field)) is not None
    ]

    # Build table data
    table = []

    for row in rows:
        values = []

        for field in display_schema.fields:
            value = get_path(row, field.path)
            value = format_value2(
                value, resource_schema.get(field.path).type, display_field=field
            )
            if field.width:
                value = truncate(value, field.width)
            values.append("" if value is None else str(value))

        table.append(values)

    # Compute column widths
    widths = [len(header) for header in headers]

    for values in table:
        for i, value in enumerate(values):
            widths[i] = max(widths[i], len(value))

    # Header
    print("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)))

    # Separator
    print("  ".join("-" * width for width in widths))

    # Rows
    for values in table:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(values)))


def omit_label(ftype: FieldType):
    return ftype == (FieldType.LIST)


def render_fields(
    data: dict[str, Any],
    display_schema: DisplaySchema,
    resource_schema: Schema,
    *,
    flatten: bool = False,
):
    if not data:
        return

    rows = []

    for field in display_schema.fields:

        if field.blank_field:
            rows.append(("", ""))
            continue

        path = field.path

        if field.label is AUTO_LABEL:
            label = format_label(path)
        else:
            label = field.label

        if flatten:
            value = data.get(".".join(path))
        else:
            value = get_path(data, path)

        field_type = resource_schema.get(field.path).type
        value = format_value2(value, field_type, field)
        rows.append((label, value))

    labels = [label for label, _ in rows if label is not None]

    width = max((len(label) for label in labels), default=0)

    for label, value in rows:
        if label is None:
            print(value)
        else:
            print(f"{label:<{width}}  {value}")


def render_object(rows):
    # TODO: implement pretty table
    print(rows)


def render_heading(title: str, skip_newline: bool = False, skip_underline: bool = False):
    if not skip_newline:
        print()
    print(title)
    if not skip_underline:
        print("-" * len(title))


def render_context(context: dict[str, Any] | None):
    if not context:
        return
    sources = context.get("sources", None)
    if sources and len(sources) > 0:
        print()
        print(f"(Data Sources: {", ".join(source.label for source in sources)})")
