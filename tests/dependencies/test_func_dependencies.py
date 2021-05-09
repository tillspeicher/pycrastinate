import pytest

from pycrastinate import stage, Result, Use, Args, set_cache_dir

from tests.utils.call_counter import CallCounter


@pytest.fixture
def fun_with_dinosaurs(tmp_path):
    set_cache_dir(tmp_path)
    call_counter = CallCounter()

    @stage
    @call_counter
    def find_fossilized_dna_sample(
        species: str
    ):
        return f"amber with {species} DNA"

    @stage
    @call_counter
    def clone_dinosaur(
        species: str,
        dna_sample=Use(find_fossilized_dna_sample)
    ):
        dna = dna_sample(species=species)
        return f"hungry {dna[11:-4]}"

    @stage
    @call_counter
    def open_theme_park(
        dinosaur=Result(clone_dinosaur, Args(species="T-Rex"))
    ):
        return f"Hmm, where did that {dinosaur} go?"

    return open_theme_park, call_counter.counter, (
        call_counter, find_fossilized_dna_sample, clone_dinosaur
    )


def test_func_dep_executed_without_args(fun_with_dinosaurs):
    dinosaur_land, call_counts, _ = fun_with_dinosaurs
    park_1 = dinosaur_land()
    park_2 = dinosaur_land()

    assert park_1 == park_2
    assert park_1 == "Hmm, where did that hungry T-Rex go?"
    assert call_counts["find_fossilized_dna_sample"] == 1
    assert call_counts["clone_dinosaur"] == 1
    assert call_counts["open_theme_park"] == 1


def test_func_dep_skipped_with_same_args_and_code(fun_with_dinosaurs):
    dinosaur_land, call_counts, _ = fun_with_dinosaurs
    park_1 = dinosaur_land(dinosaur=Args(species="Titanosaur"))
    park_2 = dinosaur_land(dinosaur=Args(species="Titanosaur"))

    assert park_1 == park_2
    assert park_1 == "Hmm, where did that hungry Titanosaur go?"
    assert call_counts["find_fossilized_dna_sample"] == 1
    assert call_counts["clone_dinosaur"] == 1
    assert call_counts["open_theme_park"] == 1


def test_func_dep_executed_with_same_args_and_different_code(fun_with_dinosaurs):
    dinosaur_land, call_counts, (
        call_counter, find_fossilized_dna_sample, clone_dinosaur_stage
    ) = fun_with_dinosaurs
    park_1 = dinosaur_land(dinosaur=Args(species="Stegosaurus"))

    @call_counter
    def clone_dinosaur(
        species: str,
        dna_sample=Use(find_fossilized_dna_sample)
    ):
        dna_snippet = dna_sample(species=species)
        return f"hungry {dna_snippet[11:-4]}"
    clone_dinosaur_stage.stage_func = clone_dinosaur
    park_2 = dinosaur_land(dinosaur=Args(species="Stegosaurus"))

    assert park_1 == park_2
    assert park_1 == "Hmm, where did that hungry Stegosaurus go?"
    assert call_counts["find_fossilized_dna_sample"] == 1
    assert call_counts["clone_dinosaur"] == 2
    assert call_counts["open_theme_park"] == 1


def test_func_dep_executed_with_same_args_and_different_code_behind_func_dependency(
    fun_with_dinosaurs
):
    _, call_counts, (
        call_counter, find_fossilized_dna_sample, clone_dinosaur_stage
    ) = fun_with_dinosaurs
    @stage
    @call_counter
    def shoot_movie(
        built: str,
        dinosaur=Use(clone_dinosaur_stage),
    ):
        return f"Woow, look at that {built} {dinosaur('T-Rex')}, so real!"
    movie_1 = shoot_movie(built="big")

    @call_counter
    def clone_dinosaur(
        species: str,
        dna_sample=Use(find_fossilized_dna_sample)
    ):
        dna_snippet = dna_sample(species=species)
        return f"hungry {dna_snippet[11:-4]}"
    clone_dinosaur_stage.stage_func = clone_dinosaur
    movie_2 = shoot_movie("big")

    assert movie_1 == movie_2 
    assert movie_1 == "Woow, look at that big hungry T-Rex, so real!"
    assert call_counts["find_fossilized_dna_sample"] == 1
    assert call_counts["clone_dinosaur"] == 2
    assert call_counts["shoot_movie"] == 2


def test_func_dep_executed_with_different_args(fun_with_dinosaurs):
    dinosaur_land, call_counts, _ = fun_with_dinosaurs
    park_1 = dinosaur_land(dinosaur=Args(species="Triceratops"))
    park_2 = dinosaur_land(dinosaur=Args(species="Utahraptor"))

    assert park_1 == "Hmm, where did that hungry Triceratops go?"
    assert park_2 == "Hmm, where did that hungry Utahraptor go?"
    assert call_counts["find_fossilized_dna_sample"] == 2
    assert call_counts["clone_dinosaur"] == 2
    assert call_counts["open_theme_park"] == 2


def test_func_dep_with_indirect_data_dependencies_rejected():
    pass
