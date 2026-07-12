from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar

T = TypeVar("T")


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


@dataclass
class Result(Generic[T]):
    code: ResultCode
    message: str = ""
    value: T | None = None

    @property
    def success(self) -> bool:
        return self.code == ResultCode.SUCCESS

    @classmethod
    def ok(cls, value: T | None = None):
        return cls(ResultCode.SUCCESS, value=value)

    @classmethod
    def fail(
        cls,
        code: ResultCode,
        message: str,
        value: T | None = None,
    ) -> "Result[T]":
        return cls(code=code, message=message, value=value)
