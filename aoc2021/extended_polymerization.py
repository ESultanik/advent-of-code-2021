from collections import Counter
from typing import Counter as CounterType, Dict, Iterable, Iterator, TextIO, Union

from . import Challenge


class Polymer:
    def __init__(
            self, first_char: str, last_char: str, rules: Dict[str, str], pairs: Union[Iterable[str], Dict[str, int]]
    ):
        self.rules: Dict[str, str] = rules
        self.first_char = first_char
        self.last_char = last_char
        self.pairs: CounterType[str] = Counter(pairs)

    def next_pairs(self) -> CounterType[str]:
        counts = Counter()
        for (e1, e2), old_count in self.pairs.items():
            middle = self.rules["".join((e1, e2))]
            counts[f"{e1}{middle}"] += old_count
            counts[f"{middle}{e2}"] += old_count
        return counts

    def step(self) -> "Polymer":
        return Polymer(self.first_char, self.last_char, self.rules, self.next_pairs())

    def num_elements(self) -> CounterType[str]:
        counts = Counter()
        for (e1, e2), count in self.pairs.items():
            counts[e1] += count
            counts[e2] += count
        ret = Counter()
        for e, count in counts.items():
            if e == self.first_char and e == self.last_char:
                ret[e] = (counts[e] - 2) // 2 + 2
            elif e == self.first_char or e == self.last_char:
                ret[e] = (counts[e] - 1) // 2 + 1
            else:
                ret[e] = counts[e] // 2
        return ret

    @staticmethod
    def load(stream: TextIO) -> "Polymer":
        first_line = stream.readline().strip()
        first_char = first_line[0]
        last_char = first_line[-1]
        rules = {}
        for line in stream:
            line = line.strip()
            if not line:
                continue
            arrow_pos = line.find("->")
            if arrow_pos <= 0:
                continue
            rules[line[:arrow_pos].strip()] = line[arrow_pos + 2:].strip()
        return Polymer(first_char, last_char, rules, pairs=("".join(c) for c in zip(first_line, first_line[1:])))


class ExtendedPolymerization(Challenge):
    day = 14

    @Challenge.register_part(0)
    def commonality(self):
        with open(self.input_path, "r") as f:
            p = Polymer.load(f)
        for _ in range(10):
            p = p.step()
        elements = p.num_elements()
        commonality = elements.most_common()
        _, highest_count = commonality[0]
        _, lowest_count = commonality[-1]
        self.output.write(f"{highest_count - lowest_count}\n")
