from typing import (
    Any,
    Callable,
    Dict,
    Optional,
)
import inspect


def get_full_func_name(func: Callable, max_length: Optional[int] = None) -> str:
    full_name = f"{func.__module__}.{func.__qualname__}"
    if max_length is not None and len(full_name) > max_length:
        full_name = full_name[-max_length:]
    return full_name


def get_arg_default_values(func: Callable) -> Dict[str, Any]:
    signature = inspect.signature(func)
    default_values = {
        arg_name: arg_desc.default
        for arg_name, arg_desc in signature.parameters.items()
        if arg_desc.default != inspect.Parameter.empty
    }
    return default_values
