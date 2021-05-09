from typing import Optional

import pytest

from pycrastinate import stage, hook, Subscription, set_cache_dir, Result
from pycrastinate import subscription_conditions as cond

from tests.utils.call_counter import CallCounter


@pytest.fixture
def butterflies(tmp_path):
    set_cache_dir(tmp_path)
    call_counter = CallCounter()

    @stage
    def flap_wings(times: int = 1) -> str:
        return " ".join(["flap"] * times)

    @stage
    def stirr_coffee(clockwise: bool) -> str:
        if clockwise:
            return "northern hemisphere"
        else:
            return "southern hemisphere"

    @stage
    def observe_butterfly(
        flapping = Result(flap_wings)
    ):
        return f"It's nothing, just {flapping}"

    values = {}
    flaps_dependency = Subscription(flap_wings, when=cond.COND_DIFFERENT_FROM_LAST)
    hemisphere_depedency = Subscription(
        stirr_coffee, when=cond.COND_DIFFERENT_FROM_LAST, optional=True,
    )

    @hook
    @call_counter
    def wind_maker(
        flaps: str = flaps_dependency,
        hemisphere: Optional[str] = hemisphere_depedency,
    ) -> None:
        if flaps == "flap":
            wind = "mild breeze"
        elif flaps == "flap flap":
            wind = "storm"
        else:
            wind = "apocalyptic hurricane"
        values["wind_maker"] = (wind, hemisphere)

    return (
        (flap_wings, stirr_coffee, observe_butterfly),
        (flaps_dependency, hemisphere_depedency),
        (values, call_counter.counter),
        (wind_maker, call_counter)
    )


def test_hook_only_triggered_with_all(butterflies):
    (
        (flap_wings, stirr_coffee, _),
        (_, hemisphere_depedency),
        (hook_outputs, call_counts),
        _,
    ) = butterflies
    hemisphere_depedency.optional = False

    assert call_counts["wind_maker"] == 0
    stirr_coffee(True)
    assert call_counts["wind_maker"] == 0
    flap_wings()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", "northern hemisphere")}


def test_hook_triggered_once_with_optional(butterflies):
    (
        (flap_wings, _, _), _, (hook_outputs, call_counts), _
    ) = butterflies
    
    assert call_counts["wind_maker"] == 0
    flap_wings()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}


def test_hook_triggered_with_all_optional_second(butterflies):
    (
        (flap_wings, stirr_coffee, _), _, (hook_outputs, call_counts), _
    ) = butterflies

    assert call_counts["wind_maker"] == 0
    flap_wings()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}
    stirr_coffee(False)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("mild breeze", "southern hemisphere")}


def test_hook_triggered_with_correct_results(butterflies):
    (
        (flap_wings, stirr_coffee, _), _, (hook_outputs, call_counts), _
    ) = butterflies

    assert call_counts["wind_maker"] == 0
    flap_wings()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}
    stirr_coffee(False)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("mild breeze", "southern hemisphere")}
    flap_wings(3)
    assert call_counts["wind_maker"] == 3
    assert hook_outputs == {"wind_maker": (
        "apocalyptic hurricane", "southern hemisphere"
    )}
    stirr_coffee(True)
    assert call_counts["wind_maker"] == 4
    assert hook_outputs == {"wind_maker": (
        "apocalyptic hurricane", "northern hemisphere"
    )}


def test_hook_triggered_twice(butterflies):
    (
        (flap_wings, _, _), _, (hook_outputs, call_counts), _
    ) = butterflies
    
    assert call_counts["wind_maker"] == 0
    flap_wings(1)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}
    flap_wings(3)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("apocalyptic hurricane", None)}


# def test_hook_triggered_on_always(butterflies):
    # (
        # (flap_wings, _, _), (flaps_dependency, _), (hook_outputs, call_counts), _
    # ) = butterflies
    # flaps_dependency.when = cond.COND_ALWAYS
    # 
    # assert call_counts["wind_maker"] == 0
    # flap_wings(4)
    # assert call_counts["wind_maker"] == 1
    # assert hook_outputs == {"wind_maker": ("apocalyptic hurricane", None)}
    # flap_wings(4)
    # assert call_counts["wind_maker"] == 2
    # assert hook_outputs == {"wind_maker": ("apocalyptic hurricane", None)}
    # flap_wings(2)
    # assert call_counts["wind_maker"] == 3
    # assert hook_outputs == {"wind_maker": ("storm", None)}


def test_hook_triggered_on_different_from_last(butterflies):
    (
        (flap_wings, _, _), (flaps_dependency, _), (hook_outputs, call_counts), _
    ) = butterflies
    flaps_dependency.when = cond.COND_DIFFERENT_FROM_LAST
    
    assert call_counts["wind_maker"] == 0
    flap_wings(2)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("storm", None)}
    flap_wings(2)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("storm", None)}
    flap_wings(5)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("apocalyptic hurricane", None)}


def test_hook_triggered_on_different_from_any(butterflies):
    (
        (flap_wings, _, _), (flaps_dependency, _), (hook_outputs, call_counts), _
    ) = butterflies
    flaps_dependency.when = cond.COND_DIFFERENT_FROM_ALL
    
    assert call_counts["wind_maker"] == 0
    flap_wings(1)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}
    flap_wings(2)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("storm", None)}
    flap_wings(1)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("storm", None)}
    flap_wings(3)
    assert call_counts["wind_maker"] == 3
    assert hook_outputs == {"wind_maker": ("apocalyptic hurricane", None)}


def modify_hook(hook, call_counter, flaps_dependency, hemisphere_depedency, values):
    @call_counter
    def wind_maker(
        flaps: str = flaps_dependency,
        hemisphere: Optional[str] = hemisphere_depedency,
    ) -> None:
        if flaps == "flap":
            wind = "mildish breeze"
        elif flaps == "flap flap":
            wind = "stormish"
        else:
            wind = "apocalypticish hurricane"
        values["wind_maker"] = (wind, hemisphere)
    hook.hook_func = wind_maker


def test_hook_triggered_on_code_change_with_same_data(butterflies):
    (
        (flap_wings, _, _),
        (flaps_dependency, hemisphere_depedency),
        (hook_outputs, call_counts),
        (wind_maker_hook, call_counter),
    ) = butterflies

    assert call_counts["wind_maker"] == 0
    flap_wings(2)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("storm", None)}
    flap_wings(2)
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("storm", None)}

    modify_hook(
        wind_maker_hook,
        call_counter,
        flaps_dependency,
        hemisphere_depedency,
        hook_outputs,
    )

    flap_wings(2)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("stormish", None)}
    flap_wings(2)
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("stormish", None)}


def test_hook_triggered_when_hooked_to_cached_dependency_and_code_changes(butterflies):
    (
        (_, _, observe_butterfly),
        (flaps_dependency, hemisphere_depedency),
        (hook_outputs, call_counts),
        (wind_maker_hook, call_counter),
    ) = butterflies

    assert call_counts["wind_maker"] == 0
    observe_butterfly()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}
    observe_butterfly()
    assert call_counts["wind_maker"] == 1
    assert hook_outputs == {"wind_maker": ("mild breeze", None)}

    modify_hook(
        wind_maker_hook,
        call_counter,
        flaps_dependency,
        hemisphere_depedency,
        hook_outputs,
    )

    observe_butterfly()
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("mildish breeze", None)}
    observe_butterfly()
    assert call_counts["wind_maker"] == 2
    assert hook_outputs == {"wind_maker": ("mildish breeze", None)}


# TODO: test hooks with dependencies
# TODO: test that if the code of a dependency changes, the hook state also gets
# invalidated
