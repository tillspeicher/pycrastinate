from pathlib import Path
from typing import Optional

from .result import PersistedInvocation
from ..utils.persistence import save_object, load_object


def save_stage_result(
    results_dir: Path,
    hash: bytes,
    result: PersistedInvocation,
) -> None:
    results_file = _get_stage_result_path(results_dir, hash)
    save_object(results_file, result)


def load_stage_result(
    results_dir: Path, hash: bytes
) -> Optional[PersistedInvocation]:
    results_file = _get_stage_result_path(results_dir, hash)
    return load_object(results_file)


STAGE_RESULTS_DIR_NAME = "stage_results"
SUBDIR_NAME_LENGTH = 2
MAX_FUNC_NAME_LENGTH = 255 # Max file name length on most file systems


def _get_stage_result_path(results_dir: Path, hash: bytes) -> Path:
    # Creating subdirectories named by a prefix of the hash is inspired by Git
    # See the structure of the .git/objects/ folder
    encoded_hash = hash.hex()
    subdir_name = encoded_hash[:SUBDIR_NAME_LENGTH]
    file_dir = (
        results_dir
        / STAGE_RESULTS_DIR_NAME
        / subdir_name
    )
    file_name = encoded_hash[SUBDIR_NAME_LENGTH:]
    return file_dir / file_name
