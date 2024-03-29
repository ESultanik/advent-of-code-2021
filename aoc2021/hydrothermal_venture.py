from abc import ABC, abstractmethod
from collections import Counter, defaultdict
import re
from typing import Dict, Iterator, Tuple

from . import Challenge


class Line(ABC):
    @abstractmethod
    def points(self) -> Iterator[Tuple[int, int]]:
        raise NotImplementedError()

    @property
    def p1(self) -> Tuple[int, int]:
        return next(iter(self.points()))

    @property
    def x1(self) -> int:
        return self.p1[0]

    @property
    def y1(self) -> int:
        return self.p1[1]

    @property
    def x2(self) -> int:
        return self.p2[0]

    @property
    def y2(self) -> int:
        return self.p2[1]

    @property
    @abstractmethod
    def p2(self) -> Tuple[int, int]:
        raise NotImplementedError()

    def __str__(self):
        return f"{self.x1},{self.y1} -> {self.x2},{self.y2}"


class HorizontalLine(Line):
    def __init__(self, from_x: int, to_x: int, y: int):
        if from_x > to_x:
            from_x, to_x = to_x, from_x
        self.from_x: int = from_x
        self.to_x: int = to_x
        self.y: int = y

    def points(self) -> Iterator[Tuple[int, int]]:
        yield from ((x, self.y) for x in range(self.from_x, self.to_x + 1))

    @property
    def p2(self) -> Tuple[int, int]:
        return self.to_x, self.y


class VerticalLine(Line):
    def __init__(self, x: int, from_y: int, to_y: int):
        self.x: int = x
        if from_y > to_y:
            from_y, to_y = to_y, from_y
        self.from_y: int = from_y
        self.to_y: int = to_y

    def points(self) -> Iterator[Tuple[int, int]]:
        yield from ((self.x, y) for y in range(self.from_y, self.to_y + 1))

    @property
    def p2(self) -> Tuple[int, int]:
        return self.x, self.to_y


class DiagonalLine(Line):
    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        if x1 > x2:
            # make sure x is always non-decreasing
            x1, x2, y1, y2 = x2, x1, y2, y1
        self._x1: int = x1
        self._y1: int = y1
        self._x2: int = x2
        self._y2: int = y2
        if x1 == x2:
            raise ValueError(f"Line {self!s} is vertical, not diagonal!")
        elif y1 == y2:
            raise ValueError(f"Line {self!s} is horizontal, not diagonal!")
        elif self._x2 - self._x1 != abs(self._y2 - self._y1):
            raise ValueError(f"Line {self!s} is not at 45°!")

    def points(self) -> Iterator[Tuple[int, int]]:
        if self._y1 <= self._y2:
            y_delta = 1
        else:
            y_delta = -1
        for i in range(self._x2 - self._x1 + 1):
            yield self._x1 + i, self._y1 + i * y_delta

    @property
    def p2(self) -> Tuple[int, int]:
        return self._x2, self._y2


class Diagram:
    def __init__(self):
        self._cells: Dict[int, Dict[int, int]] = defaultdict(Counter)
        self.max_y: int = 0
        self.max_x: int = 0

    def __getitem__(self, y: int) -> Dict[int, int]:
        return self._cells[y]

    def __iter__(self) -> Tuple[Tuple[int, int], int]:
        for y, row in self._cells.items():
            for x, count in row.items():
                yield (x, y), count


LINE_PATTERN = re.compile(r"\s*(?P<x1>\d+)\s*,\s*(?P<y1>\d+)\s*->\s*(?P<x2>\d+)\s*,\s*(?P<y2>\d+)\s*")


class HydrothermalVenture(Challenge):
    day = 5

    def read_lines(self) -> Iterator[Line]:
        with open(self.input_path, "r") as f:
            for i, line in enumerate(f):
                m = LINE_PATTERN.match(line)
                if m:
                    x1, y1, x2, y2 = map(int, (m.group("x1"), m.group("y1"), m.group("x2"), m.group("y2")))
                    if y1 == y2:
                        yield HorizontalLine(from_x=x1, to_x=x2, y=y1)
                    elif x1 == x2:
                        yield VerticalLine(x=x1, from_y=y1, to_y=y2)
                    else:
                        yield DiagonalLine(x1=x1, y1=y1, x2=x2, y2=y2)

    @Challenge.register_part(0)
    def overlap(self):
        diagram = Diagram()
        for line in self.read_lines():
            if not (isinstance(line, HorizontalLine) or isinstance(line, VerticalLine)):
                continue
            for x, y in line.points():
                diagram[y][x] += 1
        two_overlapping = sum(1 for _, count in diagram if count >= 2)
        self.output.write(f"{two_overlapping}\n")

    @Challenge.register_part(1)
    def diagonal(self):
        diagram = Diagram()
        for line in self.read_lines():
            for x, y in line.points():
                diagram[y][x] += 1
        two_overlapping = sum(1 for _, count in diagram if count >= 2)
        self.output.write(f"{two_overlapping}\n")
