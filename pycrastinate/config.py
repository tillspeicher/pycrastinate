from typing import Union
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    cache_dir: Path = Path("./__pycrastinate__") 

_config = Config()


def set_cache_dir(new_cache_dir: Union[str, Path]) -> None:
    _config.cache_dir = Path(new_cache_dir)

def get_cache_dir() -> Path:
    return _config.cache_dir
