import inspect
import functools
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Generic,
    Optional,
    Union,
    TypeVar,
)

from ..dependencies import SubscriptionDependency, FunctionDependency
from ..dependencies import subscription_conditions
from ..utils.hashing import compute_function_dependency_hashes
from ..stages import Invocation, R
from ..config import get_cache_dir
from ..logging import log_hook_exec
from . import persistence


T = TypeVar("T")


# def cond_each_call(*_) -> bool:
    # return True
# 
# def cond_each_exec(_, __, arg_result_hash: Optional[bytes]) -> bool:
    # return arg_result_hash is not None

def cond_different_from_last(
    hook_state: persistence.HookState, arg_name: str, arg_result_hash: Optional[bytes]
) -> bool:
    if arg_result_hash is None:
        return False
    arg_state = hook_state.arg_states.get(arg_name, None)
    return (
        arg_state is None
        or arg_state.last_executed_result_reference!= arg_result_hash
    )

def cond_different_from_all(
    hook_state: persistence.HookState, arg_name: str, arg_result_hash: Optional[bytes]
) -> bool:
    if arg_result_hash is None:
        return False
    arg_state = hook_state.arg_states.get(arg_name, None)
    return (
        arg_state is None
        or arg_result_hash not in arg_state.all_executed_result_references
    )

TRIGGER_CONDITIONS: Dict[str, Callable] = {
    # subscription_conditions.COND_EACH_CALL: cond_each_call,
    # subscription_conditions.COND_EACH_EXEC: cond_each_exec,
    subscription_conditions.COND_DIFFERENT_FROM_LAST: cond_different_from_last,
    subscription_conditions.COND_DIFFERENT_FROM_ALL: cond_different_from_all,
}


class Hook(Generic[T]):
    def __init__(
        self,
        hook_func: Callable[..., T],
        cache_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.hook_func = hook_func
        self._cache_dir = Path(cache_dir) if cache_dir is not None else None

        self._subscription_dependencies: Dict[str, SubscriptionDependency] = {}
        self._function_dependency_hashes: Dict[str, bytes] = {}

        self._parse_dependencies()
        # Execute the hook in case its code or that of a dependency changed
        # self._check_code_changed()

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir if self._cache_dir is not None else get_cache_dir()

    # TODO: could the underlying functions change after initialization?
    # i.e. might it be necessary to rerun this function?
    def _parse_dependencies(self) -> None:
        signature = inspect.signature(self.hook_func)
        function_dependencies = {}

        for arg_name, arg_desc in signature.parameters.items():
            if arg_desc.default is inspect.Parameter.empty:
                raise ValueError(
                    f"No default value provided for hook parameter '{arg_name}'. "
                    "All arguments of a hook must have default values defined using "
                    "'Subscribe()' or 'Use()'"
                )

            # TODO: should we allow result dependencies as well?
            elif isinstance(arg_desc.default, SubscriptionDependency):
                self._subscription_dependencies[arg_name] = arg_desc.default

            elif isinstance(arg_desc.default, FunctionDependency):
                function_dependencies[arg_name] = arg_desc.default

            else:
                raise ValueError(
                    f"Default value provided for hook parameter '{arg_name}' is not "
                    "a trigger dependency. "
                    "All arguments of a hook must have default values defined using "
                    "'Subscribe()' or 'Use()'"
                )

        self._register_with_trigger_funcs()
        self._function_dependency_hashes = compute_function_dependency_hashes(
            function_dependencies
        )

    def _register_with_trigger_funcs(self) -> None:
        for arg_name, subscription in self._subscription_dependencies.items():
            execute_arg_hook = functools.partial(self._execute_hook, arg_name)
            subscription.stage.register_hook(execute_arg_hook)

    def _execute_hook(
        self,
        triggering_arg_name: str,
        triggering_result_hash: bytes,
        triggering_result: Invocation,
    ) -> Optional[T]:
        hook_state = persistence.load_hook_state(self.cache_dir, self.hook_func)
        hook_state.update_code_hash(
            self.hook_func, self._function_dependency_hashes
        )
        subscription_results = self._get_missing_subscription_data(
            hook_state,
            triggering_arg_name,
            triggering_result_hash,
            triggering_result,
        )

        persistence.save_hook_state(self.cache_dir, self.hook_func, hook_state)
        if subscription_results is None:
            return None
        log_hook_exec(self.hook_func)

        call_data = _convert_metadata(
            self._subscription_dependencies, subscription_results
        )
        return self.hook_func(**call_data)

    def _get_missing_subscription_data(
        self,
        hook_state: persistence.HookState,
        triggering_arg_name: str,
        triggering_result_hash: bytes,
        triggering_result: Invocation,
    ) -> Optional[Dict[str, Optional[Invocation]]]:
        trigger = self._subscription_dependencies[triggering_arg_name]
        trigger_condition_type = trigger.when
        trigger_condition = TRIGGER_CONDITIONS[trigger_condition_type]
        is_triggered = trigger_condition(
            hook_state, triggering_arg_name, triggering_result_hash
        )

        hook_state.record_triggered(triggering_arg_name, triggering_result_hash)
        if not is_triggered:
            return None 

        missing_result_subscriptions = {
            arg_name: trigger
            for arg_name, trigger in self._subscription_dependencies.items()
            if arg_name != triggering_arg_name
        }
        missing_result_references = _get_missing_result_references(
            hook_state, missing_result_subscriptions
        )

        if missing_result_references is None:
            missing_results = None
        else:
            missing_results = _load_missing_results(
                missing_result_subscriptions, missing_result_references
            )

        if missing_results is None:
            # Results for non-optional dependencies are missing, skip hook execution
            return None
        else:
            return {
                triggering_arg_name: triggering_result, **missing_results
            }


def hook(func: Callable[..., T]) -> Hook[T]:
    return Hook[T](func)


def _get_missing_result_references(
    hook_state: persistence.HookState,
    subscriptions: Dict[str, SubscriptionDependency],
) -> Optional[Dict[str, Optional[bytes]]]:
    result_references = {}
    for arg_name, trigger_dependency in subscriptions.items():
        arg_state = hook_state.arg_states.get(arg_name, None)
        if arg_state is None or arg_state.result_lookup_reference is None:
            if trigger_dependency.optional:
                result_references[arg_name] = None
            else:
                return None
        else:
            result_references[arg_name] = arg_state.result_lookup_reference
    return result_references


def _load_missing_results(
    subscriptions: Dict[str, SubscriptionDependency],
    result_references: Dict[str, Optional[bytes]],
) -> Optional[Dict[str, Optional[Invocation]]]:
    results = {}
    for arg_name, subscription in subscriptions.items():
        arg_reference: Optional[bytes] = result_references.get(arg_name)
        if arg_reference is None:
            arg_result = None
        else:
            arg_result = subscription.load(arg_reference)

        if arg_result is None:
            if subscription.optional:
                results[arg_name] = None
            else:
                return None
        else:
            results[arg_name] = arg_result
    return results


def _convert_metadata(
    subscriptions: Dict[str, SubscriptionDependency],
    result_data: Dict[str, Optional[Invocation[R]]],
) -> Dict[str, Optional[Union[R, Invocation[R]]]]:
    res = {
        arg_name: (
            (data if subscriptions[arg_name].with_metadata else data.result)
            if data is not None else None
        )
        for arg_name, data in result_data.items()
    }
    return res
