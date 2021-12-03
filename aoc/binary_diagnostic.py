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

    @Challenge.register_part(1)
    def life_support_rating(self):
        oxygen_numbers = list(self.read_input())
        co2_numbers = list(oxygen_numbers)
        bit = 0
        while len(oxygen_numbers) > 1 and bit < len(oxygen_numbers[0]):
            frequency = Counter((n[bit] for n in oxygen_numbers)).most_common()
            assert len(frequency) == 2
            if frequency[0][1] == frequency[1][1]:
                # break ties with 1
                most_common = 1
            else:
                most_common = frequency[0][0]
            oxygen_numbers = [n for n in oxygen_numbers if n[bit] == most_common]
            bit += 1
        bit = 0
        while len(co2_numbers) > 1 and bit < len(co2_numbers[0]):
            frequency = Counter((n[bit] for n in co2_numbers)).most_common()
            assert len(frequency) == 2
            if frequency[0][1] == frequency[1][1]:
                # break ties with 0
                least_common = 0
            else:
                least_common = frequency[-1][0]
            co2_numbers = [n for n in co2_numbers if n[bit] == least_common]
            bit += 1
        oxygen = bits_to_int(oxygen_numbers[0])
        co2 = bits_to_int(co2_numbers[0])
        self.output.write(f"{oxygen * co2}\n")
