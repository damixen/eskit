from typing import Any, cast
from datetime import datetime, timedelta
from enum import Enum
from collections.abc import Callable
from eskit.resource.schema import FieldType
from eskit.render.display_fields import DisplayField, AUTO_LABEL
import re

SIZE_RE = re.compile(r"^\s*([\d.]+)\s*([kmgtp]?b)?\s*$", re.IGNORECASE)

MULTIPLIERS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
    "pb": 1024**5,
}


class FormatType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    SIZE = "size"

    def __str__(self):
        return self.value


def format_boolean(value: Any) -> str:
    return "Yes" if value else "No"


def format_integer(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def format_size(value: int | str | None) -> str:
    if value is None:
        return "-"

    # Already numeric
    if isinstance(value, int):
        size = float(value)

    elif isinstance(value, str):
        # Pure integer string
        if value.isdigit():
            size = float(value)
        else:
            match = SIZE_RE.match(value)
            if not match:
                return value  # Unknown format, leave unchanged

            number = float(match.group(1))
            unit = (match.group(2) or "b").lower()
            size = number * MULTIPLIERS[unit]

    else:
        return str(value)

    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size):,} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return str(value)


def format_label(path_parts: tuple[str, ...]) -> str:
    words = []

    for part in path_parts:
        words.extend(part.replace("_", " ").replace("-", " ").replace(".", " ").split())

    return " ".join(word.capitalize() for word in words)


def format_datetime(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    dt = dt.astimezone()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_value(
    value,
    fmt: FormatType | None,
):
    if value is None:
        return ""

    if fmt is None:
        return value

    formatter = FORMATTERS.get(fmt)

    if formatter is None:
        return value

    return formatter(value)


def format_list_preview(values, preview=2):
    if not values:
        return ""

    count = len(values)

    noun = "index" if count == 1 else "indices"

    if count <= preview:
        preview_text = ", ".join(values)
    else:
        preview_text = ", ".join(values[:preview]) + ", ..."

    return f"({count} {noun}) {preview_text}"


def format_list(value: list[str], indent: int = 0, preview: bool | None = False) -> str:
    if not value:
        return ""

    if preview:
        return format_list_preview(value, 2)

    prefix = " " * indent

    return "\n".join(f"{prefix}{item}" for item in value)


def format_value2(value, fmt: FieldType | None, display_field: DisplayField):
    if value is None:
        return ""

    if fmt is None:
        return value

    if fmt is FieldType.LIST:
        return format_list(value, preview=display_field.preview)

    formatter = FORMATTERS2.get(fmt)

    if formatter is None:
        return value

    return formatter(value)


def format_duration(milliseconds: int) -> str:
    """
    Format a duration in milliseconds into a human-readable string.

    Examples:
        350        -> "350 ms"
        9213       -> "9.2 s"
        16411      -> "16.4 s"
        75432      -> "1m 15s"
        3723000    -> "1h 2m 3s"
    """
    if milliseconds < 1000:
        return f"{milliseconds:,} ms"

    td = timedelta(milliseconds=milliseconds)

    total_seconds = int(td.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds}s"

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{milliseconds / 1000:.1f} s"


def resolve_label(field: DisplayField) -> str | None:
    if field.label is AUTO_LABEL:
        return format_label(field.path)
    return cast(str | None, field.label)


Formatter = Callable[[Any], str]

FORMATTERS: dict[FormatType, Formatter] = {
    FormatType.BOOLEAN: format_boolean,
    FormatType.INTEGER: format_integer,
    FormatType.SIZE: format_size,
    FormatType.DATETIME: format_datetime,
}

FORMATTERS2: dict[FieldType, Formatter] = {
    FieldType.BOOLEAN: format_boolean,
    FieldType.INTEGER: format_integer,
    FieldType.SIZE: format_size,
    FieldType.DATETIME: format_datetime,
    FieldType.LIST: format_list,
    FieldType.DURATION: format_duration,
}
