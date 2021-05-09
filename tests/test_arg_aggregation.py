from pycrastinate.utils.arg_aggregation import aggregate_args
from pycrastinate.args import Args


def greet(greeting: str, age = 25, name: str = "Janine"):
    print(f"{greeting} {name}, you're {age} years old.")


def test_no_args_passed():
    aggregation_result = aggregate_args(greet)
    assert aggregation_result.non_dependency_args == {
        "age": 25, "name": "Janine"
    }
    assert aggregation_result.data_dependencies == {}
    assert aggregation_result.data_dependency_args == {}
    assert aggregation_result.func_dependencies == {}


def test_override_name():
    aggregation_result = aggregate_args(greet, Args("Hi", name="Donald"))
    assert aggregation_result.non_dependency_args == {
        "greeting": "Hi", "age": 25, "name": "Donald"
    }
    assert aggregation_result.data_dependencies == {}
    assert aggregation_result.data_dependency_args == {}
    assert aggregation_result.func_dependencies == {}


def test_override_age():
    aggregation_result = aggregate_args(greet, Args("Hola", age=23))
    assert aggregation_result.non_dependency_args == {
        "greeting": "Hola", "age": 23, "name": "Janine"
    }
    assert aggregation_result.data_dependencies == {}
    assert aggregation_result.data_dependency_args == {}
    assert aggregation_result.func_dependencies == {}


def test_override_both():
    aggregation_result = aggregate_args(greet, Args("Moshi Moshi", age=39, name="Tim"))
    assert aggregation_result.non_dependency_args == {
        "greeting": "Moshi Moshi", "age": 39, "name": "Tim"
    }
    assert aggregation_result.data_dependencies == {}
    assert aggregation_result.data_dependency_args == {}
    assert aggregation_result.func_dependencies == {}


def test_equal_aggregated_args():
    def func_generator():
        def greet(name = "Jonas", repetitions=1):
            for _ in range(repetitions):
                print(f"Hi {name}")
        return greet

    func_1 = func_generator()
    func_2 = func_generator()
    aggregation_result_1 = aggregate_args(func_1, Args(repetitions=2))
    aggregation_result_2 = aggregate_args(func_2, Args("Jonas", 2))
    assert id(func_1) != id(func_2)
    assert aggregation_result_1 == aggregation_result_2
    assert aggregation_result_1.non_dependency_args == {
        "name": "Jonas", "repetitions": 2
    }
    assert aggregation_result_1.data_dependencies == {}
    assert aggregation_result_1.data_dependency_args == {}
    assert aggregation_result_1.func_dependencies == {}
