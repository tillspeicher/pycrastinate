from typing import (
    Any,
    Optional,
)


class Args:
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs

    def __str__(self) -> str:
        return (
            f"Args(args={self.args}, kwargs={self.kwargs})"
        )


def merge_args(
    default_args: Args,
    override_args: Optional[Args]
) -> Args:
    if override_args:
        return Args(
            *(override_args.args + default_args.args[len(override_args.args):]),
            **{**default_args.kwargs, **override_args.kwargs},
        )
    else:
        return Args(*default_args.args, **default_args.kwargs)
