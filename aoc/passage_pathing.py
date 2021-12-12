from collections import Counter
from collections.abc import Sequence, MutableSet
from typing import Dict, Iterable, Iterator, List, Optional, Set

from . import Challenge


class Cave:
    def __init__(self, name: str):
        self.name = name
        self._neighbors: Set[Cave] = set()

    def successors(self, path: "Path") -> Iterator["Cave"]:
        yield from (n for n in self.neighbors if n.can_be_added(path))

    def can_be_added(self, to_path: "Path") -> bool:
        return True

    @property
    def neighbors(self) -> Set["Cave"]:
        return self._neighbors

    def add_neighbor(self, cave: "Cave"):
        self._neighbors.add(cave)
        cave._neighbors.add(self)

    def all_paths(self, to: "Cave") -> Iterator["Path"]:
        queue: List[Path] = [Path(self)]
        while queue:
            path = queue.pop()
            if path[-1] == to:
                yield path
            else:
                queue.extend(s for s in path.successors() if s[-1] != self)

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
            self._caves: Dict[Cave, int] = Counter(parent._caves)
            self.add(cave)
        else:
            self._ordered = [cave]
            self._caves = Counter(self._ordered)

    def add(self, cave: Cave):
        self._caves[cave] += 1
        self._ordered.append(cave)

    def discard(self, value: Cave) -> None:
        raise NotImplementedError("Paths cannot discard caves")

    def num_visits(self, cave: Cave) -> int:
        return self._caves[cave]

    def __contains__(self, x) -> bool:
        return x in self._caves

    def __getitem__(self, index) -> Cave:
        return self._ordered[index]

    def __len__(self) -> int:
        return len(self._ordered)

    def __iter__(self) -> Iterator[Cave]:
        yield from self._ordered

    def successors(self) -> Iterator["Path"]:
        yield from (Path(s, self) for s in self._ordered[-1].successors(self))

    def __str__(self):
        return ",".join(map(str, self))


class SmallCave(Cave):
    def __init__(self, name: str, max_visits: int):
        super().__init__(name)
        self.max_visits: int = max_visits

    def can_be_added(self, to_path: Path) -> bool:
        return to_path.num_visits(self) == 0 or not any(
            isinstance(c, SmallCave) and to_path.num_visits(c) >= c.max_visits
            and c.name not in ("start", "end")
            for c in to_path
        )


class PassagePathing(Challenge):
    day = 12

    @staticmethod
    def parse_cave(name: str, max_small_cave_visits: int) -> Cave:
        if name == "start":
            return SmallCave("start", 0)
        elif name == "end":
            return SmallCave("end", 0)
        elif name == name.lower():
            return SmallCave(name, max_small_cave_visits)
        elif name == name.upper():
            return Cave(name)
        else:
            raise ValueError(f"Invalid cave name: {name!r}")

    @staticmethod
    def load(lines: Iterable[str], max_small_cave_visits: int) -> Dict[str, Cave]:
        caves: Dict[str, Cave] = {}
        for line in lines:
            c1, c2 = map(str.strip, line.split("-"))
            if c1 in caves:
                cave1 = caves[c1]
            else:
                cave1 = PassagePathing.parse_cave(c1, max_small_cave_visits=max_small_cave_visits)
                caves[c1] = cave1
            if c2 in caves:
                cave2 = caves[c2]
            else:
                cave2 = PassagePathing.parse_cave(c2, max_small_cave_visits=max_small_cave_visits)
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
            caves = PassagePathing.load(f, max_small_cave_visits=1)
        start = caves["start"]
        end = caves["end"]
        num_paths = sum(1 for _ in start.all_paths(end))
        self.output.write(f"{num_paths}\n")

    @Challenge.register_part(1)
    def two_visits(self):
        # self.test()
        with open(self.input_path, "r") as f:
            caves = PassagePathing.load(f, max_small_cave_visits=2)
        start = caves["start"]
        end = caves["end"]
        num_paths = sum(1 for _ in start.all_paths(end))
        self.output.write(f"{num_paths}\n")
