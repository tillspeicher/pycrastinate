import pickle
import bz2
from typing import Any


PICKLE_PROTOCOL_VERSION = 4


def encode(data: Any) -> bytes:
    # TODO: check whether the protocol version is available and throw and error if not
    return pickle.dumps(data, protocol=PICKLE_PROTOCOL_VERSION)


def decode(encoded_data: bytes) -> Any:
    return pickle.loads(encoded_data)


def compress(data: bytes) -> bytes:
    return bz2.compress(data)


def decompress(compressed_data: bytes) -> bytes:
    return bz2.decompress(compressed_data)
