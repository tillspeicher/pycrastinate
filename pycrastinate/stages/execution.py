from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
    Union,
    TYPE_CHECKING,
)

from ..args import merge_args
from ..utils.hashing import (
    compute_value_hash,
    compute_code_hash,
    compute_function_dependency_hashes,
)
from ..utils.functions import get_arg_default_values
from ..logging import log_stage_exec
from .persistence import load_stage_result, save_stage_result
from .result import Invocation, PersistedInvocation, R, DataArg, ResultArg, FuncArg

if TYPE_CHECKING:
    from ..utils.arg_aggregation import ArgsAggregationResult


@dataclass
class ExecutionData:
    arg_values: Dict[str, Any]
    non_dependency_hashes: Dict[str, bytes]
    data_dependency_hashes: Dict[str, bytes]
    function_dependency_hashes: Dict[str, bytes]
    result_reference_hashes: Dict[str, bytes]


def prepare_execution(
    aggregated_args: "ArgsAggregationResult",
) -> ExecutionData:
    data_dependency_results = {}
    data_dependency_hashes  = {}
    result_reference_hashes = {}
    for arg_name, dependency in aggregated_args.data_dependencies.items():
        passed_args = aggregated_args.data_dependency_args.get(arg_name, None)
        merged_args = merge_args(dependency.args, passed_args)
        dependency_hash, dependency_result = dependency.resolve(args=merged_args)

        if dependency.with_metadata:
            data_dependency_results[arg_name] = dependency_result
        else:
            data_dependency_results[arg_name] = dependency_result.result

        data_dependency_hashes[arg_name] = compute_value_hash(
            dependency_result.result
        )
        result_reference_hashes[arg_name] = dependency_hash

    arg_values = {
        **aggregated_args.non_dependency_args,
        **aggregated_args.func_dependencies,
        **data_dependency_results,
    }

    non_dependency_hashes = {
        arg_name: compute_value_hash(arg_value)
        for arg_name, arg_value
        in aggregated_args.non_dependency_args.items()
    }
    function_dependency_hashes = compute_function_dependency_hashes(
        aggregated_args.func_dependencies
    )

    return ExecutionData(
        arg_values=arg_values,
        non_dependency_hashes=non_dependency_hashes,
        data_dependency_hashes=data_dependency_hashes,
        function_dependency_hashes=function_dependency_hashes,
        result_reference_hashes=data_dependency_hashes,
    )


def exec_or_load(
    func: Callable[..., R],
    exec_data: ExecutionData,
    results_dir: Path,
) -> Tuple[bytes, Invocation[R]]:
    arg_hashes = {
        **exec_data.non_dependency_hashes,
        **exec_data.data_dependency_hashes,
        **exec_data.function_dependency_hashes,
    }
    code_hash = compute_code_hash(func)
    stage_hash = compute_value_hash((code_hash, arg_hashes))

    cached_result = load_stage_result(results_dir, stage_hash)
    arg_values = exec_data.arg_values
    log_stage_exec(func, cached_result is None)

    if cached_result is not None:
        result = Invocation(
            result=cached_result.result,
            args=arg_values,
            start_time=cached_result.start_time,
            execution_duration=cached_result.execution_duration,
        )
    else:
        result = exec_to_result(func, arg_values)
        data_args = {
            arg_name: DataArg(arg_values[arg_name])
            for arg_name in exec_data.non_dependency_hashes.keys()
        }
        result_args = {
            arg_name: ResultArg(result_reference_hash)
            for arg_name, result_reference_hash
            in exec_data.result_reference_hashes.items()
        }
        function_args = {
            arg_name: FuncArg(func_hash)
            for arg_name, func_hash in exec_data.function_dependency_hashes.items()
        }
        persisted_args = {
            **data_args,
            **result_args,
            **function_args,
        }
        if stage_hash is not None:
            persisted_result = PersistedInvocation(
                result.result,
                args=persisted_args,
                code_hash=code_hash,
                start_time=result.start_time,
                execution_duration=result.execution_duration,
            )
            save_stage_result(results_dir, stage_hash, persisted_result)

    return stage_hash, result


def exec_to_result(
    func: Callable[..., R],
    args: Dict[str, bytes],
) -> Invocation[R]:
    start_time = datetime.now()
    # TODO: submit to a task queue/dict by hash and skip execution if someone
    # else is already doing it
    result_data = func(**args)
    end_time = datetime.now()

    return Invocation(
        result=result_data,
        args=args,
        start_time=start_time,
        execution_duration=(end_time - start_time)
    )


def load_from_reference(
    stage_func: Callable[..., R],
    reference_hash: bytes,
    results_dir: Path,
    with_metadata: bool,
) -> Union[R, Invocation[R]]:
    cached_result = load_stage_result(results_dir, reference_hash)
    if not with_metadata:
        return cached_result.result

    from ..dependencies import ResultDependency, FunctionDependency

    default_values = get_arg_default_values(stage_func)
    arg_values = {}
    for arg_name, persisted_arg in cached_result.args.items():
        if isinstance(persisted_arg, DataArg):
            arg_values[arg_name] = persisted_arg.data
        elif isinstance(persisted_arg, ResultArg):
            arg_dependency = default_values[arg_name]
            if not isinstance(arg_dependency, ResultDependency):
                raise ValueError(
                    f"The default value for arguemnt '{arg_name}' is not a data "
                    "dependency (UseRes()), but this is required to load the cached "
                    "result for this stage."
                )
            arg_value = arg_dependency.stage.load_result(
                persisted_arg.reference_hash, with_metadata=False
            )
            arg_values[arg_name] = arg_value
        elif isinstance(persisted_arg, FuncArg):
            arg_dependency = default_values[arg_name]
            if not isinstance(arg_dependency, FunctionDependency):
                raise ValueError(
                    f"The default value for arguemnt '{arg_name}' is not a function "
                    "dependency (UseFn()), but this is required to load the cached "
                    "result for this stage."
                )
            # TODO: should we check that the function is still the same and indicate
            # that it changed if necessary?
            arg_values[arg_name] = arg_dependency.func
        else:
            raise ValueError(f"Unsupported cached data for argument '{arg_name}'")

    # TODO: should we do an integrity check, i.e. check whether the code hash is
    # still the same and whether the total hash with arguments is the same as the one
    # used to load the data (the reference hash)?
    return Invocation(
        result=cached_result.result,
        args=arg_values,
        start_time=cached_result.start_time,
        execution_duration=cached_result.execution_duration,
    )
