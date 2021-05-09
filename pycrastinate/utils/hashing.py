import ast
import hashlib
from typing import (
    Any,
    Callable,
    Dict,
    TYPE_CHECKING,
)
import inspect
import os

from .encoding import encode

if TYPE_CHECKING:
    from ..dependencies import FunctionDependency


def compute_value_hash(value: Any) -> bytes:
    serialized_value = encode(value)
    hash = hashlib.sha256(serialized_value)
    return hash.digest()


def _strip_whitespace_prefixes(func_code: str) -> str:
    """
    Strips the longest share whitespace prefix among multiple lines of code.
    Without doing this, the ast.parse() method will not accept nested function
    definitions.
    """
    code_lines = func_code.split("\n")
    longest_common_prefix = code_lines[0] if len(code_lines) > 0 else ""
    for line in code_lines:
        for length in range(1, min(len(longest_common_prefix), len(line))):
            if (
                not line[:length].isspace()
                or line[:length] != longest_common_prefix[:length]
            ):
                longest_common_prefix = line[:length - 1]
                break

    stripped_lines = [line[len(longest_common_prefix):] for line in code_lines]
    return "\n".join(stripped_lines)


OVERRIDE_FUNCTION_NAME = "_fn_"


def compute_code_hash(func: Callable) -> bytes:
    # Parse the function code to obtain a normalized representation
    # that is not dependent on comments, whitespace, etc.
    func_code = inspect.getsource(func)
    stripped_func_code = _strip_whitespace_prefixes(func_code)
    code_ast = ast.parse(stripped_func_code, mode="exec", type_comments=False)

    # Set the function name to a generic one to avoid invalidating the cache when
    # the function is renamed.
    func_def = code_ast.body[0] if len(code_ast.body) == 1 else None
    if func_def is None or not isinstance(func_def, ast.FunctionDef):
        raise ValueError("Invalid function passed for code hashing")

    func_def.name = OVERRIDE_FUNCTION_NAME
    # TODO: normalize variable and argument names as well by setting them to generic
    # names

    # Convert the AST object back to a (normalized) string for hashing
    normalized_code = ast.unparse(func_def)

    encoded_code = bytes(normalized_code, "utf-8")
    hash = hashlib.sha256(encoded_code)
    return hash.digest()


def compute_function_dependency_hashes(
    function_dependencies: Dict[str, "FunctionDependency"]
) -> Dict[str, bytes]:
    return {
        arg_name: func_dependency.get_recursive_hash()
        for arg_name, func_dependency
        in function_dependencies.items()
    }
