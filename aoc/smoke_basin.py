from heapq import nlargest
import math
from typing import FrozenSet, List, Iterable, Iterator, Optional, Set, Tuple

from . import Challenge


def clipped_range(value: int, max_value: int, min_value: int = 0) -> Iterable[int]:
    if min_value < value < max_value:
        return range(value - 1, value + 2)
    elif min_value < value:
        return range(value - 1, value + 1)
    elif value < max_value:
        return range(value, value + 2)
    else:
        return range(value, value + 1)


Location = Tuple[int, int]


class Basin:
    def __init__(self, locations: Iterable[Location]):
        self.locations: FrozenSet[Location, ...] = frozenset(locations)

    def __len__(self):
        return len(self.locations)

    def __iter__(self) -> Iterator[Location]:
        yield from iter(self.locations)

    @staticmethod
    def load(height_map: "HeightMap", row: int, col: int) -> "Basin":
        locations: Set[Location] = {(row, col)}
        queue: List[Location] = list(locations)
        while queue:
            r, c = queue.pop()
            for loc, height in height_map.neighborhood(r, c):
                if height < 9 and loc not in locations:
                    queue.append(loc)
                    locations.add(loc)
        return Basin(locations)


class HeightMap:
    def __init__(self, heights: List[List[int]]):
        self.heights: List[List[int]] = heights
        self.height: int = len(self.heights)
        self.width: int = len(self.heights[0])

    def neighborhood(self, row: int, col: int) -> Iterator[Tuple[Location, int]]:
        if row > 0:
            yield (row - 1, col), self.heights[row - 1][col]
        if col > 0:
            yield (row, col - 1), self.heights[row][col - 1]
        if col < self.width - 1:
            yield (row, col + 1), self.heights[row][col + 1]
        if row < self.height - 1:
            yield (row + 1, col), self.heights[row + 1][col]

    def low_points(self) -> Iterator[int]:
        for row in range(self.height):
            for col in range(self.width):
                _, v = self.heights[row][col]
                if all(n > v for n in self.neighborhood(row, col)):
                    yield v

    def basins(self) -> Iterator[Basin]:
        locations: Set[Location] = set()
        for row in range(self.height):
            for col in range(self.width):
                if (row, col) in locations or self.heights[row][col] >= 9:
                    continue
                basin = Basin.load(self, row, col)
                locations |= basin.locations
                yield basin


class SmokeBasin(Challenge):
    day = 9
    _map: Optional[HeightMap] = None

    @property
    def height_map(self) -> HeightMap:
        if self._map is None:
            with open(self.input_path, "r") as f:
                self._map = HeightMap([
                    [int(height) for height in line.strip()]
                    for line in f
                ])
        return self._map

    @Challenge.register_part(0)
    def risks(self):
        risk_total = sum(height + 1 for height in self.height_map.low_points())
        self.output.write(f"{risk_total}\n")

    @Challenge.register_part(1)
    def basins(self):
        basin_sizes = [len(basin) for basin in self.height_map.basins()]
        total = math.prod(nlargest(3, basin_sizes))
        self.output.write(f"{total}\n")
