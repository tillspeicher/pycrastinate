from typing import Literal


# COND_EACH_CALL = "each_call"
# COND_EACH_EXEC = "each_exec"
COND_DIFFERENT_FROM_LAST = "different_from_last"
COND_DIFFERENT_FROM_ALL = "different_from_all"

CondLiteral = Literal[
    # COND_EACH_CALL,
    # COND_EACH_EXEC,
    COND_DIFFERENT_FROM_LAST,
    COND_DIFFERENT_FROM_ALL,
]
