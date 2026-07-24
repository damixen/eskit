from dataclasses import dataclass
from typing import Iterable
from enum import Enum


class FieldType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    SIZE = "size"
    TEXT = "text"
    LIST = "list"
    DURATION = "duration"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Field:
    path: tuple[str, ...]
    type: FieldType = FieldType.TEXT

    @property
    def dot_path(self) -> str:
        return ".".join(self.path)


@dataclass
class Schema:
    def __init__(self, fields: Iterable[Field]):
        self._fields = list(fields)
        self._field_map = {field.path: field for field in self._fields}

    @property
    def fields(self) -> list[Field]:
        return self._fields

    def get(self, path: tuple[str, ...]) -> Field:
        return self._field_map[path]

    def names(self) -> list[str]:
        return [field.dot_path for field in self._fields]
