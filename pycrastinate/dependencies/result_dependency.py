from typing import (
    Any,
    Generic,
    TYPE_CHECKING,
    Tuple,
)

from ..args import Args
from ..stages import Invocation, R
from .stage_dependency import StageDependency

if TYPE_CHECKING:
    from ..stages import Stage


class ResultDependency(StageDependency, Generic[R]):
    def __init__(
        self,
        stage: "Stage",
        args: Args = Args(),
        with_metadata: bool = False,
    ) -> None:
        super().__init__(stage, with_metadata=with_metadata)

        self.args = args

        self._check_cachable()

    def __str__(self) -> str:
        return (
            f"Result({self.stage.stage_func.__name__}, args={self.args}, "
            f"with_metadata={self.with_metadata})"
        )

    def _check_cachable(self) -> None:
        from ..utils.arg_aggregation import aggregate_args
        aggregated_args = aggregate_args(self.stage.stage_func)
        for arg_name, func_dependency in aggregated_args.func_dependencies.items():
            if not func_dependency.has_no_data_dependencies():
                raise ValueError(
                    f"Function dependency {arg_name} has (recursive) data "
                    "dependencies (UseData()). Recursive data dependencies of "
                    "function dependencies prevent stages from using caching. "
                    "Either do not mark this function as stage or remove the "
                    "recursive data dependencies."
                )

    def resolve(
        self,
        args: Args,
    ) -> Tuple[bytes, Invocation[R]]:
        """
        Checks whether there is already a result for this stage with this
        configuration and returns it if there is.
        Otherwise the stage is executed.
        Checks recursively for other stages whether they need to be executed.
        """
        return self.stage.compute_or_load_result(args)


def Result(
    stage_func: "Stage",
    args: Args = Args(),
    with_metadata=False,
) -> Any:
    return ResultDependency(
        stage_func,
        args=args,
        with_metadata=with_metadata,
    )
