from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Union,
    Tuple,
)
import functools

from ..args import Args
from ..config import get_cache_dir
from .result import Invocation, R


class Stage(Generic[R]):
    def __init__(
        self,
        stage_func: Callable[..., R],
        cache_dir: Optional[Path] = None,
    ) -> None:
        functools.update_wrapper(self, stage_func)
        self.stage_func: Callable[..., R] = stage_func
        self._cache_dir = cache_dir

        self._hook_callbacks: List[
            Callable[[bytes, Invocation[R]], None]
        ] = []

    @property
    def cache_dir(self) -> Path:
        return (
            self._cache_dir
            if self._cache_dir is not None
            else get_cache_dir()
        )

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Union[R, Invocation[R]]:
        _, result = self.compute_or_load_result(Args(*args, **kwargs))
        return result.result

    def register_hook(
        self,
        result_callback: Callable[[bytes, Invocation[R]], None]
    ) -> None:
        self._hook_callbacks.append(result_callback)

    def compute_or_load_result(self, args: Args) -> Tuple[bytes, Invocation[R]]:
        from ..utils.arg_aggregation import aggregate_args
        from .execution import prepare_execution, exec_or_load

        # TODO: can we just compute the aggregated args once, and then merge
        # them with `args` on execution?
        aggregated_args = aggregate_args(self.stage_func, args)
        execution_data = prepare_execution(aggregated_args)

        stage_hash, result = exec_or_load(
            self.stage_func,
            exec_data=execution_data,
            results_dir=self.cache_dir,
        )
        self._run_hooks(stage_hash, result)
        return stage_hash, result

    def _run_hooks(
        self,
        result_reference: bytes,
        result: Invocation,
    ) -> None:
        # if result_reference is None or result is None:
            # # There aren't any new results but the hook code might have changed
            # # so we need to check whether we should rerun the hooks
            # from ..utils.arg_aggregation import aggregate_args
# 
            # aggregated_args = aggregate_args(self.stage_func)
            # for data_dependency in aggregated_args.data_dependencies.values():
                # data_dependency.stage._run_hooks()

        # TODO: push the results to task pool/queue instead
        for result_callback in self._hook_callbacks:
            result_callback(result_reference, result)

    def load_result(
        self, reference_hash: bytes, with_metadata: bool
    ) -> Union[R, Invocation[R]]:
        from .execution import load_from_reference

        # TODO: handle missing and inconsistent data
        return load_from_reference(
            self.stage_func, reference_hash, self.cache_dir, with_metadata
        )

def stage(
    func: Callable[..., R],
) -> Stage[R]:
    return Stage(func)

# @overload
# def stage(_func: Callable[..., T]) -> Stage[T]:
    # ...
# @overload
# def stage() -> Callable[[Callable[..., T]], Stage[T]]:
    # ...
# def stage(
    # _func = None,
    # # *,
    # # results_dir: Union[str, Path] = "./.results",
# # ) -> Callable[..., T]:
# ):
    # def stage_decorator(func: Callable[..., T]) -> Callable[..., T]:
        # return Stage(func, results_dir=Path(results_dir))
    # # if _func is None:
        # # return functools.partial(stage, results_dir=results_dir)
# 
    # # return Stage(_func, results_dir=results_dir)
    # if _func is None:
        # return stage_decorator
    # else:
        # return stage_decorator(_func)
