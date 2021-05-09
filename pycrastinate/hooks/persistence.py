from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Optional,
    Set,
)

from ..utils.hashing import compute_code_hash, compute_value_hash
from ..utils.functions import get_full_func_name
from ..utils.persistence import save_object, load_object


@dataclass
class HookArgumentState:
    # last_result_reference is used to load the last result and
    # last_executed_result_reference is used to evaluate whether the current result
    # is different from the last one
    result_lookup_reference: Optional[bytes] = None
    last_executed_result_reference: Optional[bytes] = None
    all_executed_result_references: Set[bytes] = field(default_factory=set)


@dataclass
class HookState:
    code_hash: Optional[bytes] = None
    arg_states: Dict[str, HookArgumentState] = field(default_factory=dict)

    def update_code_hash(
        self,
        hook_func: Callable,
        code_dependency_hashes: Dict[str, bytes],
    # ) -> Optional[Dict[str, bytes]]:
    ) -> bool:
        hook_hash = compute_code_hash(hook_func)
        code_hash = compute_value_hash((hook_hash, code_dependency_hashes))

        prev_code_hash = self.code_hash
        self.code_hash = code_hash

        if prev_code_hash is not None and prev_code_hash != code_hash:
            for arg_state in self.arg_states.values():
                arg_state.last_executed_result_reference = None
                arg_state.all_executed_result_references.clear()

        return prev_code_hash != code_hash

    def record_triggered(
        self,
        arg_name: str,
        arg_result_hash: bytes,
    ) -> None:
        arg_state = self.arg_states.setdefault(arg_name, HookArgumentState())
        arg_state.result_lookup_reference = arg_result_hash
        arg_state.last_executed_result_reference = arg_result_hash
        arg_state.all_executed_result_references.add(arg_result_hash)


HOOK_STATES_DIR_NAME = "hook_states"
MAX_FUNC_NAME_LENGTH = 255 # Max file name length on most file systems


def _get_hook_state_path(cache_dir: Path, hook_func: Callable) -> Path:
    qualified_hook_name = get_full_func_name(hook_func, MAX_FUNC_NAME_LENGTH)
    return cache_dir / HOOK_STATES_DIR_NAME / qualified_hook_name


def load_hook_state(cache_dir: Path, hook_func: Callable) -> HookState:
    hook_state_file = _get_hook_state_path(cache_dir, hook_func)
    hook_state: Optional[HookState] = load_object(hook_state_file)

    if hook_state is None:
        hook_state = HookState()

    return hook_state


def save_hook_state(
    results_dir: Path,
    hook_func: Callable,
    hook_state: HookState,
) -> None:
    hook_state_file = _get_hook_state_path(results_dir, hook_func)
    save_object(hook_state_file, hook_state)
