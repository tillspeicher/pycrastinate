from pathlib import Path
from typing import (
    Any,
    Optional,
)

from .encoding import (
    encode,
    decode,
    compress,
    decompress,
)


def save_object(results_file: Path, data: Any) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)

    encoded_data = encode(data)
    compressed_data = compress(encoded_data)
    
    results_file.write_bytes(compressed_data)


def load_object(results_file: Path) -> Optional[Any]:
    try:
        compressed_data = results_file.read_bytes()
    except FileNotFoundError:
        return None

    encoded_data = decompress(compressed_data)
    return decode(encoded_data)
