from typing import (
    Any,
    Callable,
    Generic,
    Optional,
)

from ..utils.hashing import compute_code_hash, compute_value_hash
from ..utils.arg_aggregation import aggregate_args
from ..stages import R


class FunctionDependency(Generic[R]):
    def __init__(
        self,
        func: Callable[..., R],
    ) -> None:
        self.func = func

        # TODO: caching is disabled right now to 
        self._has_no_data_dependencies: Optional[bool] = None
        self._recursive_code_hash: Optional[bytes] = None

    def __call__(self, *args: Any, **kwargs: Any) -> R:
        # TODO: pass results dir
        return self.func(*args, **kwargs)

    def has_no_data_dependencies(self) -> bool:
        """
        Recursively checks whether a function dependency has no data dependencies
        somewhere in it's dependency graph.
        Stages with function dependencies that don't have (recursive) data
        dependencies can use caching.
        """
        # if self._has_no_data_dependencies is not None:
            # # Already resolved
            # return self._has_no_data_dependencies

        dependency_args = aggregate_args(self.func)
        if len(dependency_args.data_dependencies) > 0:
            self._has_no_data_dependencies = False
        else:
            self._has_no_data_dependencies = all(
                func_dependency.has_no_data_dependencies()
                for func_dependency in dependency_args.func_dependencies.values()
            )
        return self._has_no_data_dependencies

    def get_recursive_hash(self) -> bytes:
        # assert self.has_no_data_dependencies()

        # if self._recursive_code_hash is not None:
            # return self._recursive_code_hash

        from ..stages import Stage
        func = self.func.stage_func if isinstance(self.func, Stage) else self.func

        code_hash = compute_code_hash(func)
        dependency_args = aggregate_args(func)
        dependency_hashes = {
            arg_name: func_dependency.get_recursive_hash()
            for arg_name, func_dependency in dependency_args.func_dependencies.items()
        }

        self._recursive_code_hash = compute_value_hash((code_hash, dependency_hashes))
        return self._recursive_code_hash


def Use(func: Callable[..., R]) -> FunctionDependency[R]:
    return FunctionDependency(func)
