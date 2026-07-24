from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar, Any
from eskit.resource_type import ResourceType

T = TypeVar("T")


@dataclass
class ResourceTarget:
    resource: ResourceType
    name: str


@dataclass
class Argument:
    name: str
    value: Any


class ResultCode(Enum):
    SUCCESS = auto()
    NOT_FOUND = auto()
    ALREADY_EXISTS = auto()
    INVALID_ARGUMENT = auto()
    CONNECTION_ERROR = auto()
    AUTHENTICATION_ERROR = auto()
    PERMISSION_DENIED = auto()
    TIMEOUT = auto()
    CANCELED = auto()
    INTERNAL_ERROR = auto()
    OPERATION_BLOCKED = auto()


@dataclass
class Result(Generic[T]):
    code: ResultCode
    message: str = ""
    value: T | None = None
    context: Any | None = None

    @property
    def success(self) -> bool:
        return self.code == ResultCode.SUCCESS

    @classmethod
    def ok(cls, value: T | None = None, context: Any | None = None):
        return cls(ResultCode.SUCCESS, value=value, context=context)

    @classmethod
    def fail(
        cls, code: ResultCode, message: str, context: Any | None = None
    ) -> "Result[T]":
        return cls(code=code, message=message, context=context)

    def get_resource_target(self) -> ResourceTarget | None:
        if isinstance(self.context, ResourceTarget):
            return self.context
        return None

    def get_argument(self) -> Argument | None:
        if isinstance(self.context, Argument):
            return self.context
        return None
