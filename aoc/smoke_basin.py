from typing import List, Iterable, Iterator

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


class HeightMap:
    def __init__(self, heights: List[List[int]]):
        self.heights: List[List[int]] = heights
        self.height: int = len(self.heights)
        self.width: int = len(self.heights[0])

    def neighborhood(self, row: int, col: int):
        for nrow in clipped_range(row, max_value=self.height - 1):
            for ncol in clipped_range(col, max_value=self.width - 1):
                if nrow == row and ncol == col:
                    continue
                yield self.heights[nrow][ncol]

    def low_points(self) -> Iterator[int]:
        for row in range(self.height):
            for col in range(self.width):
                v = self.heights[row][col]
                if all(n > v for n in self.neighborhood(row, col)):
                    yield v


class SmokeBasin(Challenge):
    day = 9

    @Challenge.register_part(0)
    def risks(self):
        with open(self.input_path, "r") as f:
            heightmap = HeightMap([
                [int(height) for height in line.strip()]
                for line in f
            ])
        risk_total = sum(height + 1 for height in heightmap.low_points())
        self.output.write(f"{risk_total}\n")
