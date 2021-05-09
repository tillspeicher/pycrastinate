import pytest

from pycrastinate import stage, Result, Args, set_cache_dir

from .utils.call_counter import CallCounter


@pytest.fixture
def roadtrip_planning(tmp_path):
    set_cache_dir(tmp_path)
    call_counter = CallCounter()

    @stage
    @call_counter
    def figure_out_num_people(is_josie_in: bool = False):
        if is_josie_in:
            return 4
        else:
            return 3

    @stage
    @call_counter
    def make_supply_list(
        num_people=Result(figure_out_num_people, Args(is_josie_in=False))
    ):
        return [
            f"Buy {num_people * 4} chips packages",
            "Get TimTams",
        ]

    @stage
    @call_counter
    def find_accomodation(
        num_people=Result(figure_out_num_people)
    ):
        return [f"Check availability for {num_people}"]

    @stage
    @call_counter
    def plan_car_booking(num_drivers=2):
        return [
            "Determine distance",
            f"Compare prices for {num_drivers} drivers",
        ]

    supply_planning_dependency = Result(
        make_supply_list, Args(num_people=Args(is_josie_in=False))
    )

    @stage
    @call_counter
    def plan_roadtrip(
        supply_planning=supply_planning_dependency,
        accomodation_booking=Result(find_accomodation),
        car_booking=Result(plan_car_booking),
    ):
        return supply_planning + accomodation_booking + car_booking

    return (
        plan_roadtrip, call_counter.counter, (
            call_counter, figure_out_num_people, supply_planning_dependency
        )
    )


def test_cache_used_no_changes(roadtrip_planning):
    plan_roadtrip, call_counts, _ = roadtrip_planning
    result_1 = plan_roadtrip()
    result_2 = plan_roadtrip()

    assert result_1 == result_2
    assert result_1 == [
        "Buy 12 chips packages",
        "Get TimTams",
        "Check availability for 3",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert call_counts["figure_out_num_people"] == 1
    assert call_counts["make_supply_list"] == 1
    assert call_counts["find_accomodation"] == 1
    assert call_counts["plan_car_booking"] == 1
    assert call_counts["plan_roadtrip"] == 1


def test_cache_used_unchanged_arguments(roadtrip_planning):
    plan_roadtrip, call_counts, _ = roadtrip_planning
    result_1 = plan_roadtrip(
        supply_planning=Args(num_people=Args(is_josie_in=True)),
        accomodation_booking=Args(num_people=Args(is_josie_in=True)),
        car_booking=Args(num_drivers=3),
    )
    result_2 = plan_roadtrip(
        supply_planning=Args(num_people=Args(is_josie_in=True)),
        accomodation_booking=Args(num_people=Args(is_josie_in=True)),
        car_booking=Args(num_drivers=3),
    )

    assert result_1 == result_2
    assert result_1 == [
        "Buy 16 chips packages",
        "Get TimTams",
        "Check availability for 4",
        "Determine distance",
        "Compare prices for 3 drivers",
    ]
    assert call_counts["figure_out_num_people"] == 1
    assert call_counts["make_supply_list"] == 1
    assert call_counts["find_accomodation"] == 1
    assert call_counts["plan_car_booking"] == 1
    assert call_counts["plan_roadtrip"] == 1


def test_result_recomputed_on_argument_change(roadtrip_planning):
    plan_roadtrip, call_counts, _ = roadtrip_planning
    result_1 = plan_roadtrip(
        supply_planning=Args(num_people=Args(is_josie_in=True)),
        accomodation_booking=Args(num_people=Args(is_josie_in=True)),
        car_booking=Args(num_drivers=2),
    )
    result_2 = plan_roadtrip(
        supply_planning=Args(num_people=Args(is_josie_in=False)),
        accomodation_booking=Args(num_people=Args(is_josie_in=False)),
        car_booking=Args(num_drivers=2),
    )

    assert result_1 != result_2
    assert result_1 == [
        "Buy 16 chips packages",
        "Get TimTams",
        "Check availability for 4",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert result_2 == [
        "Buy 12 chips packages",
        "Get TimTams",
        "Check availability for 3",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert call_counts["figure_out_num_people"] == 2
    assert call_counts["make_supply_list"] == 2
    assert call_counts["find_accomodation"] == 2
    assert call_counts["plan_car_booking"] == 1
    assert call_counts["plan_roadtrip"] == 2


def test_result_recomputed_on_code_change(roadtrip_planning):
    (
        plan_roadtrip, call_counts, (
            call_counter, figure_out_num_people, supply_planning_dependency
        )
    ) = roadtrip_planning
    result_1 = plan_roadtrip(
        car_booking=Args(num_drivers=2),
    )

    @stage
    @call_counter
    def make_supply_list(
        num_people=Result(figure_out_num_people, Args(is_josie_in=False))
    ):
        return [
            f"Buy {num_people * 4} chips packages",
        ]
    supply_planning_dependency.stage = make_supply_list
    result_2 = plan_roadtrip(
        car_booking=Args(num_drivers=2),
    )

    assert result_1 != result_2
    assert result_1 == [
        "Buy 12 chips packages",
        "Get TimTams",
        "Check availability for 3",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert result_2 == [
        "Buy 12 chips packages",
        "Check availability for 3",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert call_counts["figure_out_num_people"] == 1
    assert call_counts["make_supply_list"] == 2
    assert call_counts["find_accomodation"] == 1
    assert call_counts["plan_car_booking"] == 1
    assert call_counts["plan_roadtrip"] == 2


def test_result_cached_on_stage_name_change_change(roadtrip_planning):
    (
        plan_roadtrip, call_counts, (
            call_counter, figure_out_num_people, supply_planning_dependency
        )
    ) = roadtrip_planning
    result_1 = plan_roadtrip(
        car_booking=Args(num_drivers=2),
    )

    @stage
    @call_counter
    def plan_supplies(
        num_people=Result(figure_out_num_people, Args(is_josie_in=False))
    ):
        return [
            f"Buy {num_people * 4} chips packages",
            "Get TimTams",
        ]
    supply_planning_dependency.stage = plan_supplies
    result_2 = plan_roadtrip(
        car_booking=Args(num_drivers=2),
    )

    assert result_1 == result_2
    assert result_1 == [
        "Buy 12 chips packages",
        "Get TimTams",
        "Check availability for 3",
        "Determine distance",
        "Compare prices for 2 drivers",
    ]
    assert call_counts["figure_out_num_people"] == 1
    assert call_counts["make_supply_list"] == 1
    assert call_counts["plan_supplies"] == 0
    assert call_counts["find_accomodation"] == 1
    assert call_counts["plan_car_booking"] == 1
    assert call_counts["plan_roadtrip"] == 1


def test_result_recomputed_on_value_change():
    # TODO: implement
    pass


def test_result_recomputed_on_file_change():
    # TODO: implement
    pass
