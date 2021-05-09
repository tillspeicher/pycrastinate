from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import (
    Any,
    Dict,
    Generic,
    TypeVar,
)


R = TypeVar("R")


@dataclass
class BaseInvocation(Generic[R]):
    result: R
    start_time: datetime
    execution_duration: timedelta


@dataclass
class Invocation(BaseInvocation, Generic[R]):
    args: Dict[str, Any]

    def __str__(self) -> str:
        return (
            f"Invocation(data={self.result}, args={self.args})"
        )


@dataclass
class PersistedArg:
    pass
    # arg_hash: bytes


@dataclass
class DataArg(PersistedArg):
    data: Any


@dataclass
class ResultArg(PersistedArg):
    # TODO: should we add a reference to the current Git commit?
    # qualified_stage_name: str

    """The hash used to lookup the result of the stage referenced here.
    This is the hash based on the argument's stage code and arguments."""
    reference_hash: bytes


@dataclass
class FuncArg(PersistedArg):
    # TODO: should we add a reference to the current Git commit?
    # qualified_func_name: str
    recursive_code_hash: bytes


@dataclass
class PersistedInvocation(BaseInvocation):
    args: Dict[str, PersistedArg]
    code_hash: bytes
