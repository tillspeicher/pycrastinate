from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..stages import Stage


class StageDependency:
    def __init__(self, stage: "Stage", with_metadata: bool) -> None:
        from ..stages import Stage
        if not isinstance(stage, Stage):
            raise ValueError("Trigger dependencies must be stages")

        self.stage = stage
        self.with_metadata = with_metadata
