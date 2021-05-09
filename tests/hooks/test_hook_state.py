from pycrastinate.hooks.persistence import HookState, HookArgumentState
# from pycrastinate import hook


def test_invalidation_on_new_state():
    hook_state = HookState()

    def foo():
        print("a")

    assert hook_state.code_hash is None
    has_changed = hook_state.update_code_hash(foo, {})
    assert has_changed


def test_invalidation_on_code_change():
    hook_state = HookState()

    def foo():
        print("a")

    def bar():
        print("b")

    hook_state.update_code_hash(foo, {})
    hook_state.arg_states = {
        "dep1": HookArgumentState(),
        "dep2": HookArgumentState(),
    }

    has_changed = hook_state.update_code_hash(bar, {})
    assert has_changed
    assert all (
        (
            arg_state.last_executed_result_reference is None
            and len(arg_state.all_executed_result_references) == 0
        ) for arg_state in hook_state.arg_states.values()
    )


def test_invalidation_only_on_first_code_change():
    hook_state = HookState()

    def foo():
        print("Hi")

    def bar():
        print("Hop")

    hook_state.update_code_hash(foo, {})
    # hook_state.arg_states = {
        # "dep1": HookArgumentState(last_result_reference=b"abc"),
        # "dep2": HookArgumentState(last_result_reference=b"def"),
    # }

    has_changed_1 = hook_state.update_code_hash(bar, {})
    has_changed_2 = hook_state.update_code_hash(bar, {})
    assert has_changed_1
    assert not has_changed_2


def test_dependency_change_triggers_invalidation():
    hook_state = HookState()

    def foo():
        print("Hi")
    # hook_state.arg_states = {
        # "dep1": HookArgumentState(last_result_reference=b"abc"),
        # "dep2": HookArgumentState(last_result_reference=b"def"),
    # }

    has_changed_1 = hook_state.update_code_hash(foo, {
        "usage1": b"123", "usage2": b"456"
    })
    has_changed_2 = hook_state.update_code_hash(foo, {
        "usage1": b"123", "usage2": b"789"
    })
    has_changed_3 = hook_state.update_code_hash(foo, {
        "usage1": b"123", "usage2": b"789"
    })

    assert has_changed_1
    assert has_changed_2
    assert not has_changed_3
    # assert recovery_result_2 == {
        # "dep1": b"abc", "dep2": b"def"
    # }
