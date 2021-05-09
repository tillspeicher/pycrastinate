from typing import Callable
import logging

from .utils.functions import get_full_func_name


logging.getLogger().setLevel(logging.INFO)


def log_stage_exec(stage_func: Callable, executing: bool) -> None:
    exec_info = "Executing" if executing else "Using cached"
    function_name = get_full_func_name(stage_func)
    logging.info(f"{exec_info}: '{function_name}'")


def log_hook_exec(hook_func: Callable) -> None:
    function_name = get_full_func_name(hook_func)
    logging.info(f"Running hook: '{function_name}'")
