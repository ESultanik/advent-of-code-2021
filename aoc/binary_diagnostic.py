from collections import Counter
from typing import Iterable, Iterator, Tuple, TypeVar

from . import Challenge


T = TypeVar('T')


def most_frequent(data: Iterable[T]) -> T:
    return Counter(data).most_common(1)[0][0]


def least_frequent(data: Iterable[T]) -> T:
    return Counter(data).most_common()[:-2:-1][0][0]


def bits_to_int(bits: Iterable[int]) -> int:
    ret = 0
    for bit in bits:
        ret <<= 1
        if bit:
            ret |= 1
    return ret


class BinaryDiagnostic(Challenge):
    day = 3

    def read_input(self) -> Iterator[Tuple[int, ...]]:
        with open(self.input_path, "r") as f:
            for line in f:
                yield tuple(int(c) for c in line if c == "0" or c == "1")

    @Challenge.register_part(0)
    def power_consumption(self):
        numbers = list(self.read_input())
        bits = tuple(zip(*numbers))
        gamma_bits = tuple(most_frequent(b) for b in bits)
        epsilon_bits = tuple(least_frequent(b) for b in bits)
        gamma = bits_to_int(gamma_bits)
        epsilon = bits_to_int(epsilon_bits)
        self.output.write(f"{gamma * epsilon}\n")
