import inspect
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
)

from ..args import Args


class ArgsAggregationResult:
    # We can't use a dataclass here because we need to use deferred imports
    def __init__(self):
        from ..dependencies import ResultDependency
        from ..dependencies import FunctionDependency

        self.non_dependency_args: Dict[str, Any] = {}
        self.data_dependencies: Dict[str, ResultDependency] = {}
        self.data_dependency_args: Dict[str, Args] = {}
        self.func_dependencies: Dict[str, FunctionDependency] = {}

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ArgsAggregationResult):
            return False
        return (
            self.non_dependency_args == other.non_dependency_args
            and self.data_dependencies == other.data_dependencies
            and self.data_dependency_args == other.data_dependency_args
            and self.func_dependencies == other.func_dependencies
        )


def aggregate_args(
    func: Callable, args: Optional[Args] = None
) -> ArgsAggregationResult:
    from ..dependencies import ResultDependency
    from ..dependencies import FunctionDependency

    aggregation_result = ArgsAggregationResult()

    signature = inspect.signature(func)
    arg_pos = -1
    for arg_name, arg_desc in signature.parameters.items():
        arg_pos += 1
        if args and arg_pos < len(args.args):
            # The argument was provided as a positional parameter
            arg_value = args.args[arg_pos]
            arg_set = True
        elif args and arg_name in args.kwargs:
            # The argument was provided as a named parameter
            arg_value = args.kwargs[arg_name]
            arg_set = True
        else:
            arg_value = None
            arg_set = False

        if arg_set and isinstance(arg_value, ResultDependency):
            raise ValueError(
                "Argument of result dependency type (UseRes()) passed as value "
                f"for parameter '{arg_name}' "
                "but result dependency arguments are only supported as default values "
                "via 'UseRes()'."
            )
        elif arg_set and isinstance(arg_value, FunctionDependency):
            raise ValueError(
                "Argument of function dependency type (UseFn()) passed as value "
                f"for parameter '{arg_name}' "
                "but function dependency arguments are only supported as default "
                "values via 'UseFn()'."
            )
        elif arg_set and isinstance(arg_value, Args) and (
            arg_desc.default is inspect.Parameter.empty
            or not isinstance(arg_desc.default, ResultDependency)
        ):
            raise ValueError(
                f"Passed argument of type 'Args' to parameter '{arg_name}' "
                f"but '{arg_name}' is not declared as data dependency (UseRes())."
                f"instead: {type(arg_desc.default)}"
            )

        if arg_set:
            if isinstance(arg_value, Args):
                aggregation_result.data_dependency_args[arg_name] = arg_value
            else:
                aggregation_result.non_dependency_args[arg_name] = arg_value

        if (
            arg_desc.default is not inspect.Parameter.empty
            # Don't override the actual with the default arguments
            and (not arg_set or isinstance(arg_value, Args))
        ):
            default_value = arg_desc.default
            if isinstance(default_value, ResultDependency):
                aggregation_result.data_dependencies[arg_name] = default_value
            elif isinstance(default_value, FunctionDependency):
                aggregation_result.func_dependencies[arg_name] = default_value
            # TODO: make sure that default Args arguments don't overwrite passed ones
            else:
                aggregation_result.non_dependency_args[arg_name] = default_value

    return aggregation_result
