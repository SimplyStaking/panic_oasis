from typing import Union

from src.utils.types import GIGA, NANO


def scale_to_giga(num: float) -> Union[float, int]:
    return num * GIGA


def scale_to_nano(num: float) -> float:
    return num * NANO
