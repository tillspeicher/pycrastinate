from pycrastinate.utils.hashing import compute_code_hash, compute_value_hash


def test_empty_funcs_equal():
    def func_generator():
        def func():
            pass
        return func

    func_1 = func_generator()
    func_2 = func_generator()
    hash_1 = compute_code_hash(func_1)
    hash_2 = compute_code_hash(func_2)
    assert id(func_1) != id(func_2)
    assert hash_1 == hash_2


def test_funcs_equal():
    def func_generator():
        def foo(a: int, b: str = "Hi"):
            print(f"a: {a} and b: {b}")
        return foo

    func_1 = func_generator()
    func_2 = func_generator()
    hash_1 = compute_code_hash(func_1)
    hash_2 = compute_code_hash(func_2)
    assert id(func_1) != id(func_2)
    assert hash_1 == hash_2


def test_different_funcs():
    def func_generator_1():
        def foo(a: int, b: str = "Hi"):
            print(f"a: {a} and b: {b}")
        return foo

    def func_generator_2():
        def foo(a: int, b: str = "Hi"):
            print(f"param a: {a}, b: {b}")
        return foo

    func_1 = func_generator_1()
    func_2 = func_generator_2()
    hash_1 = compute_code_hash(func_1)
    hash_2 = compute_code_hash(func_2)
    assert hash_1 != hash_2


def test_different_func_names_same_content():
    def foo_1(a: int, b="b") -> str:
        if a > 5:
            b = "bb"
        return b + str(a)

    def foo_2(a: int, b="b") -> str:
        if a > 5:
            b = "bb"
        return b + str(a)

    hash_1 = compute_code_hash(foo_1)
    hash_2 = compute_code_hash(foo_2)
    assert hash_1 == hash_2


def test_different_names_and_args_same_code_different():
    def bar_1(a, b, c="c"):
        if a > 5:
            b = "bb"
        return b + str(a)

    def bar_2(a, b):
        if a > 5:
            b = "bb"
        return b + str(a)

    hash_1 = compute_code_hash(bar_1)
    hash_2 = compute_code_hash(bar_2)
    assert hash_1 != hash_2


def test_different_comments_and_whitespaces_same():
    def foo(a: int, b: int) -> int:

        # Some comment, there's a loop now
        while a < b:
            b = 2 * b
        # Let's return something
        return b - a

    def bar(a: int, b: int) -> int:
        while a < b:
            # We double b
            b = 2 * b

        return b - a # The difference

    hash_1 = compute_code_hash(foo)
    hash_2 = compute_code_hash(bar)
    assert hash_1 == hash_2


# Test:
# different names, same code -> same hash
# different names, different args, same code -> different hash
# Difference in comments and whitespace -> same hash


# def test_equal_args():
    # def func_generator():
        # def foo(a: int, b: str = "Hi"):
            # print(f"a: {a} and b: {b}")
        # return foo
# 
    # func_1 = func_generator()
    # func_2 = func_generator()
    # hash_1 = compute_stage_hash(func_1, args=Args(2, b="Hello"))
    # hash_2 = compute_stage_hash(func_2, args=Args(2, b="Hello"))
    # assert id(func_1) != id(func_2)
    # assert hash_1 == hash_2
# 
# 
# # TODO: should this actually be different?
# def test_different_names():
    # def foo():
        # return None
# 
    # def bar():
        # return None
# 
    # hash_1 = compute_stage_hash(foo, args=Args())
    # hash_2 = compute_stage_hash(bar, args=Args())
    # assert hash_1 != hash_2
    # 
# 
# def test_different_signatures():
    # def func_generator_1():
        # def f(a: int, b: str = "Hi"):
            # print(f"Hi {b}")
        # return f
# 
    # def func_generator_2():
        # def f(b: str = "Hi"):
            # print(f"Hi {b}")
        # return f
# 
    # func_1 = func_generator_1()
    # func_2 = func_generator_2()
    # hash_1 = compute_stage_hash(func_1, args=Args(b="Dorothy"))
    # hash_2 = compute_stage_hash(func_2, args=Args(b="Dorothy"))
    # assert hash_1 != hash_2
# 
# 
# def test_different_code():
    # def func_generator_1():
        # def f(a):
            # return a * 10
        # return f
# 
    # def func_generator_2():
        # def f(a):
            # return a * 2 + 10
        # return f
# 
    # func_1 = func_generator_1()
    # func_2 = func_generator_2()
    # hash_1 = compute_stage_hash(func_1, args=Args())
    # hash_2 = compute_stage_hash(func_2, args=Args())
    # assert hash_1 != hash_2
# 
# 
# def test_different_pos_params():
    # def func_generator():
        # def foo(a: int, b: str = "Hi"):
            # print(f"a: {a} and b: {b}")
        # return foo
# 
    # func_1 = func_generator()
    # func_2 = func_generator()
    # hash_1 = compute_stage_hash(func_1, args=Args(4, b="Hello"))
    # hash_2 = compute_stage_hash(func_2, args=Args(1, b="Hello"))
    # assert id(func_1) != id(func_2)
    # assert hash_1 != hash_2
# 
# 
# def test_different_named_params():
    # def func_generator():
        # def foo(a: int, b: str = "Hi"):
            # print(f"a: {a} and b: {b}")
        # return foo
# 
    # func_1 = func_generator()
    # func_2 = func_generator()
    # hash_1 = compute_stage_hash(func_1, args=Args(1, b="Hola"))
    # hash_2 = compute_stage_hash(func_2, args=Args(1, b="Hallo"))
    # assert id(func_1) != id(func_2)
    # assert hash_1 != hash_2
