from pathlib import Path

from pycrastinate import config


def test_set_results_dir():
    config.set_cache_dir("custom_dir")
    assert config.get_cache_dir() == Path("custom_dir")
    # TODO: make sure the results dir is actually used
