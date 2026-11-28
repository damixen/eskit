from typing import Any, overload
from collections import Counter
from dataclasses import dataclass, field

MISSING = object()


@dataclass
class ProjectionStats:
    num_objects: int = 0
    missing_paths: Counter[tuple[str, ...]] = field(default_factory=Counter)

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_objects": self.num_objects,
            "missing_paths": [
                {
                    "path": list(path),
                    "count": count,
                }
                for path, count in self.missing_paths.items()
            ],
        }


def build_field_list(view_config, views, fields) -> list[str] | list[list[str]]:
    """
    Builds a unique list of fields from views and explicit field selections.
    """
    result = []

    for view in views or []:
        result.extend(view_config.get(view, []))

    if fields:
        result.extend(fields.split(","))

    result = [
        list(x) if isinstance(x, tuple) else x
        for x in dict.fromkeys(
            tuple(item) if isinstance(item, list) else item for item in result
        )
    ]

    return result


def normalize_projection(fields: list[str] | list[list[str]]):
    result = []

    seen = set()

    for field in fields:
        normalized_path = normalize_path(field)
        if normalized_path in seen:
            continue

        seen.add(normalized_path)
        result.append(normalized_path)

    return result


def normalize_path(path: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:

    result = None
    if isinstance(path, str):
        result = tuple(path.split("."))
    else:
        result = tuple(path)

    result = tuple(item.replace("$", ".") for item in result)

    return result


def get_path(
    data,
    path: tuple[str, ...],
    default: Any = None,
):
    current = data

    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default

        current = current[part]

    return current


def set_path(data, path: tuple[str, ...], value):

    current = data

    for part in path[:-1]:
        part = part.replace("$", ".")

        if part not in current:
            current[part] = {}

        current = current[part]

    current[path[-1]] = value


@overload
def project(
    value: dict[str, Any],
    paths: list[tuple[str, ...]],
    flatten: bool = False,
) -> dict[str, Any]: ...


@overload
def project(
    value: list[dict[str, Any]],
    paths: list[tuple[str, ...]],
    flatten: bool = False,
) -> list[dict[str, Any]]: ...


def project(
    value: dict[str, Any] | list[dict[str, Any]],
    paths: list[tuple[str, ...]],
    flatten: bool = False,
    *,
    projection_stats: ProjectionStats | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:

    if isinstance(value, list):
        return project_list(value, paths, flatten, projection_stats=projection_stats)

    return project_object(value, paths, flatten, projection_stats=projection_stats)


def project_list(
    value: list[dict[str, Any]],
    paths: list[tuple[str, ...]],
    flatten: bool = False,
    *,
    projection_stats: ProjectionStats | None = None,
) -> list[dict[str, Any]]:

    return [
        project_object(item, paths, flatten, projection_stats=projection_stats)
        for item in value
    ]


def project_object(
    value: dict[str, Any],
    paths: list[tuple[str, ...]],
    flatten: bool = False,
    *,
    projection_stats: ProjectionStats | None = None,
) -> dict[str, Any]:

    out: dict[str, Any] = {}

    if projection_stats is not None:
        projection_stats.num_objects += 1

    for path in paths:

        field_value = get_path(value, path, default=MISSING)

        is_missing = field_value is MISSING

        if projection_stats is not None:
            projection_stats.missing_paths[path] += int(is_missing)

        if flatten:
            out[".".join(path)] = None if is_missing else field_value
        elif not is_missing and field_value is not None:
            set_path(out, path, field_value)

    return out
