from enum import Enum
import re
from typing import FrozenSet, Iterable, List, Tuple

from . import Challenge


class Axis(Enum):
    X = "x"
    Y = "y"


class Fold:
    def __init__(self, axis: Axis, position: int):
        self.axis: Axis = axis
        self.position: int = position

    def __str__(self):
        return f"fold along {self.axis.value}={self.position}"

    def __repr__(self):
        return f"Fold(Axis.{self.axis.name}, {self.position!r})"


class Dot:
    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y

    def apply(self, fold: Fold) -> "Dot":
        if fold.axis == Axis.X:
            # fold left
            assert fold.position != self.x
            if self.x <= fold.position:
                # we are left of the fold
                return self
            else:
                # we are right of the fold
                return Dot(2 * fold.position - self.x, self.y)
        else:
            # fold up
            assert fold.position != self.y
            if self.y <= fold.position:
                # we are above the fold
                return self
            else:
                # we are below the fold
                return Dot(self.x, 2 * fold.position - self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return isinstance(other, Dot) and self.x == other.x and self.y == other.y

    def __str__(self):
        return f"{self.x},{self.y}"


class TransparentPaper:
    FOLD_ALONG_PATTERN = re.compile(r"^\s*fold\s+along\s+(?P<axis>[xy])\s*=\s*(?P<pos>\d+)\s*$", re.IGNORECASE)

    def __init__(self, dots: Iterable[Dot]):
        self.dots: FrozenSet[Dot] = frozenset(dots)

    def __str__(self):
        return "\n".join(map(str, self.dots))

    def __len__(self):
        return len(self.dots)

    def __iter__(self):
        yield from self.dots

    def apply(self, fold: Fold) -> "TransparentPaper":
        return TransparentPaper((d.apply(fold) for d in self.dots))

    @classmethod
    def load(cls, stream: Iterable[str]) -> Tuple["TransparentPaper", List[Fold]]:
        dots: List[Dot] = []
        folds: List[Fold] = []
        for line in (l.strip() for l in stream):
            if not line:
                continue
            m = cls.FOLD_ALONG_PATTERN.match(line)
            if m:
                axis = [Axis.Y, Axis.X][m["axis"] == "x"]
                folds.append(Fold(axis, int(m["pos"])))
            else:
                xy = [int(i.strip()) for i in line.split(",")]
                if len(xy) != 2:
                    raise ValueError(f"Invalid line: {line!r}")
                dots.append(Dot(*xy))
        return TransparentPaper(dots), folds


class TransparentOrigami(Challenge):
    day = 13

    @Challenge.register_part(0)
    def first_fold(self):
        with open(self.input_path, "r") as f:
            paper, folds = TransparentPaper.load(f)
        after_first = paper.apply(folds[0])
        self.output.write(f"{len(after_first)}\n")
