from collections.abc import Sequence, MutableSet
from typing import Dict, Iterable, Iterator, List, Optional, Set

from . import Challenge


class Cave:
    def __init__(self, name: str):
        self.name = name
        self._neighbors: Set[Cave] = set()

    def successors(self, history: Set["Cave"]) -> Iterator["Cave"]:
        yield from (n for n in self.neighbors if isinstance(n, BigCave) or n not in history)

    @property
    def neighbors(self) -> Set["Cave"]:
        return self._neighbors

    def add_neighbor(self, cave: "Cave"):
        self._neighbors.add(cave)
        cave._neighbors.add(self)

    @staticmethod
    def parse(cave_name: str) -> "Cave":
        if cave_name == cave_name.lower():
            return SmallCave(cave_name)
        elif cave_name == cave_name.upper():
            return BigCave(cave_name)
        else:
            raise ValueError(f"Invalid cave name: {cave_name!r}")

    def all_paths(self, to: "Cave") -> Iterator["Path"]:
        queue: List[Path] = [Path(self)]
        while queue:
            path = queue.pop()
            if path[-1] == to:
                yield path
            else:
                queue.extend(path.successors())

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Cave) and other.name == self.name

    def __str__(self):
        return self.name


class Path(MutableSet[Cave], Sequence[Cave]):
    def __init__(self, cave: Cave, parent: Optional["Path"] = None):
        if parent is not None:
            self._ordered: List[Cave] = list(parent._ordered)
            self._caves: Set[Cave] = set(parent._caves)
            self.add(cave)
        else:
            self._ordered = [cave]
            self._caves = set(self._ordered)

    def add(self, cave: Cave):
        self._caves.add(cave)
        self._ordered.append(cave)

    def discard(self, value: Cave) -> None:
        raise NotImplementedError("Paths cannot discard caves")

    def __contains__(self, x) -> bool:
        return x in self._caves

    def __getitem__(self, index) -> Cave:
        return self._ordered[index]

    def __len__(self) -> int:
        return len(self._ordered)

    def __iter__(self) -> Iterator[Cave]:
        yield from self._ordered

    def successors(self) -> Iterator["Path"]:
        yield from (Path(s, self) for s in self._ordered[-1].successors(self._caves))

    def __str__(self):
        return ",".join(map(str, self))


class SmallCave(Cave):
    pass


class BigCave(Cave):
    pass


class PassagePathing(Challenge):
    day = 12

    @staticmethod
    def load(lines: Iterable[str]) -> Dict[str, Cave]:
        caves: Dict[str, Cave] = {}
        for line in lines:
            c1, c2 = map(str.strip, line.split("-"))
            if c1 in caves:
                cave1 = caves[c1]
            else:
                cave1 = Cave.parse(c1)
                caves[c1] = cave1
            if c2 in caves:
                cave2 = caves[c2]
            else:
                cave2 = Cave.parse(c2)
                caves[c2] = cave2
            cave1.add_neighbor(cave2)
        return caves

    def test(self):
        test_data = """fs-end
he-DX
fs-he
start-DX
pj-DX
end-zg
zg-sl
zg-pj
pj-he
RW-he
fs-DX
pj-RW
zg-RW
start-pj
he-WI
zg-he
pj-fs
start-RW"""
        caves = PassagePathing.load(test_data.split("\n"))
        start = caves["start"]
        end = caves["end"]
        print(sum(1 for _ in start.all_paths(end)))

    @Challenge.register_part(0)
    def small_caves(self):
        # self.test()
        with open(self.input_path, "r") as f:
            caves = PassagePathing.load(f)
        start = caves["start"]
        end = caves["end"]
        num_paths = sum(1 for _ in start.all_paths(end))
        self.output.write(f"{num_paths}\n")
