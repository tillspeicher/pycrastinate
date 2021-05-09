import pytest

from pycrastinate import stage, Result, Args, set_cache_dir

from tests.utils.call_counter import CallCounter


@pytest.fixture
def cooking_session(tmp_path):
    set_cache_dir(tmp_path)
    call_counter = CallCounter()

    @stage
    @call_counter
    def stack_ingredients(sauce: str) -> str:
        return sauce

    @stage
    @call_counter
    def bake_lasagne(
        extra_cross: bool = False,
        ingredients=Result(stack_ingredients, Args(sauce="Bolognese"))
    ) -> str:
        return ("extra cross " if extra_cross else "") + f"Lasagna {ingredients}"

    @stage
    @call_counter
    def make_salad(with_olives: bool = False) -> str:
        return "caesar salad" + (" with olives" if with_olives else "")

    @stage
    @call_counter
    def prepare_dinner(
        lasagna=Result(bake_lasagne),
        salad=Result(make_salad),
    ) -> str:
        return f"{lasagna} with {salad}"

    @stage
    @call_counter
    def clean_apartment() -> str:
        return "nice and shiny"

    return prepare_dinner, call_counter.counter


def test_run_all_dependencies(cooking_session):
    prepare_dinner, call_counts = cooking_session
    result = prepare_dinner()
    assert result == "Lasagna Bolognese with caesar salad"
    assert call_counts["stack_ingredients"] == 1
    assert call_counts["bake_lasagne"] == 1
    assert call_counts["make_salad"] == 1
    assert call_counts["prepare_dinner"] == 1
    assert call_counts["clean_apartment"] == 0


def test_override_args(cooking_session):
    prepare_dinner, call_counts = cooking_session
    result = prepare_dinner(
        lasagna=Args(True, ingredients=Args(sauce="Ricotta")),
        salad=Args(with_olives=True),
    )
    assert result == "extra cross Lasagna Ricotta with caesar salad with olives"
    assert call_counts["stack_ingredients"] == 1
    assert call_counts["bake_lasagne"] == 1
    assert call_counts["make_salad"] == 1
    assert call_counts["prepare_dinner"] == 1
    assert call_counts["clean_apartment"] == 0


def test_return_metadata(cooking_session):
    prepare_dinner, call_counts = cooking_session
    result = prepare_dinner(metadata=True)


def test_override_results_dir(cooking_session):
    pass
