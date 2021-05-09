import functools
from typing import Callable


class CallCounter:
    def __init__(self) -> None:
        self.counter = {}

    def __call__(self, func: Callable) -> Callable:
        if not func.__name__ in self.counter:
            self.counter[func.__name__] = 0

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            self.counter[func.__name__] += 1
            return func(*args, **kwargs)
        return func_wrapper
