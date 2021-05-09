from typing import (
    Any,
    TYPE_CHECKING,
)

from ..stages import R, Invocation 
from .stage_dependency import StageDependency
from .subscription_conditions import CondLiteral, COND_DIFFERENT_FROM_LAST

if TYPE_CHECKING:
    from ..stages import Stage


class SubscriptionDependency(StageDependency):
    def __init__(
        self,
        trigger_stage: "Stage",
        when: CondLiteral,
        optional: bool,
        with_metadata: bool,
    ):
        super().__init__(trigger_stage, with_metadata=with_metadata)

        self.when = when
        self.optional = optional

    def load(self, result_reference: bytes) -> Invocation:
        return self.stage.load_result(result_reference, with_metadata=True)


def Subscription(
    trigger_stage: "Stage",
    when: CondLiteral = COND_DIFFERENT_FROM_LAST,
    optional: bool = False,
    with_metadata: bool = False,
) -> Any:
    return SubscriptionDependency(
        trigger_stage,
        when=when,
        optional=optional,
        with_metadata=with_metadata,
    )
